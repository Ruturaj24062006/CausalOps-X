import React from 'react';
import { BrowserRouter, Routes, Route, NavLink, Outlet } from 'react-router-dom';
import { Activity, Radio, AlertTriangle, GitBranch, ShieldAlert, Cpu, Settings, User } from 'lucide-react';
import { DataProvider, useData } from './DataContext';

function Layout() {
  const { status, lastUpdated } = useData();

  return (
    <>
      <div className="sidebar">
        <div className="sidebar-header">
          <Cpu className="text-cyan-400" size={24} color="#00d2ff" />
          <span>CAUSALOPS X</span>
        </div>
        <div className="nav-section">
          <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} end>
            <Activity size={18} /> Overview
          </NavLink>
          <NavLink to="/service-graph" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <GitBranch size={18} /> Service Graph
          </NavLink>
          <NavLink to="/live-telemetry" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Radio size={18} /> Live Telemetry
          </NavLink>
          <NavLink to="/anomaly-detection" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <AlertTriangle size={18} /> Anomaly Detection
          </NavLink>
          <NavLink to="/root-cause" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <GitBranch size={18} /> Root Cause Analysis
          </NavLink>
          <NavLink to="/incidents" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <ShieldAlert size={18} /> Incidents
          </NavLink>
        </div>
        <div className="sidebar-footer flex-col gap-2">
          <div className="flex items-center gap-2 text-small text-muted">
            <Radio size={14} color={
              status?.pipeline === 'ready' || status?.pipeline === 'warming_up' || status?.pipeline === 'ACTIVE'
                ? '#37d67a' : '#ff4b4b'
            } />
            System: {status?.pipeline?.toUpperCase() || 'CONNECTING...'}
          </div>
          <NavLink to="/settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} style={{ padding: '10px 0', margin: '0 -20px' }}>
            <Settings size={18} /> Settings
          </NavLink>
          <NavLink to="/profile" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} style={{ padding: '10px 0', margin: '0 -20px' }}>
            <User size={18} /> Profile
          </NavLink>
        </div>
      </div>
      <div className="main-wrapper">
        <div className="topbar">
          <div>
            <div className="title" style={{ margin: 0 }}>Operations Console</div>
            <div className="text-small text-muted">Detect anomalies → Diagnose root cause → Take action</div>
          </div>
          <div className="flex items-center gap-4 text-small">
            Last Updated: {lastUpdated}
          </div>
        </div>
        <div className="content-area">
          <Outlet />
        </div>
      </div>
    </>
  );
}

const Overview = React.lazy(() => import('./pages/Overview'));
const LiveTelemetry = React.lazy(() => import('./pages/LiveTelemetry'));
const AnomalyDetection = React.lazy(() => import('./pages/AnomalyDetection'));
const RootCause = React.lazy(() => import('./pages/RootCause'));
const Shell = React.lazy(() => import('./pages/Shell'));
const ServiceGraph = React.lazy(() => import('./pages/ServiceGraph'));
const Incidents = React.lazy(() => import('./pages/Incidents'));

export default function App() {
  return (
    <BrowserRouter>
      <DataProvider>
        <React.Suspense fallback={<div style={{ padding: 24 }}>Initializing interface...</div>}>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Overview />} />
              <Route path="live-telemetry" element={<LiveTelemetry />} />
              <Route path="anomaly-detection" element={<AnomalyDetection />} />
              <Route path="root-cause" element={<RootCause />} />
              <Route path="incidents" element={<Incidents />} />
              <Route path="service-graph" element={<ServiceGraph />} />
              <Route path="settings" element={<Shell />} />
              <Route path="profile" element={<Shell />} />
            </Route>
          </Routes>
        </React.Suspense>
      </DataProvider>
    </BrowserRouter>
  );
}
