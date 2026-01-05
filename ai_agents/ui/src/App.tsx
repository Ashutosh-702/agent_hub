import './App.css';
import { useEffect } from 'react';
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
import { LoginPage, ProtectedRoute } from './components/auth';
import { getStoredUser } from './store/api';
import { identifyUser } from './services/analytics';
import { 
  ClientCallsPage, 
  StartMeetingForm, 
  LiveMeetingScreen, 
  PostCallSummary,
  PrepMeetingForm, 
  BattlecardView, 
  PostCallReflections,
  ReflectionsView,
  PhoneCallPage,
  StartPhoneCallForm,
  LogPhoneCallForm,
} from './components/clientCalls';

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
            {/* Client Calls - Live Meeting & Battlecard Prep */}
            <Route path="/client-calls" element={<ClientCallsPage />} />
            <Route path="/client-calls/start" element={<StartMeetingForm />} />
            <Route path="/client-calls/live/:meetingId" element={<LiveMeetingScreen />} />
            <Route path="/client-calls/summary/:meetingId" element={<PostCallSummary />} />
            <Route path="/client-calls/prep" element={<PrepMeetingForm />} />
            <Route path="/client-calls/battlecard/:battlecardId" element={<BattlecardView />} />
            <Route path="/client-calls/reflections" element={<PostCallReflections />} />
            <Route path="/client-calls/reflections/:meetingId" element={<ReflectionsView />} />
            {/* Phone Call Routes */}
            <Route path="/client-calls/phone" element={<PhoneCallPage />} />
            <Route path="/client-calls/phone/start" element={<StartPhoneCallForm />} />
            <Route path="/client-calls/phone/log" element={<LogPhoneCallForm />} />
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

function ProtectedApp() {
  // Identify user for analytics on app load if already authenticated
  useEffect(() => {
    const user = getStoredUser();
    if (user) {
      identifyUser({
        id: user.id,
        email: user.email,
        name: user.name,
      });
    }
  }, []);

  return (
    <ProtectedRoute>
      <SidebarProvider>
        <AppContent />
      </SidebarProvider>
    </ProtectedRoute>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public route - Login page */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* All other routes are protected */}
        <Route path="/*" element={<ProtectedApp />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
