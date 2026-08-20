import { Preferences } from '@capacitor/preferences';

const KEY_BASE_URL = 'daily_coach_base_url';
const KEY_TOKEN = 'daily_coach_app_token';

/**
 * Settings are stored on-device via Capacitor Preferences, never hardcoded.
 * Preferences is plain local storage (not hardware-backed secure storage) -
 * fine for a personal single-user app, but don't reuse this pattern if this
 * app is ever shared with other people.
 */
export async function getSettings() {
  const [baseUrl, token] = await Promise.all([
    Preferences.get({ key: KEY_BASE_URL }),
    Preferences.get({ key: KEY_TOKEN }),
  ]);
  return { baseUrl: baseUrl.value || '', token: token.value || '' };
}

export async function saveSettings({ baseUrl, token }) {
  await Promise.all([
    Preferences.set({ key: KEY_BASE_URL, value: baseUrl || '' }),
    Preferences.set({ key: KEY_TOKEN, value: token || '' }),
  ]);
}

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, { method = 'GET', body } = {}) {
  const { baseUrl, token } = await getSettings();
  if (!baseUrl) throw new ApiError('Backend URL não configurado. Vai a Settings.', 0);
  if (!token) throw new ApiError('Token não configurado. Vai a Settings.', 0);

  const res = await fetch(`${baseUrl.replace(/\/$/, '')}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 || res.status === 403) {
    throw new ApiError('Token inválido ou expirado.', res.status);
  }
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new ApiError(`Erro do servidor (${res.status}): ${text.slice(0, 200)}`, res.status);
  }
  return res.json();
}

export function getTodayReport() {
  return request('/api/v1/reports/today');
}

export function getApplyPreview() {
  return request('/api/v1/reports/today/apply/preview');
}

export function applyToday() {
  return request('/api/v1/reports/today/apply', { method: 'POST' });
}

export function getReportByDate(date) {
  return request(`/api/v1/reports/${date}`);
}

export function listReports() {
  return request('/api/v1/reports');
}

export function sendFeedback(feedbackType, note) {
  return request('/api/v1/feedback', {
    method: 'POST',
    body: { type: feedbackType, note: note || null },
  });
}

export async function healthCheck(baseUrl) {
  if (!baseUrl) return { ok: false, detail: 'URL vazio.' };
  const url = `${baseUrl.replace(/\/$/, '')}/health`;
  try {
    const res = await fetch(url);
    if (!res.ok) {
      return { ok: false, detail: `Servidor respondeu HTTP ${res.status} em ${url}` };
    }
    return { ok: true, detail: null };
  } catch (e) {
    // This is the branch that was showing as a generic "não foi possível
    // ligar" before - now we surface the real browser/network error text
    // (e.g. "Failed to fetch", a TLS error, a DNS error, etc.)
    return { ok: false, detail: `${e?.message || e} (URL testada: ${url})` };
  }
}

export { ApiError };
