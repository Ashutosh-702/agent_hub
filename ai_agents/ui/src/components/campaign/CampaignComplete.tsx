import { useNavigate } from 'react-router-dom';

interface CampaignCompleteProps {
  sequenceName: string;
}

export const CampaignComplete = ({ sequenceName }: CampaignCompleteProps) => {
  const navigate = useNavigate();

  return (
    <div className="campaign-complete">
      <div className="complete-card">
        {/* Success Animation */}
        <div className="success-animation">
          <div className="success-circle">
            <svg className="checkmark" width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path className="check-path" d="M20 6L9 17l-5-5"/>
            </svg>
          </div>
          <div className="confetti">
            {[...Array(12)].map((_, i) => (
              <div key={i} className={`confetti-piece piece-${i + 1}`} />
            ))}
          </div>
        </div>

        <h1>Campaign Created Successfully! 🎉</h1>
        <p className="subtitle">
          Your leads have been enrolled to the sequence <strong>"{sequenceName}"</strong>
        </p>

        <div className="complete-details">
          <div className="detail-card">
            <div className="detail-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
            </div>
            <div className="detail-content">
              <h4>Leads Enrolled</h4>
              <p>All approved leads are now in your outreach sequence</p>
            </div>
          </div>

          <div className="detail-card">
            <div className="detail-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
            </div>
            <div className="detail-content">
              <h4>Personalized Outreach</h4>
              <p>Each lead will receive their custom message and deck</p>
            </div>
          </div>

          <div className="detail-card">
            <div className="detail-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
            </div>
            <div className="detail-content">
              <h4>Automated Follow-ups</h4>
              <p>Lemlist will handle the sequence timing and follow-ups</p>
            </div>
          </div>
        </div>

        {/* Lemlist Link */}
        <div className="lemlist-link-card">
          <div className="lemlist-logo">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="12" cy="12" r="10"/>
              <path d="M8 12l2 2 4-4"/>
            </svg>
          </div>
          <div className="lemlist-info">
            <h4>View in Lemlist</h4>
            <p>Track your campaign progress, responses, and analytics</p>
          </div>
          <a 
            href="https://app.lemlist.com" 
            target="_blank" 
            rel="noopener noreferrer"
            className="btn-primary"
          >
            Open Lemlist
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
              <polyline points="15 3 21 3 21 9"/>
              <line x1="10" y1="14" x2="21" y2="3"/>
            </svg>
          </a>
        </div>

        {/* Actions */}
        <div className="complete-actions">
          <button className="btn-secondary" onClick={() => navigate('/campaign')}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="19" y1="12" x2="5" y2="12"/>
              <polyline points="12 19 5 12 12 5"/>
            </svg>
            Back to Campaigns
          </button>
          <button className="btn-primary" onClick={() => navigate('/campaign/new')}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            Create Another Campaign
          </button>
        </div>
      </div>
    </div>
  );
};

