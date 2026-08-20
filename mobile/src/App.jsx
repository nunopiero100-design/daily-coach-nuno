import { useState, useEffect, useCallback } from 'react';
import TodayScreen from './screens/TodayScreen';
import GymScreen from './screens/GymScreen';
import HistoryScreen from './screens/HistoryScreen';
import SettingsScreen from './screens/SettingsScreen';
import { getTodayReport, ApiError } from './api/client';
import mockReport from './mock/todayReport.json';

export default function App() {
  const [tab, setTab] = useState('today');
  const [useMock, setUseMock] = useState(true); // starts in mock mode until the ingest bridge exists

  // Today's report is fetched once here and shared by Today + Gym, so the
  // Gym tab can react to readiness too without a second network call.
  const [report, setReport] = useState(null);
  const [reportLoading, setReportLoading] = useState(true);
  const [reportError, setReportError] = useState(null);

  const loadReport = useCallback(async () => {
    setReportLoading(true);
    setReportError(null);
    try {
      if (useMock) {
        setReport(mockReport);
      } else {
        const data = await getTodayReport();
        setReport(data);
      }
    } catch (e) {
      setReportError(e instanceof ApiError ? e.message : 'Erro a carregar o relatório.');
    } finally {
      setReportLoading(false);
    }
  }, [useMock]);

  useEffect(() => { loadReport(); }, [loadReport]);

  return (
    <div className="app">
      <div className="topbar">
        <div className="brand">DAILY<span className="dot">·</span>COACH</div>
        {useMock && <span className="status-badge INCOMPLETE">MOCK</span>}
      </div>

      <div className="content">
        {tab === 'today' && (
          <TodayScreen
            useMock={useMock}
            report={report}
            loading={reportLoading}
            error={reportError}
            reload={loadReport}
          />
        )}
        {tab === 'gym' && <GymScreen report={report} />}
        {tab === 'history' && <HistoryScreen useMock={useMock} />}
        {tab === 'settings' && <SettingsScreen useMock={useMock} setUseMock={setUseMock} />}
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
