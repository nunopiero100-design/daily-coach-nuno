import { useEffect, useState } from 'react';
import { getSettings, saveSettings, healthCheck } from '../api/client';

export default function SettingsScreen({ useMock, setUseMock }) {
  const [baseUrl, setBaseUrl] = useState('');
  const [token, setToken] = useState('');
  const [status, setStatus] = useState(null);

  useEffect(() => {
    getSettings().then((s) => {
      setBaseUrl(s.baseUrl);
      setToken(s.token);
    });
  }, []);

  async function handleSave() {
    await saveSettings({ baseUrl, token });
    setStatus('saved');
  }

  async function handleTest() {
    setStatus('testing');
    try {
      const ok = baseUrl && (await healthCheck(baseUrl));
      setStatus(ok ? 'ok' : 'fail');
    } catch {
      setStatus('fail');
    }
  }

  return (
    <div>
      <div className="card">
        <div className="sub" style={{ marginBottom: 10 }}>LIGAÇÃO AO BACKEND</div>
        <label>URL do backend (Render)</label>
        <input
          type="text"
          placeholder="https://daily-coach-api.onrender.com"
          value={baseUrl}
          onChange={(e) => setBaseUrl(e.target.value)}
          autoCapitalize="none"
        />
        <label>APP_TOKEN</label>
        <input
          type="password"
          placeholder="Bearer token"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          autoCapitalize="none"
        />
        <button className="primary-btn" onClick={handleSave}>Guardar</button>
        <div style={{ height: 8 }} />
        <button className="icon-btn" style={{ width: '100%' }} onClick={handleTest}>
          Testar ligação (/health)
        </button>
        {status === 'saved' && <div className="sub" style={{ color: 'var(--green)', marginTop: 8 }}>Guardado.</div>}
        {status === 'testing' && <div className="sub" style={{ marginTop: 8 }}>A testar…</div>}
        {status === 'ok' && <div className="sub" style={{ color: 'var(--green)', marginTop: 8 }}>Backend acessível ✓</div>}
        {status === 'fail' && <div className="sub" style={{ color: 'var(--red)', marginTop: 8 }}>Não foi possível ligar.</div>}
      </div>

      <div className="card">
        <div className="sub" style={{ marginBottom: 10 }}>MODO DE DESENVOLVIMENTO</div>
        <div className="kv">
          <span className="k">Usar dados mock (offline)</span>
          <input type="checkbox" checked={useMock} onChange={(e) => setUseMock(e.target.checked)} />
        </div>
        <div className="sub" style={{ marginTop: 6 }}>
          Enquanto o backend não tiver o "ingest" a ligar o GitHub Actions ao Render, usa mock para testar o ecrã.
        </div>
      </div>
    </div>
  );
}
