import { useNavigate } from 'react-router-dom';
import { PageHeader, BackButton } from '../shared';

// Icons
const PhoneIcon = (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
  </svg>
);

const UploadIcon = (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
);

interface PhoneCallOptionProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  buttonText: string;
  onClick: () => void;
  variant: 'blue' | 'purple';
}

const PhoneCallOption = ({ icon, title, description, buttonText, onClick, variant }: PhoneCallOptionProps) => (
  <div className="phone-call-option-card" onClick={onClick}>
    <div className={`phone-call-icon-wrapper ${variant}`}>
      {icon}
    </div>
    <div className="phone-call-content">
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
    <button className={`phone-call-btn ${variant}`}>
      {buttonText}
    </button>
  </div>
);

export const PhoneCallPage = () => {
  const navigate = useNavigate();

  return (
    <div className="phone-call-container">
      <BackButton to="/client-calls" label="Back to Client Calls" />
      <PageHeader 
        title="Phone Call" 
        subtitle="Start a new phone call or log an existing call recording"
      />
      
      <div className="phone-call-options">
        <PhoneCallOption
          icon={PhoneIcon}
          title="Start Phone Call"
          description="Begin a live phone call with real-time transcription. You'll be prompted to share screen audio so Nebula can listen to both sides of the conversation."
          buttonText="Start Call"
          onClick={() => navigate('/client-calls/phone/start')}
          variant="blue"
        />
        
        <PhoneCallOption
          icon={UploadIcon}
          title="Log Existing Call"
          description="Upload a recorded phone call audio file to transcribe and analyze. Supports MP3, WAV, and other common audio formats."
          buttonText="Upload Recording"
          onClick={() => navigate('/client-calls/phone/log')}
          variant="purple"
        />
      </div>
    </div>
  );
};


