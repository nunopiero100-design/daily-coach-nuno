import { useEffect, useState } from 'react';
import { getSettings, saveSettings, healthCheck } from '../api/client';
import { IconSettingsGear } from '../components/Icons';

export default function SettingsScreen() {
  const [baseUrl, setBaseUrl] = useState('');
  const [token, setToken] = useState('');
  const [status, setStatus] = useState(null);
  const [testDetail, setTestDetail] = useState(null);

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
    setTestDetail(null);
    const result = await healthCheck(baseUrl);
    setStatus(result.ok ? 'ok' : 'fail');
    setTestDetail(result.detail);
  }

  return (
    <div>
      <div className="card">
        <div className="section-label" style={{ margin: '0 0 10px' }}><IconSettingsGear size={13} />LIGAÇÃO AO BACKEND</div>
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
        {status === 'fail' && (
          <div className="sub" style={{ color: 'var(--red)', marginTop: 8 }}>
            Não foi possível ligar.
            {testDetail && <div style={{ marginTop: 4, fontSize: 12, wordBreak: 'break-all' }}>{testDetail}</div>}
          </div>
        )}
      </div>
    </div>
  );
}
