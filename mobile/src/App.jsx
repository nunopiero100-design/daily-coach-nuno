import { useState, useEffect, useCallback } from 'react';
import TodayScreen from './screens/TodayScreen';
import GymScreen from './screens/GymScreen';
import HistoryScreen from './screens/HistoryScreen';
import SettingsScreen from './screens/SettingsScreen';
import { getTodayReport, runNow, ApiError } from './api/client';

export default function App() {
  const [tab, setTab] = useState('today');

  // Today's report is fetched once here and shared by Today + Gym, so the
  // Gym tab can react to readiness too without a second network call.
  const [report, setReport] = useState(null);
  const [reportLoading, setReportLoading] = useState(true);
  const [reportError, setReportError] = useState(null);

  const loadReport = useCallback(async () => {
    setReportLoading(true);
    setReportError(null);
    try {
      const data = await getTodayReport();
      setReport(data);
    } catch (e) {
      setReportError(e instanceof ApiError ? e.message : 'Erro a carregar o relatório.');
    } finally {
      setReportLoading(false);
    }
  }, []);

  useEffect(() => { loadReport(); }, [loadReport]);

  // Reload = trigger a fresh Daily Coach run on GitHub Actions (pulls latest
  // Intervals.icu/wellness data, not just re-reads what's already stored).
  // The result lands a bit later via the same ingest path as every morning,
  // so this doesn't refresh `report` immediately - it just kicks off the run.
  const [runState, setRunState] = useState('idle'); // idle | running | done | error
  const [runMessage, setRunMessage] = useState(null);

  async function handleRunNow() {
    setRunState('running');
    setRunMessage(null);
    try {
      const res = await runNow();
      setRunState('done');
      setRunMessage(res.message);
    } catch (e) {
      setRunState('error');
      setRunMessage(e instanceof ApiError ? e.message : 'Não foi possível pedir a atualização.');
    }
  }

  return (
    <div className="app">
      <div className="topbar">
        <div className="brand">DAILY<span className="dot">·</span>COACH</div>
        <button
          className="icon-btn"
          onClick={handleRunNow}
          disabled={runState === 'running'}
          title="Pedir uma atualização a partir do Intervals.icu"
        >
          {runState === 'running' ? '…' : '⟳ Atualizar'}
        </button>
      </div>

      {runMessage && (
        <div
          className="card"
          style={{
            margin: '0 16px 10px',
            borderLeft: `4px solid ${runState === 'error' ? 'var(--red)' : 'var(--lime)'}`,
          }}
        >
          <div className="sub" style={{ color: runState === 'error' ? 'var(--red)' : 'var(--text)' }}>
            {runMessage}
          </div>
          {runState === 'done' && (
            <button className="icon-btn" style={{ marginTop: 8 }} onClick={loadReport}>
              Verificar agora
            </button>
          )}
        </div>
      )}

      <div className="content">
        {tab === 'today' && (
          <TodayScreen
            report={report}
            loading={reportLoading}
            error={reportError}
            reload={loadReport}
          />
        )}
        {tab === 'gym' && <GymScreen report={report} />}
        {tab === 'history' && <HistoryScreen />}
        {tab === 'settings' && <SettingsScreen />}
      </div>

      <div className="tabbar">
        <div className={`tab ${tab === 'today' ? 'on' : ''}`} onClick={() => setTab('today')}>Hoje</div>
        <div className={`tab ${tab === 'gym' ? 'on' : ''}`} onClick={() => setTab('gym')}>Gym</div>
        <div className={`tab ${tab === 'history' ? 'on' : ''}`} onClick={() => setTab('history')}>Histórico</div>
        <div className={`tab ${tab === 'settings' ? 'on' : ''}`} onClick={() => setTab('settings')}>Settings</div>
      </div>
    </div>
  );
}
