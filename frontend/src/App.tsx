import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { DashboardPage } from './pages/DashboardPage';
import { RiskMapPage } from './pages/RiskMapPage';
import { ProjectsPage } from './pages/ProjectsPage';
import { ProjectDetailPage } from './pages/ProjectDetailPage';
import { StatesAnalyticsPage } from './pages/StatesAnalyticsPage';
import { StateDetailPage } from './pages/StateDetailPage';
import { MpsAnalyticsPage } from './pages/MpsAnalyticsPage';
import { MpDetailPage } from './pages/MpDetailPage';
import { AlertsPage } from './pages/AlertsPage';
import { DataQualityPage } from './pages/DataQualityPage';
import { AuditLogsPage } from './pages/AuditLogsPage';
import { SettingsPage } from './pages/SettingsPage';
import { LoginPage } from './pages/LoginPage';
import { ComparePage } from './pages/ComparePage';
import { ReportsPage } from './pages/ReportsPage';
import { User } from './types';

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>({
    id: 'usr-admin-01',
    username: 'admin',
    full_name: 'Executive Administrator',
    email: 'admin@mpladguardian.gov.in',
    role: 'ADMIN',
    department: 'Parliamentary Oversight Cell',
  });

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage onLoginSuccess={(u) => setCurrentUser(u)} />} />

        <Route element={<AppLayout currentUser={currentUser} onUserChange={(u) => setCurrentUser(u)} />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/risk-map" element={<RiskMapPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/projects/:id" element={<ProjectDetailPage />} />
          <Route path="/analytics/states" element={<StatesAnalyticsPage />} />
          <Route path="/analytics/states/:state" element={<StateDetailPage />} />
          <Route path="/mps" element={<MpsAnalyticsPage />} />
          <Route path="/mps/:id" element={<MpDetailPage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/data-quality" element={<DataQualityPage />} />
          <Route path="/audit" element={<AuditLogsPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
