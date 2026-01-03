import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PageHeader, BackButton, Loader } from '../shared';

// Mock meeting summary data
const MOCK_SUMMARY = {
  id: 'm1',
  meetingName: 'Discovery Call - Acme Retail',
  company: 'Acme Retail Ltd',
  date: new Date().toISOString(),
  duration: 2340, // seconds
  attendees: ['Rajesh Kumar (VP Operations)', 'Priya Sharma (CTO)'],
  products: ['Fynd OMS', 'Fynd WMS'],
  summary: `Productive discovery call with Acme Retail's leadership team. They're experiencing significant challenges with their current order management system, particularly around inventory visibility and fulfillment speed. The team showed strong interest in our OMS and WMS solutions, especially the real-time inventory sync feature. Budget discussions will happen in Q2, but they're eager to see a detailed demo.`,
  keyPoints: [
    'Current OMS causing 15% order cancellation rate due to inventory inaccuracies',
    'Expanding to 50+ stores in the next 18 months',
    'Looking for omnichannel capabilities (BOPIS, ship-from-store)',
    'IT team prefers cloud-native solutions with API-first architecture',
    'Decision timeline: 3-4 months, implementation before festive season',
  ],
  objections: [
    {
      objection: 'Concerned about migration complexity from legacy system',
      resolution: 'Highlighted our phased migration approach and dedicated implementation team',
    },
    {
      objection: 'Worried about integration with their custom ERP',
      resolution: 'Discussed our flexible API architecture and successful similar integrations',
    },
  ],
  actionItems: [
    { item: 'Send OMS + WMS integration architecture document', owner: 'You', dueDate: 'Tomorrow' },
    { item: 'Schedule technical deep-dive with their IT team', owner: 'You', dueDate: 'This week' },
    { item: 'Share case studies from similar retail implementations', owner: 'You', dueDate: '3 days' },
    { item: 'Prepare ROI calculator with their specific metrics', owner: 'You', dueDate: 'Before demo' },
  ],
  nextSteps: [
    'Technical demo scheduled for next Thursday',
    'Send proposal with pricing tiers by end of week',
    'Connect them with reference customer (Fashion Retail Co)',
  ],
  followUpMessages: [
    {
      contact: 'Rajesh Kumar',
      email: 'rajesh@acme.com',
      subject: 'Follow-up: Fynd OMS & WMS Discovery Call',
      draft: `Hi Rajesh,\n\nThank you for taking the time to discuss your omnichannel challenges today. I really appreciated your insights on the inventory visibility issues you're facing.\n\nAs promised, I'm attaching:\n• OMS + WMS integration architecture overview\n• Case study: How Fashion Retail Co reduced order cancellations by 40%\n\nI'm also scheduling a technical deep-dive with Priya and your IT team for next week.\n\nLooking forward to the demo on Thursday!\n\nBest regards`,
    },
  ],
};

export const PostCallSummary = () => {
  const { meetingId } = useParams<{ meetingId: string }>();
  const navigate = useNavigate();
  const [summary, setSummary] = useState<typeof MOCK_SUMMARY | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    // Simulate API fetch
    const loadSummary = async () => {
      setIsLoading(true);
      // In production, fetch from API
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSummary(MOCK_SUMMARY);
      setIsLoading(false);
    };
    
    loadSummary();
  }, [meetingId]);
  
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    return `${mins} minutes`;
  };
  
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // Could add a toast notification here
  };
  
  if (isLoading) {
    return <Loader text="Generating meeting summary..." />;
  }
  
  if (!summary) {
    return <div className="form-error">Meeting not found</div>;
  }
  
  return (
    <div className="post-call-container">
      <BackButton to="/client-calls" label="Back to Client Calls" />
      <PageHeader
        title="Meeting Summary"
        subtitle={`${summary.company} • ${new Date(summary.date).toLocaleDateString()} • ${formatDuration(summary.duration)}`}
      />
      
      {/* Summary */}
      <section className="summary-section">
        <h3 className="summary-section-title">📝 Summary</h3>
        <p className="summary-text">{summary.summary}</p>
      </section>
      
      {/* Key Discussion Points */}
      <section className="summary-section">
        <h3 className="summary-section-title">💡 Key Discussion Points</h3>
        <ul className="summary-list">
          {summary.keyPoints.map((point, idx) => (
            <li key={idx}>{point}</li>
          ))}
        </ul>
      </section>
      
      {/* Objections & Resolutions */}
      <section className="summary-section">
        <h3 className="summary-section-title">⚠️ Objections & Resolutions</h3>
        {summary.objections.map((item, idx) => (
          <div key={idx} className="objection-item">
            <p className="objection-text">"{item.objection}"</p>
            <p className="objection-response">✓ {item.resolution}</p>
          </div>
        ))}
      </section>
      
      {/* Action Items */}
      <section className="summary-section">
        <h3 className="summary-section-title">✓ Action Items</h3>
        {summary.actionItems.map((item, idx) => (
          <div key={idx} className="action-item-card">
            <span className="action-item-icon">📌</span>
            <div>
              <p className="action-item-text">{item.item}</p>
              <p className="action-item-owner">Owner: {item.owner} • Due: {item.dueDate}</p>
            </div>
          </div>
        ))}
      </section>
      
      {/* Next Steps */}
      <section className="summary-section">
        <h3 className="summary-section-title">➡️ Next Steps</h3>
        {summary.nextSteps.map((step, idx) => (
          <div key={idx} className="next-step-item">
            <span>{idx + 1}.</span>
            <span>{step}</span>
          </div>
        ))}
      </section>
      
      {/* Follow-up Message Drafts */}
      <section className="summary-section">
        <h3 className="summary-section-title">📧 Follow-up Message Draft</h3>
        {summary.followUpMessages.map((msg, idx) => (
          <div key={idx} style={{ marginBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
              <div>
                <strong>{msg.contact}</strong>
                <span style={{ color: 'var(--color-gray-500)', fontSize: '0.875rem', marginLeft: '0.5rem' }}>
                  ({msg.email})
                </span>
              </div>
              <button className="copy-section-btn" onClick={() => copyToClipboard(msg.draft)}>
                📋 Copy
              </button>
            </div>
            <div style={{ fontWeight: '500', marginBottom: '0.5rem', color: 'var(--color-gray-700)' }}>
              Subject: {msg.subject}
            </div>
            <pre style={{
              margin: 0,
              padding: '1rem',
              background: 'var(--color-gray-50)',
              borderRadius: 'var(--radius-md)',
              whiteSpace: 'pre-wrap',
              fontFamily: 'var(--font-family)',
              fontSize: '0.875rem',
              lineHeight: 1.6,
              color: 'var(--color-gray-700)',
            }}>
              {msg.draft}
            </pre>
          </div>
        ))}
      </section>
      
      {/* Action Buttons */}
      <div className="action-buttons">
        <button className="btn-primary" onClick={() => navigate(`/client-calls/reflections/${meetingId}`)}>
          View Reflections
        </button>
        <button className="btn-secondary" onClick={() => navigate('/client-calls')}>
          Back to Client Calls
        </button>
      </div>
    </div>
  );
};
