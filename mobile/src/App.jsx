import { useState } from 'react';
import TodayScreen from './screens/TodayScreen';
import GymScreen from './screens/GymScreen';
import SettingsScreen from './screens/SettingsScreen';

export default function App() {
  const [tab, setTab] = useState('today');
  const [useMock, setUseMock] = useState(true); // starts in mock mode until the ingest bridge exists

  return (
    <div className="app">
      <div className="topbar">
        <div className="brand">DAILY<span className="dot">·</span>COACH</div>
        {useMock && <span className="status-badge INCOMPLETE">MOCK</span>}
      </div>

      <div className="content">
        {tab === 'today' && <TodayScreen useMock={useMock} />}
        {tab === 'gym' && <GymScreen />}
        {tab === 'settings' && <SettingsScreen useMock={useMock} setUseMock={setUseMock} />}
      </div>

      <div className="tabbar">
        <div className={`tab ${tab === 'today' ? 'on' : ''}`} onClick={() => setTab('today')}>Hoje</div>
        <div className={`tab ${tab === 'gym' ? 'on' : ''}`} onClick={() => setTab('gym')}>Gym</div>
        <div className={`tab ${tab === 'settings' ? 'on' : ''}`} onClick={() => setTab('settings')}>Settings</div>
      </div>
    </div>
  );
}
