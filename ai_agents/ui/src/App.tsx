import './App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Form } from './components/FormNew';
import { Companies } from './components/Companies';
import { CompanyDetails } from './components/CompanyDetails';
import { CampaignList } from './components/CampaignList';
import { CampaignDetails } from './components/CampaignDetails';
import { ComingSoon } from './components/ComingSoon';
import { NewCampaignWizard } from './components/campaign';
import { ProspectingCampaigns } from './components/ProspectingCampaigns';
import { SidebarProvider, useSidebar } from './context/SidebarContext';
import { HubSpotLayout, CreateCompanyWizard, CreateContactWizard, CreateDealWizard } from './components/hubspot';
import { InboxDashboard, InboxPage } from './components/inbox';

function AppContent() {
  const { isCollapsed } = useSidebar();

  return (
    <div className="app-layout">
      <Sidebar />
      <main className={`main-content ${isCollapsed ? 'sidebar-collapsed' : ''}`}>
          <Routes>
            <Route path="/" element={<Navigate to="/inbox" replace />} />
            {/* Inbox - Unified Outreach Inbox */}
            <Route path="/inbox" element={<InboxDashboard />} />
            <Route path="/inbox/messages" element={<InboxPage />} />
            <Route path="/inbox/messages/:leadId" element={<InboxPage />} />
            {/* Campaign - Top level section */}
            <Route path="/campaign" element={<CampaignList />} />
            <Route path="/campaign/new" element={<NewCampaignWizard />} />
            <Route path="/campaign/:campaignId" element={<CampaignDetails />} />
            {/* Master Data - Companies & Contacts */}
            <Route path="/master-data" element={<Navigate to="/master-data/companies" replace />} />
            <Route path="/master-data/companies" element={<Companies />} />
            <Route path="/master-data/companies/:companyId" element={<CompanyDetails />} />
            <Route path="/master-data/contacts" element={<ComingSoon />} />
            {/* Prospecting */}
            <Route path="/prospecting" element={<Navigate to="/prospecting/campaigns" replace />} />
            <Route path="/prospecting/campaigns" element={<ProspectingCampaigns />} />
            <Route path="/prospecting/company" element={<ComingSoon />} />
            <Route path="/prospecting/contact" element={<ComingSoon />} />
            <Route path="/prospecting/wide" element={<Form />} />
            {/* HubSpot Integration */}
            <Route path="/hubspot" element={<HubSpotLayout />}>
              <Route index element={null} />
              <Route path="company" element={<CreateCompanyWizard />} />
              <Route path="contact" element={<CreateContactWizard />} />
              <Route path="deal" element={<CreateDealWizard />} />
            </Route>
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
