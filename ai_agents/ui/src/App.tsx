import './App.css';
import './novus-overrides.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Form } from './components/FormNew';
import { Companies } from './components/Companies';
import { CompanyDetails } from './components/CompanyDetails';
import { CampaignList } from './components/CampaignList';
import { CampaignDetails } from './components/CampaignDetails';
import { ComingSoon } from './components/ComingSoon';
import { SidebarProvider, useSidebar } from './context/SidebarContext';

function AppContent() {
  const { isCollapsed } = useSidebar();

  return (
    <div className="app-layout">
      <Sidebar />
      <main className={`main-content ${isCollapsed ? 'sidebar-collapsed' : ''}`}>
          <Routes>
            <Route path="/" element={<Navigate to="/master-data/campaign" replace />} />
            <Route path="/campaign" element={<Navigate to="/master-data/campaign" replace />} />
            <Route path="/master-data" element={<Navigate to="/master-data/campaign" replace />} />
            <Route path="/master-data/campaign" element={<CampaignList />} />
            <Route path="/master-data/campaign/:campaignId" element={<CampaignDetails />} />
            <Route path="/master-data/companies" element={<Companies />} />
            <Route path="/master-data/companies/:companyId" element={<CompanyDetails />} />
            <Route path="/prospecting" element={<Navigate to="/prospecting/wide" replace />} />
            <Route path="/prospecting/company" element={<ComingSoon />} />
            <Route path="/prospecting/contact" element={<ComingSoon />} />
            <Route path="/prospecting/wide" element={<Form />} />
          </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <SidebarProvider>
        <AppContent />
      </SidebarProvider>
    </BrowserRouter>
  );
}

export default App;
