#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weekly Planner Agent — Intervals.icu

Cria/atualiza a semana de treino com base no plano macro de 12 semanas,
na semana anterior e no último wellness disponível.

Este agente é deliberadamente rule-based para manter progressão e coerência.
O daily agent continua a fazer o ajuste fino diário com OpenAI.

Secrets/env:
- INTERVALS_API_KEY
- ATHLETE_ID
- SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD / TO_EMAIL
- PLAN_START_DATE optional, default 2026-05-11
- PLAN_ID optional, default coach-pro-nuno-12w-domingo-generico-150tss-v1
- WEEKLY_AUTO_APPLY optional, default false
"""

import argparse
import base64
import datetime as dt
import json
import math
import os
import re
import smtplib
import statistics
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

API_BASE = "https://intervals.icu/api/v1"
AUTH_USER = "API_KEY"
DEFAULT_PLAN_START_DATE = "2026-05-11"
DEFAULT_PLAN_ID = "coach-pro-nuno-12w-domingo-generico-150tss-v1"
TIMEZONE = "Europe/Lisbon"


def bool_env(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "sim", "y")


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


def metric_load(item):
    return fnum(first(item, ["icu_training_load", "training_load", "load", "tss", "TSS"]))


def metric_hours(item):
    v = fnum(first(item, ["moving_time", "elapsed_time", "duration", "duration_secs", "total_timer_time"]))
    if v is None:
        return None
    if v > 1000:
        return v / 3600
    if v > 20:
        return v / 60
    return v


def sleep_h(w):
    v = fnum(first(w, ["sleepSecs", "sleepSeconds", "sleep_seconds", "sleepTime", "sleep_time", "totalSleepSeconds"]))
    if v is None:
        return None
    if v > 1000:
        return v / 3600
    if v > 60:
        return v / 60
    return v


def hrv(w):
    return fnum(first(w, ["hrv", "hrvRmssd", "hrv_rmssd", "rmssd", "HRV"]))


def rhr(w):
    return fnum(first(w, ["restingHR", "resting_hr", "restingHeartRate", "rhr"]))


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
    return f"{total_minutes // 60}h{total_minutes % 60:02d}"


def monday_of(d):
    return d - dt.timedelta(days=d.weekday())


def safe_filename(name):
    trans = str.maketrans({"ç":"c","ã":"a","á":"a","é":"e","ó":"o","í":"i","ú":"u","â":"a","ê":"e","ô":"o","à":"a","õ":"o","º":"o","≤":"le","—":"-"})
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


# ----- Workout helpers -----

def wu(dur=720, lo=45, hi=72): return {"type":"Warmup","duration":dur,"power_low":lo,"power_high":hi}
def cd(dur=600, hi=60, lo=38): return {"type":"Cooldown","duration":dur,"power_low":hi,"power_high":lo}
def ss(dur, pwr): return {"type":"SteadyState","duration":dur,"power":pwr}
def itv(reps,on_dur,on_pwr,off_dur,off_pwr): return {"type":"IntervalsT","reps":reps,"on_duration":on_dur,"on_power":on_pwr,"off_duration":off_dur,"off_power":off_pwr}


def z2(minutes, pwr=63):
    return [wu(600,45,62), ss((minutes-20)*60,pwr), cd(600,58,36)]


def sunday_150():
    return [ss(10800,70.7)]


def duration_min(steps):
    sec = 0
    for s in steps:
        if s["type"] in ("Warmup","Cooldown","SteadyState"):
            sec += s["duration"]
        else:
            sec += s["reps"] * (s["on_duration"] + s["off_duration"])
    return round(sec/60)


def est_load_steps(steps):
    work = 0.0
    for s in steps:
        if s["type"] in ("Warmup","Cooldown"):
            p = ((s["power_low"] + s["power_high"]) / 2) / 100
            work += s["duration"] * p * p
        elif s["type"] == "SteadyState":
            p = s["power"] / 100
            work += s["duration"] * p * p
        else:
            pon = s["on_power"] / 100
            poff = s["off_power"] / 100
            work += s["reps"] * (s["on_duration"] * pon * pon + s["off_duration"] * poff * poff)
    return max(1, round(work/36))


def pct(x): return round(float(x)/100, 4)


def xml_escape(x):
    return str(x).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")


def zwo(name, steps):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<workout_file>", f"  <name>{xml_escape(name)}</name>", "  <sportType>bike</sportType>", "  <tags>", '    <tag name="Weekly Planner Agent" />', '    <tag name="Rolling 12W" />', "  </tags>", "  <workout>"]
    for s in steps:
        if s["type"] == "Warmup":
            lines.append(f'    <Warmup Duration="{s["duration"]}" PowerLow="{pct(s["power_low"])}" PowerHigh="{pct(s["power_high"])}" />')
        elif s["type"] == "Cooldown":
            lines.append(f'    <Cooldown Duration="{s["duration"]}" PowerLow="{pct(s["power_low"])}" PowerHigh="{pct(s["power_high"])}" />')
        elif s["type"] == "SteadyState":
            lines.append(f'    <SteadyState Duration="{s["duration"]}" Power="{pct(s["power"])}" />')
        elif s["type"] == "IntervalsT":
            lines.append(f'    <IntervalsT Repeat="{s["reps"]}" OnDuration="{s["on_duration"]}" OffDuration="{s["off_duration"]}" OnPower="{pct(s["on_power"])}" OffPower="{pct(s["off_power"])}" />')
    lines += ["  </workout>", "</workout_file>"]
    return "\n".join(lines)


def scale_hard(steps, delta=-3):
    out = []
    for s in steps:
        s = dict(s)
        if s["type"] == "SteadyState" and s.get("power",0) >= 85:
            s["power"] += delta
        elif s["type"] == "IntervalsT":
            if s.get("on_power",0) >= 95:
                s["on_power"] += delta
            if s.get("off_power",0) >= 85:
                s["off_power"] += delta
        out.append(s)
    return out


def base_week(macro_week):
    phase_week = ((macro_week - 1) % 4) + 1

    if macro_week in (4,8):
        return {
            1: ("S%02d Ter — Recovery 60min" % macro_week, "Descarga real.", z2(60,58)),
            2: ("S%02d Qua — Z2 fácil 75min" % macro_week, "Recuperação ativa.", z2(75,61)),
            3: ("S%02d Qui — SS leve 2x10 @88%%" % macro_week, "Toque curto; sem fadiga.", [wu(720,45,68), ss(300,62), itv(2,600,88,300,55), ss(900,62), cd(600,58,36)]),
            5: ("S%02d Sáb — Endurance 90min fácil" % macro_week, "Sábado curto e fácil.", z2(90,62)),
            6: ("S%02d Dom — Genérico 3h endurance ~150 TSS" % macro_week, "Placeholder domingo social/livre.", sunday_150()),
        }

    if macro_week == 12:
        return {
            1: ("S12 Ter — Openers 75min + 2x8 @100%%", "Ativar sem cansar.", [wu(720,45,68), ss(900,62), itv(2,480,100,360,55), ss(900,62), cd(600,58,36)]),
            2: ("S12 Qua — Z2 60min fácil", "Soltar.", z2(60,60)),
            3: ("S12 Qui — Openers 45min", "3x1min a 105%.", [wu(600,45,62), ss(600,60), itv(3,60,105,180,55), ss(600,60), cd(480,55,35)]),
            5: ("S12 Sáb — TESTE FTP 20min 🏁", "Teste final FTP.", [wu(900,45,78), ss(300,95), itv(3,20,115,40,60), ss(300,55), ss(300,115), ss(600,55), ss(1200,100), ss(600,55), cd(600,58,36)]),
            6: ("S12 Dom — Recuperação/social fácil", "Recuperação pós-teste.", z2(90,60)),
        }

    # Build/peak patterns.
    if macro_week <= 3:
        if phase_week == 1:
            tue = ("S%02d Ter — VO2 diesel 4x5 @108%%" % macro_week, "VO2 específico para perfil diesel.", [wu(720,45,75), ss(180,85), ss(180,55), itv(4,300,108,300,55), ss(420,62), cd(480,60,38)])
            thu = ("S%02d Qui — Sweet Spot 3x15 @90%%" % macro_week, "SS controlado.", [wu(720,45,72), ss(240,65), itv(3,900,90,300,55), ss(180,62), cd(480,60,38)])
            sat = ("S%02d Sáb — 2h SS 3x20 @88%%" % macro_week, "Sábado estruturado até 2h.", [wu(720,45,70), ss(600,64), itv(3,1200,88,300,60), ss(780,64), cd(600,58,36)])
        elif phase_week == 2:
            tue = ("S%02d Ter — Threshold 2x20 @96%%" % macro_week, "Sessão-chave de FTP.", [wu(720,45,73), itv(3,45,105,90,60), ss(120,62), ss(1200,96), ss(360,55), ss(1200,96), ss(180,60), cd(480,60,38)])
            thu = ("S%02d Qui — VO2 diesel 5x5 @108%%" % macro_week, "VO2 principal.", [wu(720,45,75), ss(180,85), ss(180,55), itv(5,300,108,300,55), ss(180,62), cd(480,60,38)])
            sat = ("S%02d Sáb — 2h Tempo/SS 2x35 @86%%" % macro_week, "Durabilidade em 2h.", [wu(720,45,68), ss(600,64), ss(2100,86), ss(360,60), ss(2100,86), ss(720,64), cd(600,58,36)])
        else:
            tue = ("S%02d Ter — VO2 diesel 4x6 @107%%" % macro_week, "VO2 longo e aeróbico.", [wu(720,45,75), ss(180,85), ss(180,55), itv(4,360,107,360,55), ss(180,62), cd(480,60,38)])
            thu = ("S%02d Qui — Threshold 1x30 + 1x15 @96%%" % macro_week, "45min threshold.", [wu(720,45,73), itv(3,45,105,90,60), ss(120,62), ss(1800,96), ss(360,55), ss(900,96), ss(180,60), cd(480,60,38)])
            sat = ("S%02d Sáb — 2h Over-Under 3x12" % macro_week, "2min 102% / 2min 92%.", [wu(900,45,70), ss(600,64), itv(3,120,102,120,92), ss(360,58), itv(3,120,102,120,92), ss(360,58), itv(3,120,102,120,92), ss(1200,64), cd(600,58,36)])
    elif macro_week <= 7:
        if phase_week == 1:
            tue = ("S%02d Ter — Threshold 3x15 @98%%" % macro_week, "45min perto do FTP.", [wu(720,45,73), itv(3,45,105,90,60), ss(120,62), itv(3,900,98,300,55), ss(120,60), cd(420,60,38)])
            thu = ("S%02d Qui — VO2 5x5 @110%%" % macro_week, "VO2 forte.", [wu(720,45,75), ss(180,85), ss(180,55), itv(5,300,110,300,55), ss(180,62), cd(480,60,38)])
            sat = ("S%02d Sáb — 2h SS 3x22 @88%%" % macro_week, "66min SS.", [wu(720,45,70), ss(360,64), itv(3,1320,88,240,60), ss(840,64), cd(600,58,36)])
        elif phase_week == 2:
            tue = ("S%02d Ter — VO2 4x6 @108%%" % macro_week, "VO2 longo.", [wu(720,45,75), ss(180,85), ss(180,55), itv(4,360,108,360,55), ss(180,62), cd(480,60,38)])
            thu = ("S%02d Qui — Threshold 2x22 @96-97%%" % macro_week, "44min perto do FTP.", [wu(720,45,73), itv(3,45,105,90,60), ss(120,62), ss(1320,96), ss(360,55), ss(1320,97), ss(120,60), cd(480,60,38)])
            sat = ("S%02d Sáb — 2h Threshold/SS 2x30 @92%%" % macro_week, "Sustained power.", [wu(720,45,70), ss(600,64), ss(1800,92), ss(360,60), ss(1800,92), ss(1320,64), cd(600,58,36)])
        else:
            tue = ("S%02d Ter — VO2 5x5 @112%%" % macro_week, "Pico VO2.", [wu(720,45,75), ss(180,85), ss(180,55), itv(5,300,112,300,55), ss(180,62), cd(480,60,38)])
            thu = ("S%02d Qui — Threshold 2x25 @96-97%%" % macro_week, "50min threshold.", [wu(720,45,73), itv(3,45,105,90,60), ss(120,62), ss(1500,96), ss(360,55), ss(1500,97), ss(180,60), cd(480,60,38)])
            sat = ("S%02d Sáb — 2h SS contínuo 1x60 @88%%" % macro_week, "60min contínuos.", [wu(720,45,70), ss(1200,64), ss(3600,88), ss(1080,64), cd(600,58,36)])
    else:
        if phase_week == 1:
            tue = ("S%02d Ter — Over-Under 3x12" % macro_week, "2min 102% / 2min 92%.", [wu(720,45,73), ss(300,65), itv(3,120,102,120,92), ss(360,55), itv(3,120,102,120,92), ss(360,55), itv(3,120,102,120,92), ss(300,60), cd(600,60,38)])
            thu = ("S%02d Qui — VO2 4x6 @109%%" % macro_week, "VO2 qualidade.", [wu(720,45,75), ss(180,85), ss(180,55), itv(4,360,109,360,55), ss(180,62), cd(480,60,38)])
            sat = ("S%02d Sáb — 2h 30/30 controlado" % macro_week, "3x10x30/30.", [wu(900,45,72), ss(600,65), itv(10,30,120,30,55), ss(360,55), itv(10,30,120,30,55), ss(360,55), itv(10,30,120,30,55), ss(2580,64), cd(600,58,36)])
        elif phase_week == 2:
            tue = ("S%02d Ter — VO2 5x5 @112%%" % macro_week, "VO2 pesado.", [wu(720,45,75), ss(180,85), ss(180,55), itv(5,300,112,300,55), ss(180,62), cd(480,60,38)])
            thu = ("S%02d Qui — Threshold 2x20 + 1x8 @97%%" % macro_week, "48min perto do FTP.", [wu(720,45,73), itv(3,45,105,90,60), ss(120,62), ss(1200,97), ss(300,55), ss(1200,97), ss(300,55), ss(480,97), ss(120,60), cd(480,60,38)])
            sat = ("S%02d Sáb — 2h SS 3x20 @90%%" % macro_week, "60min a 90%.", [wu(720,45,70), ss(600,64), itv(3,1200,90,300,60), ss(780,64), cd(600,58,36)])
        else:
            tue = ("S%02d Ter — Threshold 2x25 @97%%" % macro_week, "50min threshold.", [wu(720,45,73), itv(3,45,105,90,60), ss(120,62), ss(1500,97), ss(360,55), ss(1500,97), ss(180,60), cd(480,60,38)])
            thu = ("S%02d Qui — VO2 4x6 @110%%" % macro_week, "Último VO2 duro.", [wu(720,45,75), ss(180,85), ss(180,55), itv(4,360,110,360,55), ss(180,62), cd(480,60,38)])
            sat = ("S%02d Sáb — 2h 40/20 controlado" % macro_week, "3x8x40/20.", [wu(900,45,72), ss(600,65), itv(8,40,118,20,55), ss(360,55), itv(8,40,118,20,55), ss(360,55), itv(8,40,118,20,55), ss(2940,64), cd(600,58,36)])

    return {
        1: tue,
        2: ("S%02d Qua — Z2 real 90min HR≤128" % macro_week, "Z2 verdadeiro, HR controlada.", z2(90,63)),
        3: thu,
        5: sat,
        6: ("S%02d Dom — Genérico 3h endurance ~150 TSS" % macro_week, "Placeholder domingo social/livre.", sunday_150()),
    }


def recovery_override(macro_week):
    return {
        1: ("AJUSTADO S%02d Ter — Recovery 60min" % macro_week, "Semana ajustada para recuperação.", z2(60,58)),
        2: ("AJUSTADO S%02d Qua — Z2 fácil 75min" % macro_week, "Z2 fácil.", z2(75,60)),
        3: ("AJUSTADO S%02d Qui — Z2 60min + 3x1min" % macro_week, "Ativar sem stress.", [wu(600,45,60), ss(900,60), itv(3,60,95,180,55), ss(780,60), cd(600,55,35)]),
        5: ("AJUSTADO S%02d Sáb — Endurance 90min fácil" % macro_week, "Sem intensidade.", z2(90,60)),
        6: ("AJUSTADO S%02d Dom — Social/endurance 150 TSS" % macro_week, "Domingo social placeholder.", sunday_150()),
    }


def event_text(e):
    return " ".join(str(e.get(k, "")) for k in ("name", "description", "category", "type", "sub_type")).upper()


def is_no_bike_event(e):
    txt = event_text(e)
    keywords = [
        "NO BIKE WEEK", "NO BIKE", "SEM BIKE", "SEM BICICLETA",
        "FERIAS SEM BIKE", "FÉRIAS SEM BIKE", "VIAGEM SEM BIKE",
        "VACATION NO BIKE"
    ]
    return any(k in txt for k in keywords)


def has_no_bike_week(events, start, end):
    for e in events:
        d = parse_item_date(e)
        if d and start <= d <= end and is_no_bike_event(e):
            return True, e
        # Some multi-day holiday events may expose end_date/end_date_local. Handle overlap conservatively.
        sd = None
        ed = None
        for key in ("start_date_local", "start_date", "date", "day"):
            if e.get(key):
                try:
                    sd = dt.date.fromisoformat(str(e.get(key))[:10]); break
                except Exception:
                    pass
        for key in ("end_date_local", "end_date"):
            if e.get(key):
                try:
                    ed = dt.date.fromisoformat(str(e.get(key))[:10]); break
                except Exception:
                    pass
        if sd and ed and not (ed < start or sd > end) and is_no_bike_event(e):
            return True, e
    return False, None


def reentry_week(macro_week):
    return {
        1: ("REENTRY S%02d Ter — Z2 75min + openers" % macro_week, "Regresso pós NO BIKE WEEK. Sem compensar carga perdida.", [wu(600,45,62), ss(1200,62), itv(3,60,95,180,55), ss(900,62), cd(600,55,35)]),
        2: ("REENTRY S%02d Qua — Z2 real 90min HR≤128" % macro_week, "Z2 verdadeiro para voltar ao ritmo.", z2(90,62)),
        3: ("REENTRY S%02d Qui — Sweet Spot curto 2x10 @88%%" % macro_week, "Toque controlado; se RPE alto, transformar em Z2.", [wu(720,45,68), ss(300,62), itv(2,600,88,300,55), ss(900,62), cd(600,58,36)]),
        5: ("REENTRY S%02d Sáb — Endurance 90min fácil" % macro_week, "Sábado conservador pós-férias.", z2(90,62)),
        6: ("REENTRY S%02d Dom — Social/endurance controlado" % macro_week, "Domingo livre, mas evitar pancadaria se a semana de regresso pesar.", sunday_150()),
    }

def summarize_prior_week(events, activities, week_start):
    start = week_start - dt.timedelta(days=7)
    end = week_start - dt.timedelta(days=1)
    sunday = end

    planned = [e for e in events if parse_item_date(e) and start <= parse_item_date(e) <= end]
    planned_source = "calendar_current"
    done = [
        a for a in activities
        if parse_item_date(a)
        and start <= parse_item_date(a) <= end
        and ((metric_hours(a) or 0) > 0.15 or (metric_load(a) or 0) > 5)
    ]

    p_load = sum((metric_load(e) or 0) for e in planned)
    d_load = sum((metric_load(a) or 0) for a in done)
    p_h = sum((metric_hours(e) or 0) for e in planned)
    d_h = sum((metric_hours(a) or 0) for a in done)

    sunday_planned = [e for e in planned if parse_item_date(e) == sunday]
    sunday_done = [a for a in done if parse_item_date(a) == sunday]
    sunday_planned_load = sum((metric_load(e) or 0) for e in sunday_planned)
    sunday_done_load = sum((metric_load(a) or 0) for a in sunday_done)
    sunday_done_hours = sum((metric_hours(a) or 0) for a in sunday_done)

    # Load excluding Sunday is more useful for judging weekday/saturday compliance.
    p_load_ex_sun = p_load - sunday_planned_load
    d_load_ex_sun = d_load - sunday_done_load

    load_ratio = (d_load / p_load) if p_load > 0 else None
    load_diff = d_load - p_load

    if p_load > 50 and d_load > p_load * 1.40:
        status = "MUITO ACIMA DO PLANEADO"
    elif p_load > 50 and d_load > p_load * 1.25:
        status = "ACIMA DO PLANEADO"
    elif p_load > 50 and d_load > p_load * 1.15:
        status = "CUMPRIDA, MAS ACIMA DO PLANEADO"
    elif p_load > 50 and d_load >= p_load * 0.85:
        status = "CUMPRIDA"
    elif p_load > 50 and d_load >= p_load * 0.55:
        status = "PARCIAL"
    elif p_load > 50:
        status = "ABAIXO DO PLANEADO"
    elif d_load > 50:
        status = "EXTRA / SEM PLANO"
    else:
        status = "SEMANA LEVE / SEM PLANO"

    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "status": status,
        "planned_load": p_load,
        "done_load": d_load,
        "load_diff": load_diff,
        "load_ratio": load_ratio,
        "planned_hours": p_h,
        "done_hours": d_h,
        "planned_count": len(planned),
        "done_count": len(done),
        "planned_source": planned_source,

        "sunday_date": sunday.isoformat(),
        "sunday_planned_load": sunday_planned_load,
        "sunday_done_load": sunday_done_load,
        "sunday_done_hours": sunday_done_hours,
        "sunday_delta_load": sunday_done_load - sunday_planned_load,

        "planned_load_ex_sunday": p_load_ex_sun,
        "done_load_ex_sunday": d_load_ex_sun,
    }


def decide_adjustment(macro_week, prior, latest_w):
    """
    Decide o ajuste semanal como um treinador, não como uma folha Excel.

    Regras principais:
    - Domingo social acima do previsto NÃO força recovery week sozinho.
    - Recovery week só aparece se houver sinais fortes combinados:
      carga muito acima + wellness/form maus, ou semana macro de recuperação.
    - Se domingo foi muito pesado mas wellness está ok, mantém estrutura e deixa o daily agent
      decidir terça com dados frescos.
    """
    reasons = []

    if macro_week in (4, 8, 12):
        return "recovery", [f"Semana {macro_week} é semana macro de recuperação/taper."]

    planned = prior["planned_load"]
    done = prior["done_load"]
    ratio = done / planned if planned > 50 else None

    sunday_planned = prior.get("sunday_planned_load", 0) or 0
    sunday_done = prior.get("sunday_done_load", 0) or 0
    sunday_delta = prior.get("sunday_delta_load", 0) or 0

    planned_ex_sun = prior.get("planned_load_ex_sunday", planned) or 0
    done_ex_sun = prior.get("done_load_ex_sunday", done) or 0
    ratio_ex_sun = done_ex_sun / planned_ex_sun if planned_ex_sun > 50 else None

    fm = form(latest_w) if latest_w else None
    sh = sleep_h(latest_w) if latest_w else None
    latest_hrv = hrv(latest_w) if latest_w else None
    latest_rhr = rhr(latest_w) if latest_w else None

    sunday_big = sunday_planned > 0 and sunday_done >= sunday_planned + 70
    sunday_very_big = sunday_planned > 0 and sunday_done >= sunday_planned + 120

    wellness_bad = False
    wellness_very_bad = False

    if fm is not None and fm < -18:
        wellness_bad = True
        reasons.append(f"Form moderadamente baixa: {fmt(fm,0)}.")
    if fm is not None and fm < -28:
        wellness_very_bad = True
        reasons.append(f"Form muito baixa: {fmt(fm,0)}.")

    if sh is not None and sh < 6:
        wellness_bad = True
        reasons.append(f"Sono recente baixo: {fmt_h(sh)}.")
    if sh is not None and sh < 5.3:
        wellness_very_bad = True
        reasons.append(f"Sono recente muito baixo: {fmt_h(sh)}.")

    # HRV/RHR absolute values are less useful without baseline here, so they are informational only.
    if latest_hrv is not None:
        reasons.append(f"HRV mais recente disponível: {fmt(latest_hrv)}.")
    if latest_rhr is not None:
        reasons.append(f"RHR mais recente disponível: {fmt(latest_rhr,0)} bpm.")

    if sunday_big:
        reasons.append(
            f"Domingo social acima do previsto: {fmt(sunday_done,0)} vs {fmt(sunday_planned,0)} TSS. "
            "Isto é sinal de atenção, não motivo automático para semana de recuperação."
        )

    if ratio_ex_sun is not None and ratio_ex_sun > 1.20:
        reasons.append(
            f"Carga sem contar domingo também ficou alta: {fmt(done_ex_sun,0)} vs {fmt(planned_ex_sun,0)} TSS."
        )

    # True recovery week: only if macro says so, or if high load combines with bad wellness.
    if sunday_very_big and wellness_very_bad:
        return "recovery", reasons + ["Domingo muito acima do previsto combinado com sinais fortes de fadiga."]
    if ratio is not None and ratio > 1.40 and wellness_very_bad:
        return "recovery", reasons + ["Semana muito acima do planeado combinada com wellness muito mau."]
    if ratio_ex_sun is not None and ratio_ex_sun > 1.35 and wellness_bad:
        return "recovery", reasons + ["A semana foi pesada mesmo excluindo domingo e há sinais de fadiga."]

    # Reduced week: useful if weekday/saturday load was also high, or if wellness is bad.
    if ratio_ex_sun is not None and ratio_ex_sun > 1.20:
        return "reduced", reasons + ["Redução moderada: a carga extra não veio só do domingo."]
    if sunday_very_big and wellness_bad:
        return "reduced", reasons + ["Domingo muito pesado e alguns sinais de fadiga: reduzir ligeiramente a semana."]
    if fm is not None and fm < -18:
        return "reduced", reasons + ["Form baixa: reduzir ligeiramente e deixar o daily agent decidir o dia."]
    if sh is not None and sh < 6:
        return "reduced", reasons + ["Sono recente baixo: reduzir ligeiramente e reavaliar diariamente."]

    # If Sunday was big but body is responding well, keep week normal.
    if sunday_big:
        return "normal", reasons + [
            "Como não há sinais fortes de fadiga, mantém-se a estrutura da semana. "
            "O daily agent ajustará terça se o HRV/sono/RHR piorarem."
        ]

    if ratio is not None and ratio > 1.25:
        return "normal", reasons + [
            "Semana acima do planeado, mas sem sinais suficientes para reduzir a semana inteira. "
            "Monitorizar diariamente."
        ]

    return "normal", reasons or ["Semana anterior e wellness permitem progressão normal."]


def build_events(week_start, macro_week, adjustment, plan_id):
    if adjustment == "no_bike":
        return []
    lib = recovery_override(macro_week) if adjustment == "recovery" else (reentry_week(macro_week) if adjustment == "reentry" else base_week(macro_week))
    dates = {1: week_start+dt.timedelta(days=1), 2: week_start+dt.timedelta(days=2), 3: week_start+dt.timedelta(days=3), 5: week_start+dt.timedelta(days=5), 6: week_start+dt.timedelta(days=6)}
    times = {1: dt.time(11,30), 2: dt.time(11,30), 3: dt.time(11,30), 5: dt.time(8,0), 6: dt.time(8,0)}
    events = []
    for d in [1,2,3,5,6]:
        name, desc, steps = lib[d]
        if adjustment == "reduced" and d in (1,3,5):
            name = "AJUSTADO — " + name
            desc += "\n\nAjuste semanal: carga/intensidade reduzida por sinais da semana anterior."
            steps = scale_hard(steps, -3)
        dur = duration_min(steps)
        tss = est_load_steps(steps)
        start_dt = dt.datetime.combine(dates[d], times[d])
        filename = safe_filename(name)
        events.append({
            "category": "WORKOUT",
            "type": "Ride",
            "start_date_local": start_dt.isoformat(timespec="seconds"),
            "end_date_local": (start_dt + dt.timedelta(minutes=dur)).isoformat(timespec="seconds"),
            "name": name,
            "description": desc + f"\n\nPlano semanal rolling. Macro week: {macro_week}. Ajuste semanal: {adjustment}.",
            "moving_time": dur*60,
            "load": tss,
            "icu_training_load": tss,
            "external_id": f"{plan_id}-w{macro_week:02d}-d{d}",
            "filename": filename,
            "file_contents_base64": base64.b64encode(zwo(name, steps).encode("utf-8")).decode("ascii"),
        })
    return events


def smtp_configured():
    return all(os.getenv(k, "").strip() for k in ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "TO_EMAIL"])


def send_email(subject, body, attachments=None):
    if not smtp_configured():
        return False, "SMTP não configurado; e-mail não enviado."
    host = os.getenv("SMTP_HOST").strip()
    port = int(os.getenv("SMTP_PORT", "587").strip())
    user = os.getenv("SMTP_USER").strip()
    pwd = os.getenv("SMTP_PASSWORD").strip()
    to_email = os.getenv("TO_EMAIL").strip()
    from_email = os.getenv("FROM_EMAIL", user).strip() or user
    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    for p in attachments or []:
        path = Path(p)
        if path.exists():
            msg.add_attachment(path.read_bytes(), maintype="application", subtype="octet-stream", filename=path.name)
    with smtplib.SMTP(host, port, timeout=45) as smtp:
        smtp.starttls()
        smtp.login(user, pwd)
        smtp.send_message(msg)
    return True, f"E-mail enviado para {to_email}."


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-week-start", default=None)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--email", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    key = os.getenv("INTERVALS_API_KEY", "").strip()
    athlete_id = os.getenv("ATHLETE_ID", "0").strip() or "0"
    plan_start = dt.date.fromisoformat(os.getenv("PLAN_START_DATE", DEFAULT_PLAN_START_DATE).strip() or DEFAULT_PLAN_START_DATE)
    plan_id = os.getenv("PLAN_ID", DEFAULT_PLAN_ID).strip() or DEFAULT_PLAN_ID
    weekly_auto = bool_env("WEEKLY_AUTO_APPLY", False)
    if not key:
        raise RuntimeError("Falta INTERVALS_API_KEY.")

    today_pt = dt.datetime.now(ZoneInfo(TIMEZONE)).date()

    if args.target_week_start:
        week_start = monday_of(dt.date.fromisoformat(args.target_week_start))
    else:
        week_start = monday_of(today_pt)

    macro_week = ((week_start - plan_start).days // 7) + 1
    pre_plan = week_start < plan_start

    client = IntervalsClient(athlete_id, key)
    athlete = client.athlete()
    if athlete_id == "0" and athlete.get("id"):
        client.athlete_id = athlete["id"]

    history_start = week_start - dt.timedelta(days=21)
    history_end = week_start + dt.timedelta(days=6)
    wellness = client.wellness_range(history_start, history_end)
    activities = client.activities_range(history_start, history_end)
    events = client.events_range(week_start - dt.timedelta(days=7), week_start + dt.timedelta(days=6))

    by_day = {}
    for w in wellness:
        d = parse_item_date(w)
        if d:
            by_day[d] = w
    # Only use real wellness up to the workflow run date.
    # Intervals can return projected/future wellness rows for fitness/form,
    # but sleep/HRV/RHR are not real for future dates and should not drive weekly planning.
    real_wellness_days = [d for d in by_day.keys() if d <= today_pt]
    latest_day = max(real_wellness_days) if real_wellness_days else None
    latest_w = by_day.get(latest_day, {}) if latest_day else {}

    no_bike_current, no_bike_event = has_no_bike_week(events, week_start, week_start + dt.timedelta(days=6))
    no_bike_previous, previous_no_bike_event = has_no_bike_week(events, week_start - dt.timedelta(days=7), week_start - dt.timedelta(days=1))

    prior = summarize_prior_week(events, activities, week_start)
    if pre_plan:
        adjustment = "pre_plan_observation"
        reasons = [
            f"Semana anterior ao PLAN_START_DATE ({plan_start.isoformat()}).",
            "Plano principal ainda é FasCat/observação; não gerar treinos do plano Coach Nuno antes do arranque.",
            "Usar este relatório apenas para analisar carga realizada, wellness e tendência."
        ]
        week_events = []
    elif no_bike_current:
        adjustment = "no_bike"
        reasons = ["NO BIKE WEEK detetada no Intervals. Não criar treinos de bicicleta; não compensar carga perdida."]
        week_events = build_events(week_start, macro_week, adjustment, plan_id)
    elif no_bike_previous:
        adjustment = "reentry"
        reasons = ["Semana anterior marcada como NO BIKE WEEK. Criar semana de reentrada progressiva, sem VO2 pesado logo de início."]
        week_events = build_events(week_start, macro_week, adjustment, plan_id)
    else:
        adjustment, reasons = decide_adjustment(macro_week, prior, latest_w)
        week_events = build_events(week_start, macro_week, adjustment, plan_id)

    total_load = sum(e["load"] for e in week_events)
    total_hours = sum(e["moving_time"] for e in week_events) / 3600

    allow_apply = (args.apply or (args.auto and weekly_auto)) and not args.dry_run
    applied = False
    apply_msg = "Não aplicado."
    if allow_apply:
        if pre_plan:
            apply_msg = "PRÉ-PLANO: nada aplicado antes do PLAN_START_DATE."
        elif week_events:
            client.upload_bulk_events(week_events)
            applied = True
            apply_msg = f"{len(week_events)} treinos criados/atualizados no Intervals."
        else:
            apply_msg = "NO BIKE WEEK: não há treinos de bicicleta para criar/atualizar."
    elif args.dry_run:
        apply_msg = "Dry-run ativo; nada aplicado."
    elif args.auto and not weekly_auto:
        apply_msg = "WEEKLY_AUTO_APPLY=false; nada aplicado."

    lines = []
    lines.append("="*72)
    lines.append(f"WEEKLY PLANNER AGENT — Semana {macro_week} — {week_start.isoformat()}")
    lines.append("="*72)
    lines.append(f"Atleta: {athlete.get('name') or athlete.get('id') or 'n/d'}")
    lines.append(f"Ajuste semanal: {adjustment}")
    if adjustment == "pre_plan_observation":
        lines.append("Modo especial: PRÉ-PLANO / FasCat em observação.")
    elif adjustment == "no_bike":
        lines.append("Modo especial: NO BIKE WEEK / férias sem bicicleta.")
    elif adjustment == "reentry":
        lines.append("Modo especial: reentrada progressiva após NO BIKE WEEK.")
    if macro_week <= 0:
        lines.append(f"Nota: esta é uma semana anterior ao PLAN_START_DATE ({plan_start.isoformat()}). A semana 1 começa em {plan_start.isoformat()}.")
    lines.append("")
    lines.append("SEMANA ANTERIOR")
    lines.append(f"Estado: {prior['status']}")
    lines.append(f"Planeado: {fmt(prior['planned_load'],0)} TSS | {fmt_h(prior['planned_hours'])}")
    lines.append(f"Realizado: {fmt(prior['done_load'],0)} TSS | {fmt_h(prior['done_hours'])}")
    if prior.get("planned_load") and prior.get("planned_load") > 50 and prior.get("load_ratio") is not None:
        diff = prior.get("load_diff") or 0
        ratio_pct = (prior.get("load_ratio") - 1) * 100
        sign = "+" if diff >= 0 else ""
        lines.append(f"Desvio: {sign}{fmt(diff,0)} TSS | {sign}{fmt(ratio_pct,0)}% vs planeado")
    lines.append(f"Domingo: planeado {fmt(prior.get('sunday_planned_load'),0)} TSS / realizado {fmt(prior.get('sunday_done_load'),0)} TSS | {fmt_h(prior.get('sunday_done_hours'))}")
    lines.append(f"Sem domingo: planeado {fmt(prior.get('planned_load_ex_sunday'),0)} TSS / realizado {fmt(prior.get('done_load_ex_sunday'),0)} TSS")
    lines.append("Fonte planeado: calendário atual do Intervals.")
    lines.append("")
    lines.append("ÚLTIMO WELLNESS")
    lines.append(f"Data: {latest_day.isoformat() if latest_day else 'n/d'}")
    lines.append(f"Sono: {fmt_h(sleep_h(latest_w))} | HRV: {fmt(hrv(latest_w))} | RHR: {fmt(rhr(latest_w),0)} bpm | Form: {fmt(form(latest_w),0)}")
    lines.append("")
    lines.append("MOTIVOS DO AJUSTE")
    lines += [f"- {r}" for r in reasons]
    lines.append("")
    lines.append("PLANO DA SEMANA")
    if adjustment == "pre_plan_observation":
        lines.append("- Pré-plano: não gerar proposta semanal do Coach Nuno antes do PLAN_START_DATE.")
        lines.append("- Mantém FasCat como plano principal e usa o Daily Coach para validar o dia.")
        lines.append("- O Weekly serve apenas para observar carga/wellness até ao arranque do plano em " + plan_start.isoformat() + ".")
    else:
        lines.append(f"Total estimado: {fmt(total_load,0)} TSS | {fmt_h(total_hours)}")
        if not week_events and adjustment == "no_bike":
            lines.append("- Sem treinos de ciclismo criados esta semana.")
            lines.append("- Manutenção sugerida: caminhadas, mobilidade e core leve 2-3x, sem tentar simular VO2/threshold fora da bicicleta.")
            lines.append("- Regresso: semana seguinte deve ser progressiva, sem compensar carga perdida.")
        for e in week_events:
            lines.append(f"- {e['start_date_local'][:10]} {e['name']} | {fmt(e['load'],0)} TSS | {fmt_h(e['moving_time']/3600)}")
    lines.append("")
    lines.append("INTERVALS")
    lines.append(f"- {apply_msg}")
    lines.append("")
    lines.append("Nota: o daily agent continua a ajustar cada dia às 08:20 conforme sono/HRV/fadiga.")
    report = "\n".join(lines)

    json_payload = {
        "week_start": week_start.isoformat(),
        "macro_week": macro_week,
        "pre_plan": pre_plan,
        "plan_start": plan_start.isoformat(),
        "adjustment": adjustment,
        "reasons": reasons,
        "prior_week": prior,
        "latest_wellness_date": latest_day.isoformat() if latest_day else None,
        "latest_wellness": latest_w,
        "planned_events": [{k:v for k,v in e.items() if k != "file_contents_base64"} for e in week_events],
        "applied": applied,
        "apply_msg": apply_msg,
    }
    Path("weekly_planner_report.txt").write_text(report, encoding="utf-8")
    Path("weekly_planner_report.json").write_text(json.dumps(json_payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    Path("weekly_planner_payload.json").write_text(json.dumps([{k:v for k,v in e.items() if k != "file_contents_base64"} for e in week_events], indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    if args.debug:
        Path("weekly_debug_raw.json").write_text(json.dumps({"wellness": wellness, "activities": activities[:80], "events": events}, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    if args.email:
        ok, msg = send_email(f"Weekly Planner — Semana {macro_week} — {adjustment} — {week_start.isoformat()}", report, ["weekly_planner_report.json"])
        report += "\nEMAIL\n"
        report += f"- {msg}\n"
        Path("weekly_planner_report.txt").write_text(report, encoding="utf-8")

    print(report)
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("## Weekly Planner Agent\n\n```text\n")
            f.write(report)
            f.write("\n```\n")


if __name__ == "__main__":
    main()
