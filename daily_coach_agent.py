#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Coach Agent — GitHub Actions / Intervals.icu / OpenAI

Corre em GitHub Actions e gera:
- daily_agent_report.txt
- daily_agent_report.json
- last_update_payload.json, se alterar treino

Pode substituir automaticamente o treino do dia se:
- AUTO_APPLY=true
- o workflow correr com --auto
- decisão for AMARELO ou VERMELHO
- treino do dia tiver external_id

Secrets esperadas:
INTERVALS_API_KEY
ATHLETE_ID
OPENAI_API_KEY
OPENAI_MODEL
AUTO_APPLY
"""

import argparse
import base64
import datetime as dt
import json
import math
import os
import re
import statistics
import sys
import smtplib
from email.message import EmailMessage
from pathlib import Path

import requests

API_BASE = "https://intervals.icu/api/v1"
AUTH_USER = "API_KEY"
OPENAI_BASE = "https://api.openai.com/v1/responses"
CHAT_COMPLETIONS_BASE = "https://api.openai.com/v1/chat/completions"


def fnum(x):
    try:
        if x is None or x == "":
            return None
        v = float(x)
        if math.isnan(v):
            return None
        return v
    except Exception:
        return None


def first(d, keys):
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, ""):
            return d.get(k)
    return None


def as_list(x):
    if isinstance(x, list):
        return [i for i in x if isinstance(i, dict)]
    if isinstance(x, dict):
        for k in ("data", "items", "results"):
            if isinstance(x.get(k), list):
                return [i for i in x[k] if isinstance(i, dict)]
        return [x]
    return []


def parse_item_date(item):
    for k in ("id", "date", "day", "start_date_local", "start_date", "start_date_timezone"):
        v = item.get(k)
        if not v:
            continue
        try:
            return dt.date.fromisoformat(str(v)[:10])
        except Exception:
            pass
    return None


def parse_datetime_local(raw, fallback_date):
    s = str(raw or "")
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return dt.datetime.combine(fallback_date, dt.time(11, 30))


def sleep_h(w):
    v = fnum(first(w, ["sleepSecs", "sleepSeconds", "sleep_seconds", "sleepTime", "sleep_time", "totalSleepSeconds"]))
    if v is None:
        return None
    if v > 1000:
        return v / 3600
    if v > 60:
        return v / 60
    return v


def sleep_score(w):
    return fnum(first(w, ["sleepScore", "sleep_score", "sleepQuality", "sleep_quality"]))


def hrv(w):
    return fnum(first(w, ["hrv", "hrvRmssd", "hrv_rmssd", "rmssd", "HRV"]))


def rhr(w):
    return fnum(first(w, ["restingHR", "resting_hr", "restingHeartRate", "rhr"]))


def weight_kg(w):
    """Best-effort weight extraction from Intervals wellness/Garmin sync."""
    v = fnum(first(w, [
        "weight", "weightKg", "weight_kg", "bodyWeight", "body_weight",
        "mass", "icu_weight", "Weight"
    ]))
    if v is None:
        return None
    # If some API ever returns grams, normalize defensively.
    if v > 300:
        return v / 1000
    return v


def ctl(w):
    return fnum(first(w, ["ctl", "fitness", "icu_ctl", "icu_fitness"]))


def atl(w):
    return fnum(first(w, ["atl", "fatigue", "icu_atl", "icu_fatigue"]))


def form(w):
    v = fnum(first(w, ["form", "tsb", "icu_form"]))
    if v is not None:
        return v
    c, a = ctl(w), atl(w)
    if c is not None and a is not None:
        return c - a
    return None


def pre_workout_metric(today_w, yesterday_w, getter, planned_load_today, has_done_today):
    """
    For CTL/ATL/Form-like metrics that may include today's planned workout in Intervals.
    If there is a planned workout today and no activity is completed yet, use yesterday
    as the best available pre-workout proxy.
    """
    today_value = getter(today_w)
    yesterday_value = getter(yesterday_w) if yesterday_w else None
    if not has_done_today and planned_load_today and planned_load_today > 0 and yesterday_value is not None:
        return yesterday_value
    return today_value


def pre_workout_form(today_w, yesterday_w, planned_load_today, has_done_today):
    """
    Intervals.icu may expose Fitness/Fatigue/Form for the date including planned workouts.
    If there is a planned workout today but no completed activity yet, the reported
    Form can be a post-planned-load projection rather than true pre-workout readiness.
    """
    today_form = form(today_w)
    yesterday_form = form(yesterday_w) if yesterday_w else None
    if not has_done_today and planned_load_today and planned_load_today > 0 and yesterday_form is not None:
        return yesterday_form
    return today_form


def load(item):
    return fnum(first(item, ["icu_training_load", "training_load", "load", "tss", "TSS"]))


def hours(item):
    v = fnum(first(item, ["moving_time", "elapsed_time", "duration", "duration_secs", "total_timer_time"]))
    if v is None:
        return None
    if v > 1000:
        return v / 3600
    if v > 20:
        return v / 60
    return v


def mean(vals):
    vals = [v for v in vals if v is not None]
    return statistics.mean(vals) if vals else None


def fueling_guidance(context, weight_today=None, weight_avg_7d=None):
    """Simple coaching guidance for weight loss without compromising training."""
    target_weight = 74.0
    planned = context.get("planned_events_today", [])
    done_today_summary = context.get("done_today_summary", {})
    done_today = bool(done_today_summary.get("has_activity"))
    done_load = done_today_summary.get("load") or 0
    done_hours = done_today_summary.get("hours") or 0

    yesterday = context.get("yesterday", {}) or {}
    y_comp = yesterday.get("compliance", {}) or {}
    y_done_load = y_comp.get("done_load") or 0
    y_done_hours = y_comp.get("done_hours") or 0
    y_status = str(y_comp.get("status") or "").upper()
    recent_3d = context.get("recent_3d", {}) or {}
    recent_load_3d = recent_3d.get("load") or 0
    big_yesterday = y_done_load >= 150 or y_done_hours >= 3.0 or "MAIS DURO" in y_status
    high_recent_load = recent_load_3d >= 300

    planned_load = sum((e.get("load") or 0) for e in planned)
    planned_hours = sum((e.get("hours") or 0) for e in planned)
    names = " ".join(str(e.get("name") or "") for e in planned).lower()

    intense_terms = [
        "sweet spot", "threshold", "vo2", "zone 5", "zone 6", "over", "under",
        "tempo", "interval", "burst", "sprint", "test", "race", "cheetah", "pounce"
    ]
    easy_terms = [
        "zone 2", "z2", "endurance", "recovery", "recuper", "easy", "facil", "fácil"
    ]

    effective_load = done_load if done_today else planned_load
    effective_hours = done_hours if done_today else planned_hours
    has_easy_terms = any(t in names for t in easy_terms)
    has_quality_terms = any(t in names for t in intense_terms)

    # Mixed workouts with Sweet Spot/Threshold/VO2 plus Z2 in the name are still quality.
    is_planned_easy = has_easy_terms and not has_quality_terms
    is_quality = has_quality_terms or (effective_load >= 80 and not is_planned_easy)
    is_mixed_quality_easy = has_quality_terms and has_easy_terms
    is_long = effective_hours >= 2.0 or effective_load >= 100
    is_rest_or_easy = is_planned_easy or (effective_load <= 35 and not is_quality)

    ref_weight = weight_avg_7d if weight_avg_7d is not None else weight_today
    delta = (ref_weight - target_weight) if ref_weight is not None else None

    lines = []
    if weight_today is not None:
        lines.append(f"Peso hoje: {fmt(weight_today,1)} kg.")
    else:
        lines.append("Peso hoje: n/d.")
    if weight_avg_7d is not None:
        lines.append(f"Média 7d: {fmt(weight_avg_7d,1)} kg.")
    else:
        lines.append("Média 7d: n/d.")
    if delta is not None:
        if delta > 0:
            lines.append(f"Objetivo 74 kg: faltam ~{fmt(delta,1)} kg pela média 7d; apontar para 0,25–0,40 kg/semana.")
        else:
            lines.append("Objetivo 74 kg: já estás na zona-alvo pela média 7d; proteger potência e recuperação.")
    else:
        lines.append("Objetivo 74 kg: usar média semanal, não o peso de um único dia.")

    if weight_today is not None and weight_avg_7d is not None and weight_today < weight_avg_7d - 0.6:
        lines.append("Peso de hoje está bem abaixo da média 7d; tratar como oscilação/hidratação e não apertar dieta por causa de um dia.")

    lines.append("Proteína: 150–170 g/dia.")

    if done_today:
        lines.append(f"Treino já concluído: {fmt(done_load,0)} TSS / {fmt_h(done_hours)}.")
        lines.append("Agora o foco é recuperação, não mais carga.")
        lines.append("Pós-treino: 30–40 g proteína + hidratos suficientes para repor glicogénio.")
        if is_quality or done_hours >= 1.0:
            lines.append("Hoje não fazer défice agressivo; deixa o treino assentar.")
        else:
            lines.append("Défice leve apenas se estiveres bem alimentado e sem fome/fadiga anormal.")
    elif is_planned_easy and effective_hours >= 1.25:
        lines.append("Hoje é Z2/endurance: foco em recuperação ativa e aeróbico, não intensidade.")
        if effective_hours > 2.0:
            lines.append("Durante o treino: 40–60 g hidratos/h para Z2 longo (>2h), com água/eletrólitos suficientes.")
            lines.append("Défice leve pode existir no dia, mas não à custa de sair vazio num treino longo.")
        else:
            lines.append("Durante o treino: 30–45 g hidratos/h é suficiente para Z2 de ~75–120 min; água/eletrólitos se for muito fácil.")
            lines.append("Défice leve é aceitável, mas sem sair vazio após dois dias de qualidade.")
    elif is_mixed_quality_easy:
        lines.append("Hoje é qualidade controlada com Z2: há blocos de intensidade, mas o restante deve ficar fácil/controlado.")
        lines.append("Durante o treino: 50–70 g hidratos/h se a sessão passar de ~75 min; usar bidão + gel/chews se necessário.")
        lines.append("Não fazer défice agressivo; manter Z2 realmente controlado fora dos blocos.")
        lines.append("Pós-treino: 30–40 g proteína + hidratos suficientes para recuperar.")
    elif is_quality:
        lines.append("Hoje há qualidade/intensidade: não fazer défice agressivo; alimentar bem antes e depois.")
        if planned_hours >= 1.0:
            lines.append("Durante o treino: 60–80 g hidratos/h se a sessão passar de ~75 min ou tiver blocos duros.")
        lines.append("Pós-treino: 30–40 g proteína + hidratos suficientes para recuperar.")
    elif is_long:
        lines.append("Treino longo/endurance: 40–70 g hidratos/h conforme intensidade; não acabar vazio.")
        lines.append("Défice leve apenas se a recuperação estiver boa.")
    elif is_rest_or_easy:
        has_planned_easy_workout = planned_load > 5 or planned_hours > 0
        if big_yesterday or high_recent_load:
            if has_planned_easy_workout:
                lines.append("Dia fácil/Z2 após carga alta: foco em recuperação ativa e aeróbico leve, não em cortar hidratos agressivamente.")
            else:
                lines.append("Dia de descanso após carga alta: foco em recuperação, não em cortar hidratos agressivamente.")
            lines.append("Défice no máximo leve; manter proteína alta, hidratação/eletrólitos e hidratos moderados para repor glicogénio.")
        else:
            if has_planned_easy_workout:
                lines.append("Dia fácil/Z2: défice leve aceitável, mas manter energia suficiente para cumprir o treino sem arrastar.")
            else:
                if mild_fatigue_no_plan(context):
                    lines.append("Dia de descanso com sinais ligeiros de fadiga: défice no máximo leve; recuperar primeiro.")
                    lines.append("Manter proteína alta, hidratação/eletrólitos e hidratos moderados; não cortar agressivamente hoje.")
                else:
                    lines.append("Dia fácil/descanso: défice leve aceitável; hidratos mais baixos se energia/fome estiverem ok, proteína alta.")
    else:
        lines.append("Dia moderado: défice leve, sem cortar demasiado os hidratos pré/pós treino.")

    lines.append("Nos próximos relatórios, se HRV/sono baixarem ou potência/RPE ficarem anormais, reduzir défice e priorizar recuperação.")
    return lines


def fmt(v, digits=1):
    if v is None:
        return "n/d"
    try:
        return f"{float(v):.{digits}f}"
    except Exception:
        return str(v)


def fmt_h(v):
    if v is None:
        return "n/d"
    total_minutes = int(round(float(v) * 60))
    hh = total_minutes // 60
    mm = total_minutes % 60
    return f"{hh}h{mm:02d}"


def bool_env(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "sim", "y")


def safe_filename(name):
    trans = str.maketrans({
        "ç": "c", "ã": "a", "á": "a", "é": "e", "ó": "o", "í": "i", "ú": "u",
        "â": "a", "ê": "e", "ô": "o", "à": "a", "õ": "o", "º": "o", "≤": "le",
        "—": "-"
    })
    n = str(name).translate(trans).replace("🏁", "")
    n = re.sub(r"[^A-Za-z0-9_. -]+", "", n)
    n = re.sub(r"\s+", "_", n).strip("_")
    return (n[:100] or "workout") + ".zwo"


class IntervalsClient:
    def __init__(self, athlete_id, api_key):
        self.athlete_id = athlete_id
        self.s = requests.Session()
        self.s.auth = (AUTH_USER, api_key)
        self.s.headers.update({"Accept": "application/json"})

    def get(self, path, params=None, required=False):
        url = API_BASE + path
        r = self.s.get(url, params=params, timeout=45)
        if required and not r.ok:
            raise RuntimeError(f"GET {url} falhou: HTTP {r.status_code}\n{r.text[:1200]}")
        if not r.ok:
            return None
        try:
            return r.json()
        except Exception:
            return None

    def post(self, path, payload):
        url = API_BASE + path
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        r = self.s.post(url, json=payload, headers=headers, timeout=120)
        if not r.ok:
            raise RuntimeError(f"POST {url} falhou: HTTP {r.status_code}\n{r.text[:2000]}")
        try:
            return r.json()
        except Exception:
            return r.text

    def athlete(self):
        return self.get(f"/athlete/{self.athlete_id}", required=True)

    def wellness_range(self, start, end):
        for params in ({"oldest": start.isoformat(), "newest": end.isoformat()},
                       {"start": start.isoformat(), "end": end.isoformat()}):
            data = self.get(f"/athlete/{self.athlete_id}/wellness", params=params)
            items = as_list(data)
            if items:
                return items
        out = []
        cur = start
        while cur <= end:
            data = self.get(f"/athlete/{self.athlete_id}/wellness/{cur.isoformat()}")
            out += as_list(data)
            cur += dt.timedelta(days=1)
        return out

    def activities_range(self, start, end):
        for params in ({"oldest": start.isoformat(), "newest": end.isoformat()},
                       {"start": start.isoformat(), "end": end.isoformat()}):
            data = self.get(f"/athlete/{self.athlete_id}/activities", params=params)
            items = as_list(data)
            if items:
                return items
        return []

    def events_range(self, start, end):
        for params in ({"oldest": start.isoformat(), "newest": end.isoformat()},
                       {"start": start.isoformat(), "end": end.isoformat()}):
            data = self.get(f"/athlete/{self.athlete_id}/events", params=params)
            items = as_list(data)
            if items:
                return items
        return []

    def upload_bulk_events(self, events):
        return self.post(f"/athlete/{self.athlete_id}/events/bulk", events)


def completed_activities_on(activities, target):
    out = []
    for a in activities:
        d = parse_item_date(a)
        if d != target:
            continue
        h = hours(a) or 0
        l = load(a) or 0
        if h > 0.15 or l > 5:
            out.append(a)
    return out


def events_on(events, target):
    return [e for e in events if parse_item_date(e) == target]


def compliance_check(planned_events, done_activities):
    planned_load = sum((load(e) or 0.0) for e in planned_events)
    planned_hours = sum((hours(e) or 0.0) for e in planned_events)
    done_load = sum((load(a) or 0.0) for a in done_activities)
    done_hours = sum((hours(a) or 0.0) for a in done_activities)

    # Infer the date for contextual rules. This is mainly used to interpret
    # Saturday/Sunday substitutions correctly.
    dates = [parse_item_date(x) for x in list(planned_events) + list(done_activities)]
    dates = [d for d in dates if d is not None]
    target_date = dates[0] if dates else None
    is_weekend = target_date.weekday() >= 5 if target_date else False

    done_density = (done_load / done_hours) if done_hours and done_hours > 0 else 0
    planned_density = (planned_load / planned_hours) if planned_hours and planned_hours > 0 else 0
    ratio = done_load / planned_load if planned_load > 10 else 1.0

    interpretation = ""
    no_compensation = False
    substitution_valid = False

    if planned_events and done_activities:
        duration_ratio = done_hours / planned_hours if planned_hours and planned_hours > 0 else 1.0

        if ratio > 1.25:
            status = "FEITO MAS MAIS DURO"
            interpretation = "Carga acima do planeado. Observar readiness antes de manter intensidade nos dias seguintes."
        elif ratio >= 0.85 and duration_ratio >= 0.80:
            status = "CUMPRIDO"
            if ratio >= 1.08 or duration_ratio >= 1.12:
                interpretation = "Treino cumprido, mas com carga/duração acima do planeado. Não compensar; observar recuperação no dia seguinte."
            else:
                interpretation = "Treino cumprido dentro de margem normal."
        # Weekend practical logic:
        # - Saturday for Nuno is usually max 2h; 75-90min indoor can be a valid shorter version only if it was actually shorter.
        # - Sunday is social/free; 90min indoor quality is a valid substitute if outdoor/social fails.
        # Do not classify these as simple failure, but only when the session was materially shorter/lower than planned.
        elif is_weekend and planned_hours >= 1.75 and 1.0 <= done_hours <= 2.25 and done_load >= 45 and ratio >= 0.45 and (duration_ratio < 0.80 or planned_hours >= 2.5):
            substitution_valid = True
            no_compensation = True
            if planned_hours >= 2.5:
                status = "SUBSTITUIÇÃO INDOOR/VERSÃO CURTA VÁLIDA"
                interpretation = "Fim de semana: volume abaixo do planeado, mas houve estímulo válido. Não compensar volume perdido à força."
            else:
                status = "VERSÃO CURTA CUMPRIDA"
                interpretation = "Fim de semana/treino até 2h: versão curta válida. Não compensar no dia seguinte."
        elif ratio >= 0.55:
            status = "PARCIAL / MAIS LEVE"
            interpretation = "Treino parcial/mais leve. Não compensar automaticamente; decidir pelo estado de hoje."
            no_compensation = True
        else:
            status = "MUITO ABAIXO DO PLANO"
            interpretation = "Muito abaixo do plano. Não transformar em dívida; reavaliar pelo readiness."
            no_compensation = True
    elif planned_events and not done_activities:
        status = "PLANEADO MAS NÃO REALIZADO"
        interpretation = "Treino planeado não realizado. Treino perdido não vira dívida; não compensar automaticamente no dia seguinte."
        no_compensation = True
    elif not planned_events and done_activities:
        status = "EXTRA / NÃO PLANEADO"
        interpretation = "Atividade extra. Considerar carga real antes de intensificar."
    else:
        status = "DESCANSO CUMPRIDO / SEM TREINO"
        interpretation = "Dia sem treino cumprido."

    return {
        "status": status,
        "planned_load": planned_load,
        "planned_hours": planned_hours,
        "done_load": done_load,
        "done_hours": done_hours,
        "planned_count": len(planned_events),
        "done_count": len(done_activities),
        "done_density": done_density,
        "planned_density": planned_density,
        "ratio": ratio,
        "target_date": target_date.isoformat() if target_date else None,
        "is_weekend": is_weekend,
        "substitution_valid": substitution_valid,
        "no_compensation": no_compensation,
        "interpretation": interpretation,
    }


def pct(x):
    return round(float(x) / 100, 4)


def escape_xml(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def zwo_from_steps(name, steps):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<workout_file>",
        f"  <name>{escape_xml(name)}</name>",
        "  <sportType>bike</sportType>",
        "  <tags>",
        '    <tag name="Daily Coach Agent" />',
        '    <tag name="Auto Adjusted" />',
        "  </tags>",
        "  <workout>",
    ]
    for s in steps:
        t = s["type"]
        if t == "Warmup":
            lines.append(f'    <Warmup Duration="{s["duration"]}" PowerLow="{pct(s["power_low"])}" PowerHigh="{pct(s["power_high"])}" />')
        elif t == "Cooldown":
            lines.append(f'    <Cooldown Duration="{s["duration"]}" PowerLow="{pct(s["power_low"])}" PowerHigh="{pct(s["power_high"])}" />')
        elif t == "SteadyState":
            lines.append(f'    <SteadyState Duration="{s["duration"]}" Power="{pct(s["power"])}" />')
        elif t == "IntervalsT":
            lines.append(f'    <IntervalsT Repeat="{s["reps"]}" OnDuration="{s["on_duration"]}" OffDuration="{s["off_duration"]}" OnPower="{pct(s["on_power"])}" OffPower="{pct(s["off_power"])}" />')
    lines += ["  </workout>", "</workout_file>"]
    return "\n".join(lines)


def dur_min(steps):
    sec = 0
    for s in steps:
        if s["type"] in ("Warmup", "Cooldown", "SteadyState"):
            sec += s["duration"]
        else:
            sec += s["reps"] * (s["on_duration"] + s["off_duration"])
    return round(sec / 60)


def est_load_steps(steps):
    work = 0.0
    for s in steps:
        if s["type"] in ("Warmup", "Cooldown"):
            p = ((s["power_low"] + s["power_high"]) / 2) / 100
            work += s["duration"] * p * p
        elif s["type"] == "SteadyState":
            p = s["power"] / 100
            work += s["duration"] * p * p
        else:
            pon = s["on_power"] / 100
            poff = s["off_power"] / 100
            work += s["reps"] * (s["on_duration"] * pon * pon + s["off_duration"] * poff * poff)
    return max(1, round(work / 36))


def replacement_steps(kind):
    if kind == "red_recovery":
        return [
            {"type": "Warmup", "duration": 600, "power_low": 40, "power_high": 55},
            {"type": "SteadyState", "duration": 2400, "power": 55},
            {"type": "Cooldown", "duration": 600, "power_low": 55, "power_high": 35},
        ]
    if kind == "yellow_vo2":
        return [
            {"type": "Warmup", "duration": 720, "power_low": 45, "power_high": 72},
            {"type": "SteadyState", "duration": 180, "power": 82},
            {"type": "SteadyState", "duration": 180, "power": 55},
            {"type": "IntervalsT", "reps": 4, "on_duration": 240, "on_power": 105, "off_duration": 300, "off_power": 55},
            {"type": "SteadyState", "duration": 600, "power": 62},
            {"type": "Cooldown", "duration": 600, "power_low": 58, "power_high": 36},
        ]
    if kind == "yellow_threshold":
        return [
            {"type": "Warmup", "duration": 720, "power_low": 45, "power_high": 70},
            {"type": "IntervalsT", "reps": 2, "on_duration": 900, "on_power": 92, "off_duration": 360, "off_power": 55},
            {"type": "SteadyState", "duration": 900, "power": 62},
            {"type": "Cooldown", "duration": 600, "power_low": 58, "power_high": 36},
        ]
    if kind == "yellow_ss":
        return [
            {"type": "Warmup", "duration": 720, "power_low": 45, "power_high": 68},
            {"type": "IntervalsT", "reps": 2, "on_duration": 720, "on_power": 88, "off_duration": 300, "off_power": 55},
            {"type": "SteadyState", "duration": 1200, "power": 62},
            {"type": "Cooldown", "duration": 600, "power_low": 58, "power_high": 36},
        ]
    return [
        {"type": "Warmup", "duration": 600, "power_low": 45, "power_high": 62},
        {"type": "SteadyState", "duration": 3600, "power": 62},
        {"type": "Cooldown", "duration": 600, "power_low": 58, "power_high": 36},
    ]


def choose_replacement_kind(status, planned_name):
    name = (planned_name or "").lower()
    if status == "VERMELHO":
        return "red_recovery"
    if "vo2" in name or "30/30" in name or "40/20" in name:
        return "yellow_vo2"
    if "threshold" in name or "ftp" in name or "over-under" in name:
        return "yellow_threshold"
    if "sweet" in name or "spot" in name or "ss" in name:
        return "yellow_ss"
    return "yellow_endurance"


def heuristic_decision(today_w, baseline, recent_load, planned_load, yesterday_compliance, readiness_form=None):
    reasons, actions = [], []
    score = 0

    today_hrv, base_hrv = hrv(today_w), baseline.get("hrv")
    if today_hrv is not None and base_hrv:
        diff = (today_hrv - base_hrv) / base_hrv * 100
        if diff <= -15:
            score += 3; reasons.append(f"HRV muito baixa: {fmt(diff)}% vs baseline.")
        elif diff <= -8:
            score += 2; reasons.append(f"HRV baixa: {fmt(diff)}% vs baseline.")
        elif diff <= -5:
            score += 1; reasons.append(f"HRV ligeiramente baixa: {fmt(diff)}% vs baseline.")
        else:
            reasons.append(f"HRV ok: {fmt(today_hrv)} vs baseline {fmt(base_hrv)}.")

    today_rhr, base_rhr = rhr(today_w), baseline.get("rhr")
    if today_rhr is not None and base_rhr:
        diff = today_rhr - base_rhr
        if diff >= 7:
            score += 3; reasons.append(f"Resting HR muito alta: +{fmt(diff,0)} bpm.")
        elif diff >= 4:
            score += 2; reasons.append(f"Resting HR alta: +{fmt(diff,0)} bpm.")
        elif diff >= 2:
            score += 1; reasons.append(f"Resting HR ligeiramente alta: +{fmt(diff,0)} bpm.")
        else:
            reasons.append(f"Resting HR ok: {fmt(today_rhr,0)} bpm.")

    sh = sleep_h(today_w)
    if sh is not None:
        if sh < 5.75:
            score += 3; reasons.append(f"Sono muito baixo: {fmt_h(sh)}.")
        elif sh < 6.5:
            score += 2; reasons.append(f"Sono baixo: {fmt_h(sh)}.")
        elif sh < 7:
            score += 1; reasons.append(f"Sono aceitável mas curto: {fmt_h(sh)}.")
        else:
            reasons.append(f"Sono ok: {fmt_h(sh)}.")

    fm = readiness_form if readiness_form is not None else form(today_w)
    if fm is not None:
        if fm < -30:
            score += 3; reasons.append(f"Form muito negativa: {fmt(fm,0)}.")
        elif fm < -22:
            score += 2; reasons.append(f"Form baixa: {fmt(fm,0)}.")
        elif fm < -15:
            score += 1; reasons.append(f"Form moderadamente baixa: {fmt(fm,0)}.")
        else:
            reasons.append(f"Form ok: {fmt(fm,0)}.")

    if recent_load >= 450:
        score += 2; reasons.append(f"Carga alta últimos 3 dias: {fmt(recent_load,0)} TSS.")
    elif recent_load >= 300:
        score += 1; reasons.append(f"Carga moderada/alta últimos 3 dias: {fmt(recent_load,0)} TSS.")

    y_status = yesterday_compliance.get("status")
    if y_status == "FEITO MAS MAIS DURO":
        score += 1
        reasons.append(
            f"Ontem foi mais duro que o planeado: feito {fmt(yesterday_compliance.get('done_load'),0)} vs planeado {fmt(yesterday_compliance.get('planned_load'),0)} TSS."
        )
    elif y_status in ("SUBSTITUIÇÃO INDOOR/VERSÃO CURTA VÁLIDA", "VERSÃO CURTA CUMPRIDA"):
        reasons.append("Ontem houve substituição/versão curta válida. Não compensar volume perdido; decidir apenas pelo estado de hoje.")
    elif y_status == "PLANEADO MAS NÃO REALIZADO":
        reasons.append("Ontem havia treino planeado, mas não foi realizado. Treino perdido não vira dívida; não compensar automaticamente.")
    elif y_status in ("PARCIAL / MAIS LEVE", "MUITO ABAIXO DO PLANO"):
        reasons.append(f"Ontem ficou abaixo do planeado ({y_status}). Não compensar à força; ajustar pelo estado de hoje.")

    if score >= 7:
        status = "VERMELHO"
        actions = ["Trocar por recovery/Z2 45–75min ou descanso total.", "Não fazer VO2/threshold hoje."]
    elif score >= 4:
        status = "AMARELO"
        actions = ["Reduzir 2–5% a potência ou cortar 1 repetição.", "Se RPE >8/10 cedo, terminar em Z2."]
    else:
        status = "VERDE"
        actions = ["Fazer o treino planeado como está."]

    if planned_load is None or planned_load <= 5:
        if status == "VERDE":
            actions = ["Sem treino estruturado encontrado: manter descanso/Z2 fácil."]
        elif status == "AMARELO":
            actions = ["Sem treino estruturado: boa oportunidade para recuperar."]
        else:
            actions = ["Descanso total recomendado."]

    return {"status": status, "reasons": reasons, "actions": actions, "source": "heuristic"}



def get_openai_reasoning_effort(default="medium"):
    """
    Reasoning effort can be controlled with OPENAI_REASONING_EFFORT.
    Useful values: none/minimal, low, medium, high, xhigh.
    """
    effort = os.getenv("OPENAI_REASONING_EFFORT", default).strip().lower()
    allowed = {"minimal", "none", "low", "medium", "high", "xhigh"}
    if effort not in allowed:
        print(f"OPENAI_REASONING_EFFORT inválido: {effort!r}. A usar {default!r}.")
        return default
    return effort


def call_openai(openai_key, model, reasoning_effort, context):
    """
    Chama a OpenAI para decisão do treinador.

    Versão robusta:
    1) tenta Responses API com reasoning minimal e output budget maior
    2) se vier sem texto, tenta Chat Completions como fallback
    3) não exige JSON do modelo; usa formato linha-a-linha fácil de parsear
    """
    if not openai_key:
        return None, "OPENAI_API_KEY ausente; usei regras heurísticas."

    instructions = """
És um treinador profissional de ciclismo de estrada do Nuno.

Perfil do atleta:
- Homem, 38/39 anos
- 77 kg
- FTP 319-320 W
- Perfil fisiológico diesel: forte em potência sustentada, tempo, sweet spot e threshold
- Objetivo principal: melhorar FTP e potência sustentada sem comprometer recuperação
- O plano atual tem segunda e sexta como descanso, terça e quinta como dias de qualidade, quarta Z2 real, sábado estruturado até 2h e domingo social/livre

Princípios de decisão:
- Preservar consistência, recuperação e adaptação é mais importante do que forçar treino num dia aparentemente bom.
- Peso/fueling: objetivo 74 kg, mas sem comprometer potência, sono, HRV ou recuperação. Em dias intensos não sugerir défice agressivo.
- Não transformar um dia sem treino planeado num treino de qualidade só porque sono, HRV ou Form estão bons.
- Form positiva significa que o atleta está fresco; não significa automaticamente que deve fazer intensidade.
- Nunca recomendar compensar um treino falhado aumentando intensidade no dia seguinte.
- Se ontem foi mais duro que o planeado, ser conservador hoje.
- Se ontem foi cumprido e hoje não há treino planeado, respeitar descanso ou Z2 fácil.

Regras específicas:
1. Se planned_events_today estiver vazio:
   - Não sugerir sweet spot, threshold, VO2, over-unders, tempo forte ou qualquer treino de qualidade.
   - A recomendação deve ser descanso total OU Z2 fácil.
   - Z2 fácil significa 45-75 min, HR controlada, RPE baixo, sem blocos.
   - Se a semana ou treino recente tiver termos como Regen, Recovery, Recuperação, Taper ou easy, recomendar preferencialmente descanso total ou 45-60 min Z2 muito fácil.

2. Se nomes dos treinos recentes ou planeados tiverem termos como Regen, Recovery, Recuperação, Taper ou easy:
   - Ser ainda mais conservador.
   - Não sugerir intensidade alternativa.
   - Priorizar absorção de carga.

3. Se houver treino planeado e o estado for VERDE:
   - Manter o treino como está.
   - Não acrescentar intensidade extra.

4. Se houver treino planeado e o estado for AMARELO:
   - Reduzir 2-5% a potência alvo OU cortar 1 repetição/bloco.
   - Se for VO2, reduzir para o limite baixo e terminar em Z2 se RPE subir demasiado cedo.

5. Se houver treino planeado e o estado for VERMELHO:
   - Substituir por recovery/Z2 45-75 min ou descanso total.
   - Não fazer VO2, threshold, sweet spot ou over-unders.

6. Se já existir atividade concluída hoje:
   - Não recomendar repetir treino.
   - Recomendação deve focar recuperação, hidratação e nutrição pós-treino.

8. Regra automática de fim de semana:
   - Se calendar_context.is_weekend for true, inclui SEMPRE uma alternativa indoor/rolo de 90 minutos.
   - Esta alternativa deve servir para chuva, mau tempo, falta de grupo ou impossibilidade de sair.
   - A alternativa indoor de 90 minutos deve respeitar o estado do dia:
     VERDE: treino estruturado indoor equivalente mas controlado.
     AMARELO: versão indoor reduzida, mais Z2 e menos intensidade.
     VERMELHO: recovery/Z2 indoor ou descanso.
   - Não obrigar o atleta a preencher available_minutes, training_location ou notes para ter esta alternativa.
   - Se o treino original for domingo social/grupo, a alternativa indoor deve ser clara e executável em 90 minutos.

9. Treinos falhados e substituições válidas:
   - Se ontem teve treino planeado mas não foi realizado, NÃO tratar como dívida.
   - Não recomendar compensar o treino perdido no dia seguinte.
   - Se yesterday.compliance.status indicar SUBSTITUIÇÃO INDOOR/VERSÃO CURTA VÁLIDA ou VERSÃO CURTA CUMPRIDA, aceitar como estímulo válido.
   - Sábado do Nuno é normalmente até 2h; uma versão indoor de 75-90 min pode ser cumprimento válido.
   - Domingo é social/livre; se não der para sair e houver 90 min indoor com carga razoável, considerar substituição válida.
   - Em todos estes casos, a decisão de hoje deve depender de readiness e do treino de hoje, não de “pagar” volume perdido.

9. Alternativas com duração correta:
   - A alternativa de 45 min nunca pode passar de 45 min.
   - A alternativa de 60 min nunca pode passar de 60 min.
   - A alternativa indoor de fim de semana deve caber em 90 min.
   - Não usar blocos até FTP em alternativas; usar tempo/SS baixo @80–88%, salvo se o treino planeado for explicitamente threshold/teste.
   - O plano B indoor deve ser igual ou mais fácil que o plano principal, nunca mais duro.

10. Regra chuva/fim de semana por duração:
   - Se for sábado/domingo e o treino planeado tiver até 2h, não criar alternativa indoor de 90 min.
   - Para treinos até 2h, dizer apenas: se chover ou as condições forem desfavoráveis, faz o treino planeado indoor/rolo.
   - Só criar alternativa indoor de 90 min se o treino planeado for acima de 2h, social ride, group ride, endurance longo ou saída outdoor longa.

11. Regra para treino Z2/endurance planeado:
   - Se o treino planeado contiver Zone 2, Z2, Endurance, Recovery ou fácil, as alternativas de 45/60 min devem continuar Z2/recovery.
   - Não sugerir tempo, sweet spot, threshold ou blocos quando o treino planeado do dia é Z2/endurance puro.
   - Se houver qualidade nos dias anteriores, reforçar que hoje é para absorver carga e manter HR/RPE baixos.
   - Fueling para Z2 75–120 min: normalmente 30–45 g hidratos/h, não 60–80 g/h obrigatório.
   - Fueling para Z2 longo acima de 2h: normalmente 40–60 g hidratos/h + água/eletrólitos suficientes.

11.a Regra Z2 puro curto:
   - Se o treino planeado é Z2/recovery/endurance puro, curto (até ~75 min), e HRV/RHR/sono estão bons, não marcar AMARELO apenas por Form/carga acumulada.
   - O estado deve ser VERDE para cumprir Z2 fácil.
   - Mesmo se o estado for AMARELO, as ações devem continuar Z2/recovery, nunca tempo/SS/threshold.

11.b Regra treino misto qualidade + Z2:
   - Se o treino contiver Sweet Spot, Threshold, VO2, Over-Under, Intervals ou similar, e também contiver Z2/Endurance no nome, classificar como qualidade controlada/mista, não como Z2 puro.
   - Neste caso, manter a cautela nos blocos e Z2 realmente fácil fora deles.
   - Fueling para treino misto >75 min: normalmente 50–70 g hidratos/h, não 30–45 g/h de Z2 puro.

12. Regra AMARELO forte para treino longo/de qualidade:
   - Se ontem foi FEITO MAS MAIS DURO/acima do planeado e hoje há treino longo/de qualidade (>=150 TSS, >=2h30, Sweet Spot Group Ride, Group Ride ou similar), com HRV baixa e/ou Form <= -10:
     Estado deve ser AMARELO.
     Não recomendar "reduzir 3%" nem "cortar um bloco" como plano principal.
     Plano principal deve ser substituir por 90–120 min Z2 fácil/endurance, sem blocos, ou descanso se houver fadiga.
   - Group ride em AMARELO forte só é aceitável se o atleta conseguir ficar em Z2 e cortar cedo.

13. Regra pós-treino grande:
   - Se ontem teve >=150 TSS, >=3h ou foi acima do planeado, e hoje não há treino planeado:
     recomendar descanso total preferencial; no máximo 30–60 min recovery muito fácil.
     Não sugerir hidratos baixos/agressivos; recuperação primeiro. Se houver Z2/fácil planeado, chamar "dia fácil/Z2", não "descanso".
     Défice calórico, se existir, deve ser no máximo leve, com hidratos moderados, proteína alta, hidratação e eletrólitos.
   - Se treino foi cumprido mas >8% acima em carga ou >12% acima em duração, dizer "cumprido, mas acima do planeado", não apenas "dentro da margem normal".

14. Regra CTL/ATL/Form pré-treino:
   - Se há treino planeado hoje e ainda não há atividade concluída hoje, a Fitness/CTL, Fatigue/ATL e Form/TSB reportadas pelo Intervals podem incluir o treino planeado de hoje.
   - Para decidir readiness antes do treino, usa:
     today_metrics.readiness_fitness_ctl
     today_metrics.readiness_fatigue_atl
     today_metrics.readiness_form
   - Se today_metrics.metrics_are_projected_after_planned for true, não uses CTL/ATL/Form reportados como motivo principal para reduzir.
   - Não cites valores CTL/ATL/Form reportados/projetados nos motivos; cita apenas os valores pré-treino usados.
   - Se reduzires, baseia a decisão em readiness pré-treino, HRV, RHR, sono, carga real recente e compliance de ontem.
   - Menciona que usaste os valores pré-treino quando os valores reportados estiverem projetados.

15. Regra consistência com compliance de ontem:
   - Se yesterday.compliance.status for CUMPRIDO e a leitura disser "dentro de margem normal", não digas que ontem foi acima do planeado, mais duro, excesso ou ligeiramente acima.
   - Se precisares justificar cautela, usa carga acumulada recente, readiness pré-treino ou sequência semanal, não um excesso que não existiu.

16. Regra dia sem treino com sinais ligeiros de fadiga:
   - Se não há treino planeado hoje e HRV está ~8-10% abaixo do baseline, RHR está +3 bpm ou mais, ou sono/score está fraco, não tratar como VERDE normal.
   - Recomendar descanso total preferencial; no máximo 30-45 min recovery muito fácil.
   - Não sugerir 60-75 min Z2 como opção principal nestes dias.
   - No fueling, défice no máximo leve; evitar défice agressivo e priorizar recuperação.

Responde em português, seguindo EXATAMENTE este formato simples.
Não uses JSON.
Não uses aspas.
Não uses markdown.
Não coloques texto antes de STATUS.

STATUS: VERDE ou AMARELO ou VERMELHO
DECISION: uma frase curta
REASONS:
- motivo 1
- motivo 2
- motivo 3
ACTIONS:
- Plano normal: ação principal
- Se só tiveres 60 min: versão reduzida
- Se só tiveres 45 min: versão muito reduzida ou Z2
- Se for indoor/rolo: versão indoor estruturada
- Se for sábado/domingo e não der para sair: alternativa indoor/rolo de 90 minutos
- Recuperação/fueling: nota curta
SHOULD_MODIFY_INTERVALS: true ou false

Definições:
- VERDE = manter o treino planeado; se não houver treino planeado, descanso ou Z2 fácil.
- AMARELO = reduzir/cortar o treino planeado; se não houver treino planeado, descanso ou Z2 fácil.
- VERMELHO = recovery/Z2 ou descanso total.

Se estiveres inseguro, sê conservador.
""".strip()

    user_input = "Dados do dia em JSON:\n" + json.dumps(context, ensure_ascii=False, indent=2)
    headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}

    def extract_response_text(data):
        if isinstance(data, dict) and isinstance(data.get("output_text"), str) and data["output_text"].strip():
            return data["output_text"].strip()
        parts = []
        if isinstance(data, dict):
            for item in data.get("output", []) or []:
                if not isinstance(item, dict):
                    continue
                for c in item.get("content", []) or []:
                    if isinstance(c, dict):
                        if c.get("type") in ("output_text", "text") and isinstance(c.get("text"), str):
                            parts.append(c["text"])
                        elif isinstance(c.get("content"), str):
                            parts.append(c["content"])
                if item.get("type") in ("output_text", "text") and isinstance(item.get("text"), str):
                    parts.append(item["text"])
        return "\n".join([p for p in parts if p]).strip()

    def call_responses():
        payload = {
            "model": model,
            "instructions": instructions,
            "input": user_input,
            "max_output_tokens": 2000,
            "reasoning": {"effort": reasoning_effort},
        }
        r = requests.post(OPENAI_BASE, headers=headers, json=payload, timeout=90)
        if not r.ok:
            return None, f"Responses API falhou HTTP {r.status_code}: {r.text[:800]}"
        data = r.json()
        txt = extract_response_text(data)
        if txt:
            return txt, None
        return None, f"Responses API sem texto. status={data.get('status') if isinstance(data, dict) else None}; incomplete={data.get('incomplete_details') if isinstance(data, dict) else None}"

    def call_chat_completions():
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": user_input},
            ],
            "max_completion_tokens": 2000,
            "reasoning_effort": reasoning_effort,
        }
        r = requests.post(CHAT_COMPLETIONS_BASE, headers=headers, json=payload, timeout=90)
        if not r.ok:
            payload.pop("reasoning_effort", None)
            r2 = requests.post(CHAT_COMPLETIONS_BASE, headers=headers, json=payload, timeout=90)
            if not r2.ok:
                return None, f"Chat Completions falhou HTTP {r.status_code}/{r2.status_code}: {r.text[:400]} | {r2.text[:400]}"
            data = r2.json()
        else:
            data = r.json()

        msg = None
        try:
            msg = data["choices"][0]["message"]["content"]
        except Exception:
            pass
        if isinstance(msg, list):
            parts = []
            for part in msg:
                if isinstance(part, dict):
                    if isinstance(part.get("text"), str):
                        parts.append(part["text"])
                    elif isinstance(part.get("content"), str):
                        parts.append(part["content"])
                elif isinstance(part, str):
                    parts.append(part)
            msg = "\n".join(parts)
        if isinstance(msg, str) and msg.strip():
            return msg.strip(), None
        return None, "Chat Completions sem texto."

    try:
        response_text, err1 = call_responses()
        used_fallback = False
        err2 = None

        if not response_text:
            response_text, err2 = call_chat_completions()
            used_fallback = True

        if not response_text:
            return None, f"OpenAI sem texto. Responses: {err1}; Chat: {err2}; usei regras heurísticas."

        parsed = parse_openai_coach_text(response_text)
        parsed["source"] = "openai"
        parsed["raw_openai_text"] = response_text[:3000]
        if used_fallback:
            parsed.setdefault("reasons", []).append("Nota técnica: usei fallback Chat Completions porque a Responses API não devolveu texto visível.")
        return parsed, None

    except Exception as e:
        return None, f"Erro OpenAI: {e}; usei regras heurísticas."


def yellow_long_quality_risk(context, planned_load, planned_hours, lname, is_quality):
    """
    Identifica dias em que AMARELO deve ser AMARELO forte:
    - treino planeado longo/duro de qualidade;
    - ontem acima do planeado;
    - readiness comprometida (Form negativo ou HRV baixa).
    Nestes casos o plano não deve ser "menos 3%"; deve virar Z2/recovery.
    """
    y = context.get("yesterday", {}).get("compliance", {}) or {}
    y_status = str(y.get("status") or "").upper()
    y_ratio = y.get("ratio")
    y_done_load = y.get("done_load") or 0
    y_planned_load = y.get("planned_load") or 0

    tm = context.get("today_metrics", {}) or {}
    base = context.get("baseline_14d", {}) or {}
    hrv_now = tm.get("hrv")
    hrv_base = base.get("hrv")
    form_now = tm.get("form")

    hrv_low = bool(hrv_now is not None and hrv_base and hrv_now < hrv_base * 0.96)
    form_negative = bool(form_now is not None and form_now <= -10)

    yesterday_hard = (
        "MAIS DURO" in y_status
        or (y_ratio is not None and y_ratio >= 1.20)
        or (y_done_load >= 130 and y_planned_load >= 60)
    )

    long_quality_today = (
        is_quality
        and (
            planned_load >= 150
            or planned_hours >= 2.5
            or any(t in lname for t in ["group ride", "sweet spot group", "ride: 3", "ride 3", "3 hours", "3h"])
        )
    )

    return long_quality_today and yesterday_hard and (hrv_low or form_negative)



def mild_fatigue_no_plan(context):
    """
    Detect a no-planned-workout day where the best coaching answer is recovery,
    not a normal green optional Z2 day.
    """
    planned = context.get("planned_events_today", []) or []
    done_today = context.get("done_today", []) or []
    if planned or done_today:
        return False

    tm = context.get("today_metrics", {}) or {}
    bl = context.get("baseline_14d", {}) or {}

    hrv = tm.get("hrv")
    hrv_base = bl.get("hrv")
    rhr = tm.get("resting_hr")
    rhr_base = bl.get("rhr")
    sleep_score = tm.get("sleep_score")
    sleep_hours = tm.get("sleep_hours")

    hrv_low = hrv is not None and hrv_base and hrv <= hrv_base * 0.92
    hrv_borderline = hrv is not None and hrv_base and hrv <= hrv_base * 0.95
    rhr_high = rhr is not None and rhr_base and rhr >= rhr_base + 3
    sleep_weak = (sleep_score is not None and sleep_score < 80) or (sleep_hours is not None and sleep_hours < 7.0)

    if hrv_low and rhr_high:
        return True

    signals = sum([bool(hrv_low or hrv_borderline), bool(rhr_high), bool(sleep_weak)])
    return signals >= 2


def normalize_no_plan_recovery_day(decision, context):
    """
    If there is no planned workout and mild fatigue markers are present,
    force recovery wording/actions. This avoids 'VERDE normal' reports when
    the useful recommendation is rest.
    """
    if not mild_fatigue_no_plan(context):
        return decision

    tm = context.get("today_metrics", {}) or {}
    bl = context.get("baseline_14d", {}) or {}

    hrv = tm.get("hrv")
    hrv_base = bl.get("hrv")
    rhr = tm.get("resting_hr")
    rhr_base = bl.get("rhr")
    sleep_score = tm.get("sleep_score")
    sleep_hours = tm.get("sleep_hours")

    decision["status"] = "AMARELO"
    decision["decision_text"] = "Descanso total preferencial; no máximo recovery muito fácil se quiseres mexer as pernas."

    decision["reasons"] = [
        "Não há treino planeado para hoje, por isso não há necessidade de acrescentar carga.",
        f"HRV abaixo do habitual ({fmt(hrv,0)} vs baseline {fmt(hrv_base,1)}) e RHR acima do habitual ({fmt(rhr,0)} vs baseline {fmt(rhr_base,0)}), sinalizando recuperação incompleta.",
        f"Sono/score mais fraco do que o habitual ({fmt(sleep_hours,1)} h; score {fmt(sleep_score,0)}), reforçando que hoje deve ser dia de absorção.",
        "Form positiva não justifica treino extra num dia sem plano quando há sinais fisiológicos de fadiga."
    ]

    decision["actions"] = [
        "Plano normal: descanso total preferencial.",
        "Se quiseres mesmo rolar: 30–45 min recovery/Z1-Z2 muito fácil, HR baixa, RPE 1–2/10, sem blocos e sem perseguir TSS.",
        "Se só tiveres 60 min: não é preciso usar os 60 min; fazer 30–45 min muito fácil ou descansar.",
        "Se for indoor/rolo: recovery muito fácil com boa ventilação; não transformar em Z2 longo nem em intensidade.",
        "Recuperação/fueling: défice no máximo leve; proteína alta, hidratação/eletrólitos e hidratos moderados. Evitar défice agressivo hoje."
    ]

    return decision



def normalize_yesterday_compliance_reasons(decision, context):
    """
    Ensure OpenAI reasons don't contradict deterministic yesterday compliance.
    If yesterday was completed within normal margin, remove wording saying it was
    above planned / harder than planned.
    """
    y = context.get("yesterday", {}).get("compliance", {}) or {}
    y_status = str(y.get("status") or "").upper()
    y_interp = str(y.get("interpretation") or "").lower()
    y_ratio = y.get("ratio")

    yesterday_normal_completed = (
        y_status == "CUMPRIDO"
        and "acima" not in y_interp
        and "mais duro" not in y_interp
        and (y_ratio is None or y_ratio < 1.08)
    )

    if not yesterday_normal_completed:
        return decision

    reasons = list(decision.get("reasons") or [])
    cleaned = []
    removed = False

    bad_markers = [
        "ontem", "yesterday"
    ]
    contradiction_markers = [
        "acima", "mais duro", "ligeiramente acima", "above", "harder", "excesso"
    ]

    for r in reasons:
        s = str(r)
        low = s.lower()
        if any(m in low for m in bad_markers) and any(m in low for m in contradiction_markers):
            removed = True
            continue
        cleaned.append(s)

    if removed:
        replacement = "Ontem o treino ajustado foi cumprido dentro da margem; a cautela vem da carga acumulada recente, não de excesso ontem."
        if replacement not in cleaned:
            cleaned.insert(0, replacement)

    decision["reasons"] = cleaned[:5]
    return decision



def normalize_pure_easy_day_decision(decision, context):
    """
    Pure Z2/recovery days are meant to absorb load.
    If OpenAI returns AMARELO for a short pure Z2 workout only because recent load/Form is high,
    the practical prescription must remain Z2/recovery, not tempo/SS blocks.
    Also, if HRV/RHR/sleep are good and the planned workout is short/easy, keep VERDE.
    """
    planned = context.get("planned_events_today", [])
    if not planned:
        return decision

    e = planned[0]
    name = str(e.get("name") or "").lower()
    planned_load = e.get("load") or 0
    planned_hours = e.get("hours") or 0

    easy_terms = ["zone 2", "z2", "endurance", "recovery", "recuper", "easy", "facil", "fácil"]
    quality_terms = ["sweet spot", "threshold", "tempo", "vo2", "interval", "over", "under", "burst", "sprint", "test", "race", "cheetah", "pounce"]

    is_pure_easy = any(t in name for t in easy_terms) and not any(t in name for t in quality_terms)
    if not is_pure_easy:
        return decision

    tm = context.get("today_metrics", {}) or {}
    bl = context.get("baseline_14d", {}) or {}
    hrv_now = tm.get("hrv")
    hrv_base = bl.get("hrv")
    rhr_now = tm.get("resting_hr")
    rhr_base = bl.get("rhr")
    sleep_hours = tm.get("sleep_hours")
    readiness_form = tm.get("readiness_form")

    hrv_good = hrv_now is not None and hrv_base and hrv_now >= hrv_base * 0.95
    rhr_good = rhr_now is not None and rhr_base and rhr_now <= rhr_base + 2
    sleep_good = sleep_hours is not None and sleep_hours >= 7.0
    short_easy = planned_hours <= 1.25 and planned_load <= 60

    # For short Z2 with good readiness, do not turn the day AMARELO just because
    # recent load/Form is still carrying accumulated training stress.
    if decision.get("status") == "AMARELO" and short_easy and hrv_good and rhr_good and sleep_good:
        decision["status"] = "VERDE"
        decision["decision_text"] = "Manter o treino Z2 planeado; fazer fácil e sem acrescentar intensidade."
        reasons = [
            "Treino planeado é Z2 puro e curto; objetivo é absorver carga, não criar novo estímulo.",
            "HRV, RHR e sono estão bons para cumprir Z2 fácil.",
            f"Form pré-treino {fmt(readiness_form,0)} reflete carga acumulada, mas não justifica cortar um Z2 curto; apenas manter RPE/HR baixos."
        ]
        decision["reasons"] = reasons

    # Whether status stays AMARELO or becomes VERDE, pure Z2 actions must remain Z2/recovery.
    if decision.get("status") in ("VERDE", "AMARELO"):
        decision["actions"] = [
            f"Plano normal: fazer {e.get('name') or 'o treino Z2 planeado'} com HR controlada, RPE baixo, sem blocos e sem perseguir TSS.",
            "Se só tiveres 60 min: 60 min Z2 fácil/recovery, HR controlada, RPE baixo, sem blocos.",
            "Se só tiveres 45 min: 45 min recovery/Z2 muito fácil ou descanso, sem blocos.",
            "Se for indoor/rolo: fazer Z2 fácil/recovery com boa ventilação; não transformar em tempo/SS.",
            "Recuperação/fueling: hidratação adequada; hidratos só se precisares/fores vazio, proteína suficiente no dia."
        ]

    return decision



def normalize_projected_metric_reasons(decision, context):
    """
    When Intervals metrics are projected with today's planned workout, do not let
    OpenAI reasons use reported CTL/ATL/Form as if they were pre-workout readiness.
    Keep the decision, but clean the explanation and add deterministic wording
    with the pre-workout values used.
    """
    tm = context.get("today_metrics", {}) or {}
    if not tm.get("metrics_are_projected_after_planned"):
        return decision

    reasons = list(decision.get("reasons") or [])
    cleaned = []
    for r in reasons:
        s = str(r)
        low = s.lower()

        mentions_projected_metrics = any(k in low for k in [
            "fatigue_atl", "fatigue/atl", "atl",
            "fitness_ctl", "fitness/ctl", "ctl",
            "form real", "form report", "form projet", "form projetado",
            "readiness_form", "readiness fatigue", "readiness_fatigue",
        ])

        # Remove reasons that mix reported/projected values or raw variable names.
        if mentions_projected_metrics and any(k in low for k in [
            "report", "projet", "81.", "82.", "67.", "readiness_form", "fatigue_atl"
        ]):
            continue

        cleaned.append(s)

    replacement_reason = (
        "Valores CTL/ATL/Form reportados podem incluir o treino planeado de hoje; "
        f"para readiness pré-treino usei CTL {fmt(tm.get('readiness_fitness_ctl'),0)}, "
        f"ATL {fmt(tm.get('readiness_fatigue_atl'),0)} e Form {fmt(tm.get('readiness_form'),0)}."
    )

    if replacement_reason not in cleaned:
        cleaned.insert(0, replacement_reason)

    decision["reasons"] = cleaned[:5]
    return decision



def normalize_practical_actions(decision, context):
    """
    Forca alternativas praticas coerentes, porque o modelo pode errar contas de duracao.
    - 45 min cabe em 45 min
    - 60 min cabe em 60 min
    - fim de semana indoor cabe em 90 min
    - plano B nao deve ser mais duro que o plano principal
    """
    status = decision.get("status")
    if status in ("JÁ FEITO", "DADOS INCOMPLETOS"):
        return decision

    actions = list(decision.get("actions") or [])
    planned = context.get("planned_events_today", [])
    cal = context.get("calendar_context", {})
    is_weekend = bool(cal.get("weekend_indoor_alternative_required"))

    name = ""
    planned_load = 0
    planned_hours = 0
    if planned:
        name = str(planned[0].get("name") or "")
        planned_load = planned[0].get("load") or 0
        planned_hours = planned[0].get("hours") or 0

    lname = name.lower()
    easy_terms = [
        "zone 2", "z2", "endurance", "recovery", "recuper", "easy", "facil", "fácil"
    ]
    quality_terms = [
        "sweet spot", "threshold", "tempo", "vo2", "interval", "over", "under",
        "burst", "sprint", "test", "race", "cheetah", "pounce"
    ]
    has_easy_terms = any(t in lname for t in easy_terms)
    has_quality_terms = any(t in lname for t in quality_terms)

    # Quality terms override easy terms for mixed workouts like:
    # "Sweet Spot 2 x 15 min + Z2 cap 200W".
    # These are not pure Z2 days; they are controlled quality days.
    is_quality = has_quality_terms or (planned_load >= 80 and not has_easy_terms)
    is_easy = (has_easy_terms and not has_quality_terms) or (planned_load <= 45 and not is_quality)
    is_mixed_quality_easy = has_quality_terms and has_easy_terms
    amarelo_forte_long_quality = (
        status == "AMARELO"
        and yellow_long_quality_risk(context, planned_load, planned_hours, lname, is_quality)
    )

    long_or_social_weekend = planned_hours > 2.05 or any(t in lname for t in ["social", "group ride", "long", "longo", "endurance ride", "ride 3h", "ride 4h", "ride 5h"])

    if status == "VERMELHO":
        a60 = "Se só tiveres 60 min: não usar para compensar; descanso total ou 45–60 min recovery muito leve em Z1/Z2."
        a45 = "Se só tiveres 45 min: descanso total preferível; se precisares mexer as pernas, 30–45 min rolo muito fácil."
        indoor = "Se for indoor/rolo: recovery muito leve, sem blocos, ou descanso total."
        weekend_alt = "Se for sábado/domingo e não der para sair: descanso total ou 45–60 min rolo muito fácil; nada de intensidade."
        weekend_weather = "Se chover/condições forem más: não forces a saída; descanso total ou recovery muito leve."
    elif status == "AMARELO":
        if is_easy:
            a60 = "Se só tiveres 60 min: 60 min Z2 fácil/recovery, HR controlada, RPE baixo, sem blocos."
            a45 = "Se só tiveres 45 min: 45 min recovery/Z2 muito fácil ou descanso, sem blocos."
            indoor = "Se for indoor/rolo: fazer Z2 fácil/recovery com boa ventilação; não transformar em tempo/SS."
            weekend_alt = "Se for sábado/domingo e não der para sair: 60–90 min Z2/recovery muito fácil; sem intensidade."
            weekend_weather = f"Se chover/condições forem más: faz {name or 'o treino Z2 planeado'} indoor/rolo em Z2 fácil, sem blocos."
        elif amarelo_forte_long_quality:
            decision["decision_text"] = "AMARELO forte: não fazer o treino longo/de qualidade como planeado; substituir por Z2 fácil/endurance controlado."
            extra_reasons = decision.setdefault("reasons", [])
            msg = "Treino longo/de qualidade planeado após dia acima do planeado e readiness comprometida; reduzir para Z2, não apenas -3%."
            if msg not in extra_reasons:
                extra_reasons.append(msg)
            a60 = "Se só tiveres 60 min: 60 min Z2/recovery muito fácil, HR controlada, sem blocos."
            a45 = "Se só tiveres 45 min: 45 min recovery muito fácil ou descanso total."
            indoor = "Se for indoor/rolo: Z2 fácil/recovery; sem tempo, sem sweet spot, sem perseguir watts."
            weekend_alt = "Se for sábado/domingo e não der para sair ou se o treino planeado for demasiado pesado: 90–120 min Z2 fácil/endurance, sem blocos e sem perseguir TSS."
            weekend_weather = f"Se chover/condições forem más: não tentar salvar {name or 'o treino planeado'}; fazer 90–120 min Z2 fácil ou descanso."
        else:
            a60 = "Se só tiveres 60 min: 10 min aquecer, 2x8 min tempo leve @80–85% com 5 min Z2, resto Z2 fácil, 5 min arrefecer."
            a45 = "Se só tiveres 45 min: 10 min aquecer, 1x12 min tempo leve @80–85%, resto Z2 fácil, 5 min arrefecer."
            indoor = "Se for indoor/rolo: versão reduzida; Z2 dominante e no máximo 2x8 min tempo leve @80–85%, sem perseguir watts."
            weekend_alt = "Se for sábado/domingo e não der para sair: 90 min indoor — 15 min aquecer, 2x15 min tempo leve @80–85% com 8 min Z2, completar Z2, 10 min arrefecer."
            weekend_weather = f"Se chover/condições forem más: faz uma versão indoor reduzida de {name or 'o treino planeado'}, mantendo Z2 dominante e sem forçar intensidade."
    else:
        if is_easy:
            a60 = "Se só tiveres 60 min: 60 min Z2 fácil/recovery, HR controlada, RPE baixo, sem blocos."
            a45 = "Se só tiveres 45 min: 45 min recovery/Z2 muito fácil ou descanso, sem blocos."
            indoor = "Se for indoor/rolo: fazer Z2 fácil/recovery com boa ventilação; não transformar em tempo/SS."
            weekend_alt = "Se for sábado/domingo e não der para sair: 90 min indoor — Z2 contínuo confortável, 3x1 min cadência alta opcional, sem intensidade."
            weekend_weather = f"Se chover/condições forem más: faz {name or 'o treino planeado'} indoor/rolo, mantendo Z2 fácil e RPE baixo."
        else:
            a60 = "Se só tiveres 60 min: 10 min aquecer, 2x12 min tempo/SS baixo @85–88% com 6 min Z2, resto Z2 fácil, 5 min arrefecer."
            a45 = "Se só tiveres 45 min: 10 min aquecer, 2x8 min tempo/SS baixo @85–88% com 5 min Z2, 9 min Z2 fácil, 5 min arrefecer."
            indoor = "Se for indoor/rolo: manter controlado; usar 85–88% para tempo/SS baixo, não ir até FTP; ventoinha forte e RPE estável."
            weekend_alt = "Se for sábado/domingo e não der para sair: 90 min indoor — 15 min aquecer, 3x12 min tempo/SS baixo @85–88% com 6 min Z2, completar Z2, 10 min arrefecer."
            weekend_weather = f"Se chover/condições forem más: faz {name or 'o treino planeado'} indoor/rolo como planeado; é até 2h e é fazível no rolo. Ventoinha forte, hidratação e RPE controlado."

    def replaceable(action):
        s = str(action).lower().strip()

        practical_markers = [
            "se só tiveres 60", "se so tiveres 60", "if só tiveres 60", "if so tiveres 60",
            "se só tiveres 45", "se so tiveres 45", "if só tiveres 45", "if so tiveres 45",
            "se tiveres 60", "se tiveres 45",
            "se for indoor", "if for indoor",
            "se chover", "if chover", "se as condições", "se as condicoes",
            "se for sábado/domingo", "se for sabado/domingo",
            "if for sábado/domingo", "if for sabado/domingo",
        ]
        if any(s.startswith(m) for m in practical_markers):
            return True

        if ("45 min" in s or "60 min" in s or "90 min" in s) and (
            "só tiveres" in s or "so tiveres" in s or "indoor" in s or "rolo" in s or
            "sábado" in s or "sabado" in s or "domingo" in s
        ):
            return True

        if amarelo_forte_long_quality and (
            "reduzir" in s or "-3" in s or "3%" in s or "eliminar um bloco" in s or "cortar um bloco" in s
            or "sweet spot group ride" in s or "group ride" in s
        ):
            return True

        return False

    cleaned = [a for a in actions if not replaceable(a)]
    if amarelo_forte_long_quality:
        cleaned = [a for a in cleaned if not str(a).lower().startswith("plano normal")]
        cleaned.insert(0, "Plano normal ajustado: não fazer o treino longo/de qualidade como planeado; fazer 90–120 min Z2 fácil/endurance, sem blocos, ou descanso se as pernas estiverem pesadas.")
    elif not any(str(a).lower().startswith("plano normal") for a in cleaned):
        if planned:
            cleaned.insert(0, f"Plano normal: fazer {name} conforme planeado, sem acrescentar carga.")
        else:
            cleaned.insert(0, "Plano normal: descanso total preferencial; se quiseres pedalar, Z2 muito fácil, sem blocos.")

    no_planned_workout = not planned or planned_load <= 5
    y = context.get("yesterday", {}).get("compliance", {}) or {}
    y_done_load = y.get("done_load") or 0
    y_done_hours = y.get("done_hours") or 0
    y_status = str(y.get("status") or "").upper()
    recent_load_3d = (context.get("recent_3d", {}) or {}).get("load") or 0
    big_yesterday = y_done_load >= 150 or y_done_hours >= 3.0 or "MAIS DURO" in y_status
    high_recent_load = recent_load_3d >= 300
    if no_planned_workout:
        if mild_fatigue_no_plan(context):
            decision["decision_text"] = "Descanso total preferencial; no máximo recovery muito fácil se quiseres mexer as pernas."
            a60 = "Se tiveres 60 min disponíveis: não é preciso usar os 60; faz 30–45 min recovery muito fácil ou descansa."
            a45 = "Se quiseres rolar 45 min: recovery/Z1-Z2 muito fácil, HR baixa, RPE 1–2/10, sem blocos."
            indoor = "Se for indoor/rolo: recovery muito fácil com boa ventilação; não transformar em Z2 longo nem em intensidade."
        elif big_yesterday or high_recent_load:
            decision["decision_text"] = "Descanso total preferencial; no máximo recovery muito fácil conforme sensação."
            a60 = "Se quiseres mesmo rolar 60 min: só recovery/Z1-Z2 muito fácil, HR baixa, sem blocos."
            a45 = "Se quiseres rolar 45 min: recovery muito fácil; descanso total também é excelente."
            indoor = "Se for indoor/rolo: soltar pernas muito fácil; não transformar recuperação em treino."
        else:
            a60 = "Se quiseres rolar 60 min: Z2 muito fácil/recovery, HR controlada, sem blocos."
            a45 = "Se quiseres rolar 45 min: recovery muito fácil ou descanso total."
            indoor = "Se for indoor/rolo: rolar muito fácil com boa ventilação; não transformar descanso em treino."

    if is_weekend and is_easy and planned_hours > 2.05:
        cleaned.append("Se 2h30 não encaixar no sábado: 2h Z2 bem feitas são válidas; manter HR/RPE baixos e não perseguir TSS.")
    cleaned.append(a60)
    cleaned.append(a45)
    cleaned.append(indoor)
    if is_weekend:
        if long_or_social_weekend:
            cleaned.append(weekend_alt)
        else:
            cleaned.append(weekend_weather)
    recovery_lines = [
        a for a in cleaned
        if ("recuper" in str(a).lower() or "fuel" in str(a).lower() or "hidrata" in str(a).lower())
    ]
    cleaned = [
        a for a in cleaned
        if not ("recuper" in str(a).lower() or "fuel" in str(a).lower() or "hidrata" in str(a).lower())
    ]

    if no_planned_workout and (big_yesterday or high_recent_load):
        recovery = "Recuperação/fueling: após carga alta, não fazer défice agressivo; proteína 150–170 g, hidratos moderados, hidratação e eletrólitos."
    elif recovery_lines:
        recovery = recovery_lines[0]
    else:
        recovery = "Recuperação/fueling: comer e hidratar de acordo com a sessão; não fazer défice agressivo em dia de qualidade."

    cleaned.append(recovery)

    decision["actions"] = cleaned
    return decision


def parse_openai_coach_text(response_text):
    """
    Parser tolerante para o formato:
    STATUS:
    DECISION:
    REASONS:
    - ...
    ACTIONS:
    - ...
    SHOULD_MODIFY_INTERVALS:
    """
    text = response_text.replace("\r\n", "\n").replace("\r", "\n").strip()

    status_match = re.search(r"^\s*STATUS\s*:\s*(VERDE|AMARELO|VERMELHO)\s*$", text, re.I | re.M)
    if not status_match:
        status_match = re.search(r"\b(VERDE|AMARELO|VERMELHO)\b", text, re.I)
    if not status_match:
        raise ValueError("não consegui ler STATUS da resposta OpenAI")

    status = status_match.group(1).upper()

    decision_match = re.search(r"^\s*DECISION\s*:\s*(.+?)\s*$", text, re.I | re.M)
    decision_text = decision_match.group(1).strip() if decision_match else ""

    def block_items(header, next_headers):
        pattern = rf"^\s*{header}\s*:\s*\n(?P<body>.*?)(?=^\s*(?:{'|'.join(next_headers)})\s*:|\Z)"
        m = re.search(pattern, text, re.I | re.M | re.S)
        if not m:
            return []
        body = m.group("body").strip()
        items = []
        for line in body.splitlines():
            line = line.strip()
            if not line:
                continue
            line = re.sub(r"^[-*•]\s*", "", line).strip()
            if line:
                items.append(line)
        return items

    reasons = block_items("REASONS", ["ACTIONS", "SHOULD_MODIFY_INTERVALS"])
    actions = block_items("ACTIONS", ["SHOULD_MODIFY_INTERVALS"])

    modify_match = re.search(r"^\s*SHOULD_MODIFY_INTERVALS\s*:\s*(true|false|sim|não|nao|yes|no)\s*$", text, re.I | re.M)
    should_modify = False
    if modify_match:
        val = modify_match.group(1).lower()
        should_modify = val in ("true", "sim", "yes")

    if not reasons:
        reasons = ["OpenAI não listou motivos em formato esperado; decisão interpretada pelo status."]
    if not actions:
        if status == "VERDE":
            actions = ["Manter o treino planeado; se não houver treino planeado, descanso ou Z2 fácil."]
        elif status == "AMARELO":
            actions = ["Reduzir/cortar treino planeado; se não houver treino planeado, descanso ou Z2 fácil."]
        else:
            actions = ["Recovery/Z2 ou descanso total."]

    return {
        "status": status,
        "decision_text": decision_text,
        "reasons": reasons,
        "actions": actions,
        "should_modify_intervals": should_modify,
    }


def build_replacement_event(original, target_date, status, decision_text, reasons, actions):
    original_name = original.get("name") or "treino planeado"
    ext_id = original.get("external_id")
    if not ext_id:
        return None, "O treino de hoje não tem external_id; não vou substituir automaticamente para evitar duplicados."

    kind = choose_replacement_kind(status, original_name)
    steps = replacement_steps(kind)
    duration = dur_min(steps)
    new_load = est_load_steps(steps)

    if status == "VERMELHO":
        new_name = f"AJUSTADO — Recovery/Z2 60min (substitui: {original_name})"
    else:
        new_name = f"AJUSTADO — versão reduzida ({original_name})"

    zwo_text = zwo_from_steps(new_name, steps)
    filename = safe_filename(new_name)
    zwo_b64 = base64.b64encode(zwo_text.encode("utf-8")).decode("ascii")

    start_raw = original.get("start_date_local") or f"{target_date.isoformat()}T11:30:00"
    start_dt = parse_datetime_local(start_raw, target_date)
    end_dt = start_dt + dt.timedelta(minutes=duration)

    desc = []
    desc.append("Alterado automaticamente pelo Daily Coach Agent.")
    desc.append(f"Estado: {status}")
    desc.append("")
    desc.append("Treino original:")
    desc.append(original_name)
    desc.append("")
    desc.append("Decisão:")
    desc.append(decision_text or "")
    desc.append("")
    desc.append("Motivos:")
    desc += [f"- {r}" for r in reasons]
    desc.append("")
    desc.append("Ações:")
    desc += [f"- {a}" for a in actions]

    ev = {
        "category": "WORKOUT",
        "type": original.get("type") or "Ride",
        "start_date_local": start_dt.isoformat(timespec="seconds"),
        "end_date_local": end_dt.isoformat(timespec="seconds"),
        "name": new_name,
        "description": "\n".join(desc),
        "moving_time": duration * 60,
        "load": new_load,
        "icu_training_load": new_load,
        "external_id": ext_id,
        "filename": filename,
        "file_contents_base64": zwo_b64,
    }
    return ev, None



def smtp_configured():
    required = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "TO_EMAIL"]
    return all(os.getenv(k, "").strip() for k in required)


def send_email_report(subject, body, attachment_paths=None):
    if not smtp_configured():
        return False, "SMTP não configurado; e-mail não enviado."

    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587").strip())
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    to_email = os.getenv("TO_EMAIL", "").strip()
    from_email = os.getenv("FROM_EMAIL", user).strip() or user

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    for p in attachment_paths or []:
        path = Path(p)
        if not path.exists():
            continue
        data = path.read_bytes()
        msg.add_attachment(
            data,
            maintype="application",
            subtype="octet-stream",
            filename=path.name,
        )

    with smtplib.SMTP(host, port, timeout=45) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(msg)

    return True, f"E-mail enviado para {to_email}."


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--email", action="store_true", help="Enviar relatório por e-mail se SMTP estiver configurado.")
    args = parser.parse_args()

    intervals_key = os.getenv("INTERVALS_API_KEY", "").strip()
    athlete_id = os.getenv("ATHLETE_ID", "0").strip() or "0"
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    openai_model = os.getenv("OPENAI_MODEL", "gpt-5-mini").strip()
    openai_reasoning_effort = get_openai_reasoning_effort("medium")
    auto_apply = bool_env("AUTO_APPLY", False)

    if not intervals_key:
        raise RuntimeError("Falta INTERVALS_API_KEY nos secrets/env.")

    allow_apply = (args.apply or (args.auto and auto_apply)) and not args.dry_run

    target = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    yesterday = target - dt.timedelta(days=1)
    start = target - dt.timedelta(days=args.days)
    end = target + dt.timedelta(days=1)

    client = IntervalsClient(athlete_id, intervals_key)
    athlete = client.athlete()
    if athlete_id == "0" and athlete.get("id"):
        client.athlete_id = athlete["id"]

    wellness = client.wellness_range(start, end)
    activities = client.activities_range(start, end)
    events = client.events_range(yesterday, target)

    by_day = {}
    for w in wellness:
        d = parse_item_date(w)
        if d:
            by_day[d] = w

    today_w = by_day.get(target, {})
    yesterday_w = by_day.get(yesterday, {})
    prev14 = [by_day[d] for d in [target - dt.timedelta(days=i) for i in range(1, 15)] if d in by_day]
    prev7 = [by_day[d] for d in [target - dt.timedelta(days=i) for i in range(1, 8)] if d in by_day]
    baseline = {
        "hrv": mean([hrv(w) for w in prev14]),
        "rhr": mean([rhr(w) for w in prev14]),
        "sleep": mean([sleep_h(w) for w in prev14]),
        "weight_7d": mean([weight_kg(w) for w in prev7]),
    }

    recent_load = 0.0
    recent_hours = 0.0
    for a in activities:
        d = parse_item_date(a)
        if d and target - dt.timedelta(days=3) <= d <= target - dt.timedelta(days=1):
            recent_load += load(a) or 0
            recent_hours += hours(a) or 0

    today_events = events_on(events, target)
    done_today = completed_activities_on(activities, target)
    yesterday_events = events_on(events, yesterday)
    done_yesterday = completed_activities_on(activities, yesterday)
    yesterday_compliance = compliance_check(yesterday_events, done_yesterday)

    planned_loads = [load(e) for e in today_events if load(e) is not None]
    planned_load = sum(planned_loads) if planned_loads else None

    reported_fitness_today = ctl(today_w)
    reported_fatigue_today = atl(today_w)
    reported_form_today = form(today_w)

    readiness_fitness = pre_workout_metric(today_w, yesterday_w, ctl, planned_load, bool(done_today))
    readiness_fatigue = pre_workout_metric(today_w, yesterday_w, atl, planned_load, bool(done_today))
    readiness_form = pre_workout_form(today_w, yesterday_w, planned_load, bool(done_today))

    metrics_projected_after_planned = bool(
        planned_load and planned_load > 0 and not done_today and (
            readiness_form != reported_form_today
            or readiness_fatigue != reported_fatigue_today
            or readiness_fitness != reported_fitness_today
        )
    )

    context = {
        "date": target.isoformat(),
        "athlete": {"id": athlete.get("id"), "name": athlete.get("name")},
        "today_metrics": {
            "sleep_hours": sleep_h(today_w),
            "sleep_score": sleep_score(today_w),
            "hrv": hrv(today_w),
            "resting_hr": rhr(today_w),
            "weight_kg": weight_kg(today_w),
            "fitness_ctl": reported_fitness_today,
            "fatigue_atl": reported_fatigue_today,
            "form": reported_form_today,
            "readiness_fitness_ctl": readiness_fitness,
            "readiness_fatigue_atl": readiness_fatigue,
            "readiness_form": readiness_form,
            "metrics_are_projected_after_planned": metrics_projected_after_planned,
            "form_is_projected_after_planned": bool(planned_load and planned_load > 0 and not done_today and readiness_form != reported_form_today),
            "fatigue_is_projected_after_planned": bool(planned_load and planned_load > 0 and not done_today and readiness_fatigue != reported_fatigue_today),
            "fitness_is_projected_after_planned": bool(planned_load and planned_load > 0 and not done_today and readiness_fitness != reported_fitness_today),
        },
        "baseline_14d": baseline,
        "recent_3d": {"load": recent_load, "hours": recent_hours},
        "planned_events_today": [
            {
                "id": e.get("id"),
                "external_id": e.get("external_id"),
                "name": e.get("name"),
                "load": load(e),
                "hours": hours(e),
                "start_date_local": e.get("start_date_local"),
                "type": e.get("type"),
            } for e in today_events
        ],
        "completed_activities_today": [
            {"name": a.get("name"), "type": a.get("type"), "load": load(a), "hours": hours(a)}
            for a in done_today
        ],
        "yesterday": {
            "date": yesterday.isoformat(),
            "compliance": yesterday_compliance,
            "planned_events": [{"name": e.get("name"), "load": load(e), "hours": hours(e)} for e in yesterday_events],
            "completed_activities": [{"name": a.get("name"), "load": load(a), "hours": hours(a)} for a in done_yesterday],
        },
        "counts": {
            "wellness_days": len(wellness),
            "activities": len(activities),
            "events": len(events),
            "baseline_days": len(prev14),
        },
    }

    context["calendar_context"] = {
        "weekday": target.strftime("%A"),
        "weekday_number": target.weekday(),
        "is_weekend": target.weekday() >= 5,
        "weekend_indoor_alternative_required": target.weekday() >= 5,
    }

    required_today_metrics = {
        "sleep_hours": context["today_metrics"].get("sleep_hours"),
        "hrv": context["today_metrics"].get("hrv"),
        "resting_hr": context["today_metrics"].get("resting_hr"),
    }
    missing_today_metrics = [k for k, v in required_today_metrics.items() if v is None]
    context["data_quality"] = {
        "required_today_metrics": required_today_metrics,
        "missing_today_metrics": missing_today_metrics,
        "is_complete": len(missing_today_metrics) == 0,
    }

    context["done_today_summary"] = {
        "has_activity": bool(done_today),
        "load": sum((a.get("load") or 0) for a in done_today),
        "hours": sum((a.get("hours") or 0) for a in done_today),
        "count": len(done_today),
    }

    context["fueling_guidance"] = fueling_guidance(
        context,
        weight_today=context["today_metrics"].get("weight_kg"),
        weight_avg_7d=context["baseline_14d"].get("weight_7d"),
    )

    heuristic = heuristic_decision(today_w, baseline, recent_load, planned_load, yesterday_compliance, readiness_form=readiness_form)

    if missing_today_metrics:
        decision = {
            "status": "DADOS INCOMPLETOS",
            "decision_text": "Dados incompletos: atualiza/sincroniza os dados no Intervals e corre manualmente o Daily Coach.",
            "reasons": [
                "Faltam métricas essenciais de hoje: " + ", ".join(missing_today_metrics) + ".",
                "Prefiro não dar uma recomendação de treino baseada em dados incompletos.",
                "Depois de Garmin/Intervals sincronizarem sono, HRV e resting HR, corre o workflow manualmente."
            ],
            "actions": [
                "Abrir Garmin/Intervals e confirmar sincronização dos dados de hoje.",
                "Correr manualmente o Daily Coach Agent depois da sincronização.",
                "Até lá: não alterar treino automaticamente; se precisares sair já, escolhe a opção mais conservadora."
            ],
            "should_modify_intervals": False,
            "source": "data_quality_guard",
        }
        ai_error = None
    elif done_today:
        done_today_load = sum((load(a) or 0.0) for a in done_today)
        done_today_hours = sum((hours(a) or 0.0) for a in done_today)
        decision = {
            "status": "JÁ FEITO",
            "decision_text": "Já existe atividade concluída hoje no Intervals. Não vou recomendar nem substituir outro treino.",
            "reasons": [
                f"Atividade hoje: {fmt(done_today_load,0)} TSS / {fmt_h(done_today_hours)}.",
                "O agente foi corrido depois do treino."
            ],
            "actions": [
                "Não repetir treino.",
                "Priorizar recuperação, hidratação e nutrição pós-treino.",
                "Monitorizar sensação, sono e HRV amanhã para decidir a próxima sessão.",
            ],
            "should_modify_intervals": False,
            "source": "done_detection",
        }
        ai_error = None
    else:
        ai_decision, ai_error = call_openai(openai_key, openai_model, openai_reasoning_effort, {**context, "heuristic_decision": heuristic})
        decision = ai_decision or heuristic

    decision = normalize_no_plan_recovery_day(decision, context)
    decision = normalize_yesterday_compliance_reasons(decision, context)
    decision = normalize_pure_easy_day_decision(decision, context)
    decision = normalize_projected_metric_reasons(decision, context)
    decision = normalize_practical_actions(decision, context)

    if ai_error and decision.get("source") != "openai":
        decision.setdefault("reasons", []).append(f"Nota técnica: {ai_error}")

    applied = False
    apply_error = None

    if decision.get("status") in ("AMARELO", "VERMELHO"):
        if not today_events:
            apply_error = "sem treino planeado hoje."
        elif allow_apply:
            replacement, err = build_replacement_event(
                original=today_events[0],
                target_date=target,
                status=decision["status"],
                decision_text=decision.get("decision_text", ""),
                reasons=decision.get("reasons", []),
                actions=decision.get("actions", []),
            )
            if err:
                apply_error = err
            else:
                Path("last_update_payload.json").write_text(json.dumps(replacement, indent=2, ensure_ascii=False), encoding="utf-8")
                client.upload_bulk_events([replacement])
                applied = True
        else:
            apply_error = "AUTO_APPLY desligado, --dry-run ativo ou execução sem permissão de apply."
    elif decision.get("status") == "JÁ FEITO":
        apply_error = "já existe atividade feita hoje; nada alterado."
    elif decision.get("status") == "DADOS INCOMPLETOS":
        apply_error = "dados de hoje incompletos; nada alterado."

    lines = []
    lines.append("=" * 72)
    lines.append(f"DAILY COACH AGENT — {target.isoformat()}")
    lines.append("=" * 72)
    lines.append(f"Atleta: {athlete.get('name') or athlete.get('id') or 'n/d'}")
    lines.append(f"Fonte decisão: {decision.get('source')}")
    lines.append("")
    lines.append("TREINO PLANEADO HOJE")
    if context["planned_events_today"]:
        for e in context["planned_events_today"]:
            lines.append(f"- {e.get('name')} | load={fmt(e.get('load'),0)} | duração={fmt_h(e.get('hours'))} | external_id={e.get('external_id') or 'n/d'}")
    else:
        lines.append("- Sem treino planeado encontrado.")
    lines.append("")
    lines.append("ATIVIDADE JÁ FEITA HOJE")
    if context["completed_activities_today"]:
        for a in context["completed_activities_today"]:
            lines.append(f"- {a.get('name') or a.get('type') or '(atividade)'} | load={fmt(a.get('load'),0)} | duração={fmt_h(a.get('hours'))}")
    else:
        lines.append("- Nenhuma atividade concluída hoje encontrada.")
    lines.append("")
    lines.append("ONTEM — PLANO VS REALIZADO")
    yc = context["yesterday"]["compliance"]
    lines.append(f"Estado: {yc['status']}")
    lines.append(f"Planeado: {fmt(yc['planned_load'],0)} TSS | {fmt_h(yc['planned_hours'])}")
    lines.append(f"Realizado: {fmt(yc['done_load'],0)} TSS | {fmt_h(yc['done_hours'])}")
    if yc.get("interpretation"):
        lines.append(f"Leitura: {yc.get('interpretation')}")
    lines.append("")
    tm = context["today_metrics"]
    bl = context["baseline_14d"]
    lines.append("DADOS")
    lines.append(f"- Sono: {fmt_h(tm.get('sleep_hours'))} | score: {fmt(tm.get('sleep_score'),0)}")
    lines.append(f"- HRV: {fmt(tm.get('hrv'))} | baseline 14d: {fmt(bl.get('hrv'))}")
    lines.append(f"- Resting HR: {fmt(tm.get('resting_hr'),0)} bpm | baseline 14d: {fmt(bl.get('rhr'),0)} bpm")
    lines.append(f"- Peso: {fmt(tm.get('weight_kg'),1)} kg | média 7d: {fmt(bl.get('weight_7d'),1)} kg | objetivo: 74,0 kg")
    if tm.get("metrics_are_projected_after_planned"):
        lines.append(
            f"- Fitness/CTL reportada: {fmt(tm.get('fitness_ctl'),0)} | pré-treino usada: {fmt(tm.get('readiness_fitness_ctl'),0)}"
            f" | Fatigue/ATL reportada: {fmt(tm.get('fatigue_atl'),0)} | pré-treino usada: {fmt(tm.get('readiness_fatigue_atl'),0)}"
            f" | Form reportada: {fmt(tm.get('form'),0)} | pré-treino usada: {fmt(tm.get('readiness_form'),0)}"
        )
    else:
        lines.append(
            f"- Fitness/CTL: {fmt(tm.get('fitness_ctl'),0)}"
            f" | Fatigue/ATL: {fmt(tm.get('fatigue_atl'),0)}"
            f" | Form usada: {fmt(tm.get('readiness_form'),0)}"
        )
    lines.append(f"- Últimos 3 dias: {fmt(context['recent_3d'].get('load'),0)} TSS | {fmt_h(context['recent_3d'].get('hours'))}")
    dq = context.get("data_quality", {})
    if not dq.get("is_complete", True):
        lines.append(f"- Qualidade dos dados: INCOMPLETA — faltam {', '.join(dq.get('missing_today_metrics', []))}")
    else:
        lines.append("- Qualidade dos dados: completa")
    lines.append("")
    lines.append("PESO / FUELING")
    lines += [f"- {x}" for x in context.get("fueling_guidance", [])]
    lines.append("")
    lines.append("DECISÃO")
    lines.append(f"Estado: {decision.get('status')}")
    if decision.get("decision_text"):
        lines.append(decision["decision_text"])
    lines.append("")
    lines.append("Motivos:")
    lines += [f"- {r}" for r in decision.get("reasons", [])] or ["- n/d"]
    lines.append("")
    lines.append("Ações:")
    lines += [f"- {a}" for a in decision.get("actions", [])] or ["- n/d"]
    lines.append("")
    lines.append("INTERVALS")
    if applied:
        lines.append("- Treino substituído automaticamente no Intervals.")
    elif apply_error:
        lines.append(f"- Não alterado: {apply_error}")
    else:
        lines.append("- Não alterado.")
    lines.append("")

    report = "\n".join(lines)
    Path("daily_agent_report.txt").write_text(report, encoding="utf-8")
    Path("daily_agent_report.json").write_text(json.dumps({
        "context": context,
        "heuristic_decision": heuristic,
        "decision": decision,
        "ai_error": ai_error,
        "applied": applied,
        "apply_error": apply_error,
    }, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    if args.debug:
        Path("debug_raw_agent.json").write_text(json.dumps({
            "wellness": wellness,
            "activities": activities[:50],
            "events": events,
        }, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    email_status = None
    if args.email:
        subject_status = decision.get("status") or "n/d"
        subject = f"Daily Coach — {subject_status} — {target.isoformat()}"
        ok, msg = send_email_report(
            subject=subject,
            body=report,
            attachment_paths=["daily_agent_report.json"],
        )
        email_status = msg
        report += "\nEMAIL\n"
        report += f"- {msg}\n"
        Path("daily_agent_report.txt").write_text(report, encoding="utf-8")

    print(report)

    github_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if github_summary:
        with open(github_summary, "a", encoding="utf-8") as f:
            f.write("## Daily Coach Agent\n\n")
            f.write("```text\n")
            f.write(report)
            f.write("\n```\n")


if __name__ == "__main__":
    main()
