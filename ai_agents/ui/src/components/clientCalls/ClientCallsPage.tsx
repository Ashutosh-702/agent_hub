import { useNavigate } from 'react-router-dom';
import { PageHeader } from '../shared';
import { MeetingHistory } from './MeetingHistory';

// Icons for the module cards
const Icons = {
  phone: (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
    </svg>
  ),
  clipboard: (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
      <rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>
      <path d="M9 12h6"/>
      <path d="M9 16h6"/>
    </svg>
  ),
  lightbulb: (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 18h6"/>
      <path d="M10 22h4"/>
      <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/>
    </svg>
  ),
};

interface ModuleCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  buttonText: string;
  onClick: () => void;
  variant: 'green' | 'purple' | 'orange';
}

const ModuleCard = ({ icon, title, description, buttonText, onClick, variant }: ModuleCardProps) => (
  <div className="client-calls-module-card" onClick={onClick}>
    <div className={`module-icon-wrapper ${variant}`}>
      {icon}
    </div>
    <div className="module-card-content">
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
    <button className={`module-card-btn ${variant}`}>
      {buttonText}
    </button>
  </div>
);

export const ClientCallsPage = () => {
  const navigate = useNavigate();

  return (
    <div className="client-calls-container">
      <PageHeader 
        title="Client Calls" 
        subtitle="Manage your client meetings with AI-powered insights and preparation"
      />
      
      <div className="client-calls-modules">
        <ModuleCard
          icon={Icons.phone}
          title="Start Meeting"
          description="Begin a live call with real-time transcription and AI-powered insights. Get intelligent suggestions as you speak with your prospect."
          buttonText="Start New Meeting"
          onClick={() => navigate('/client-calls/start')}
          variant="green"
        />
        
        <ModuleCard
          icon={Icons.clipboard}
          title="Prep for Meeting"
          description="Generate a comprehensive battlecard before your meeting. Get talking points, objection handlers, and discovery questions."
          buttonText="Prepare Battlecard"
          onClick={() => navigate('/client-calls/prep')}
          variant="purple"
        />
        
        <ModuleCard
          icon={Icons.lightbulb}
          title="Post Call Reflections"
          description="Review AI-generated insights from past calls. Add your own notes and track deal progress over time."
          buttonText="View Reflections"
          onClick={() => navigate('/client-calls/reflections')}
          variant="orange"
        />
      </div>
      
      {/* Recent Meetings Section */}
      <div style={{ marginTop: 'var(--space-10)' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: 'var(--space-4)'
        }}>
          <h2 style={{ 
            margin: 0, 
            fontSize: 'var(--text-xl)', 
            fontWeight: 600, 
            color: 'var(--color-gray-800)' 
          }}>
            Recent Meetings
          </h2>
          <button 
            className="btn-secondary" 
            onClick={() => navigate('/client-calls/reflections')}
            style={{ padding: '0.5rem 1rem', fontSize: 'var(--text-sm)' }}
          >
            View All →
          </button>
        </div>
        <MeetingHistory limit={5} showFilters={false} />
      </div>
    </div>
  );
};
