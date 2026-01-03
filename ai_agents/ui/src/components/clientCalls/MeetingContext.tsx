interface MeetingContextProps {
  context: {
    company: {
      name: string;
      industry: string;
      size: string;
      website?: string;
    };
    contacts: Array<{ name: string; title: string }>;
    products: string[];
    painPoints: string[];
    previousMeetings: number;
    dealStage: string;
  };
  actionItems: string[];
}

export const MeetingContext = ({ context, actionItems }: MeetingContextProps) => {
  return (
    <div>
      {/* Company Info */}
      <div className="context-section">
        <div className="context-label">Company</div>
        <div className="context-value">{context.company.name}</div>
        <div className="context-subtitle">{context.company.industry}</div>
        <div className="context-subtitle">{context.company.size}</div>
      </div>
      
      {/* Contacts */}
      <div className="context-section">
        <div className="context-label">Attendees</div>
        {context.contacts.map((contact, idx) => (
          <div key={idx} style={{ marginBottom: '0.25rem' }}>
            <span className="context-value">{contact.name}</span>
            <span className="context-subtitle" style={{ marginLeft: '0.5rem' }}>({contact.title})</span>
          </div>
        ))}
      </div>
      
      {/* Products */}
      <div className="context-section">
        <div className="context-label">Products</div>
        <div className="context-tags">
          {context.products.map((product, idx) => (
            <span key={idx} className="context-tag">{product}</span>
          ))}
        </div>
      </div>
      
      {/* Pain Points */}
      <div className="context-section">
        <div className="context-label">Known Pain Points</div>
        <ul style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--color-gray-600)' }}>
          {context.painPoints.map((point, idx) => (
            <li key={idx} style={{ fontSize: '0.875rem', marginBottom: '0.25rem' }}>{point}</li>
          ))}
        </ul>
      </div>
      
      {/* Deal Stage */}
      <div className="context-section">
        <div className="context-label">Deal Stage</div>
        <span className="context-tag" style={{ background: 'var(--color-info-light)', color: 'var(--color-info)' }}>
          {context.dealStage}
        </span>
      </div>
      
      {/* Previous Meetings */}
      {context.previousMeetings > 0 && (
        <div className="context-section">
          <div className="context-label">Previous Meetings</div>
          <div className="context-value">{context.previousMeetings}</div>
        </div>
      )}
      
      {/* Action Items (added during meeting) */}
      {actionItems.length > 0 && (
        <div className="context-section">
          <div className="context-label">Action Items ({actionItems.length})</div>
          {actionItems.map((item, idx) => (
            <div key={idx} className="action-item-card" style={{ marginBottom: '0.5rem' }}>
              <span className="action-item-icon">✓</span>
              <p className="action-item-text" style={{ margin: 0, fontSize: '0.875rem' }}>{item}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

