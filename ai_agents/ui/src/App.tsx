import './App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Form } from './components/FormNew';
import { Companies } from './components/Companies';
import { Contacts } from './components/Contacts';
import { CampaignList } from './components/CampaignList';

function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/campaign" replace />} />
            <Route path="/campaign" element={<CampaignList />} />
            <Route path="/campaign/new" element={<Form />} />
            <Route path="/master-data" element={<Navigate to="/master-data/companies" replace />} />
            <Route path="/master-data/companies" element={<Companies />} />
            <Route path="/master-data/contacts" element={<Contacts />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
