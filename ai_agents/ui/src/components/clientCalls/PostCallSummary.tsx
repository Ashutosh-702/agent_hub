import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PageHeader, BackButton, Loader } from '../shared';

interface MeetingSummary {
  summary?: string;
  key_discussion_points?: string[];
  objections_resolutions?: Array<{ objection: string; resolution: string }>;
  action_items?: Array<{ text: string; owner?: string; due_date?: string }>;
  next_steps?: string[];
  follow_up_message?: {
    subject: string;
    body: string;
  };
}

interface Meeting {
  id: string;
  meeting_name?: string;
  company_domain?: string;
  started_at?: string;
  ended_at?: string;
  product_ids?: string[];
  summary?: string;
  key_discussion_points?: string[];
  action_items?: Array<{ text: string; owner?: string; due_date?: string }>;
  next_steps?: string[];
  objections_resolutions?: Array<{ objection: string; resolution: string }>;
}

export const PostCallSummary = () => {
  const { meetingId } = useParams<{ meetingId: string }>();
  const navigate = useNavigate();
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [analysis, setAnalysis] = useState<MeetingSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  useEffect(() => {
    const loadSummary = async () => {
      if (!meetingId) return;
      
      setIsLoading(true);
      try {
        // Fetch meeting data
        const meetingRes = await fetch(`/api/v1/meetings/${meetingId}`);
        const meetingData = await meetingRes.json();
        
        if (meetingData.success) {
          const m = meetingData.data;
          setMeeting(m);
          
          // If summary exists, use it; otherwise trigger analysis
          if (m.summary) {
            setAnalysis({
              summary: m.summary,
              key_discussion_points: m.key_discussion_points || [],
              objections_resolutions: m.objections_resolutions || [],
              action_items: m.action_items || [],
              next_steps: m.next_steps || [],
            });
          } else {
            // Trigger analysis
            await triggerAnalysis();
          }
        }
      } catch (error) {
        console.error('Error loading summary:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadSummary();
  }, [meetingId]);
  
  const triggerAnalysis = async () => {
    if (!meetingId) return;
    
    setIsAnalyzing(true);
    try {
      const res = await fetch(`/api/v1/meetings/${meetingId}/analyze`, {
        method: 'POST',
      });
      const data = await res.json();
      
      if (data.success) {
        setAnalysis(data.data);
        // Refresh meeting to get updated data
        const meetingRes = await fetch(`/api/v1/meetings/${meetingId}`);
        const meetingData = await meetingRes.json();
        if (meetingData.success) {
          setMeeting(meetingData.data);
        }
      }
    } catch (error) {
      console.error('Error analyzing meeting:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };
  
  const formatDuration = (started?: string, ended?: string) => {
    if (!started || !ended) return 'N/A';
    const start = new Date(started);
    const end = new Date(ended);
    const seconds = Math.floor((end.getTime() - start.getTime()) / 1000);
    const mins = Math.floor(seconds / 60);
    return `${mins} minutes`;
  };
  
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // Could add a toast notification here
  };
  
  if (isLoading) {
    return <Loader text="Loading meeting summary..." />;
  }
  
  if (!meeting) {
    return <div className="form-error">Meeting not found</div>;
  }
  
  const displayData = analysis || {
    summary: meeting.summary,
    key_discussion_points: meeting.key_discussion_points || [],
    objections_resolutions: meeting.objections_resolutions || [],
    action_items: meeting.action_items || [],
    next_steps: meeting.next_steps || [],
  };
  
  return (
    <div className="post-call-container">
      <BackButton to="/client-calls" label="Back to Client Calls" />
      <PageHeader
        title="Meeting Summary"
        subtitle={`${meeting.company_domain || meeting.meeting_name || 'Meeting'} • ${meeting.ended_at ? new Date(meeting.ended_at).toLocaleDateString() : ''} • ${formatDuration(meeting.started_at, meeting.ended_at)}`}
      />
      
      {!displayData.summary && !isAnalyzing && (
        <div style={{ marginBottom: '1rem', padding: '1rem', background: 'var(--color-info-light)', borderRadius: 'var(--border-radius-md)' }}>
          <p>No summary available. Click "Generate Analysis" to create one.</p>
          <button className="btn-primary" onClick={triggerAnalysis} style={{ marginTop: '0.5rem' }}>
            Generate Analysis
          </button>
        </div>
      )}
      
      {isAnalyzing && (
        <div style={{ marginBottom: '1rem', padding: '1rem', background: 'var(--color-info-light)', borderRadius: 'var(--border-radius-md)' }}>
          <Loader text="Analyzing meeting..." />
        </div>
      )}
      
      {/* Summary */}
      {displayData.summary && (
        <section className="summary-section">
          <h3 className="summary-section-title">📝 Summary</h3>
          <p className="summary-text">{displayData.summary}</p>
        </section>
      )}
      
      {/* Key Discussion Points */}
      {displayData.key_discussion_points && displayData.key_discussion_points.length > 0 && (
        <section className="summary-section">
          <h3 className="summary-section-title">💡 Key Discussion Points</h3>
          <ul className="summary-list">
            {displayData.key_discussion_points.map((point, idx) => (
              <li key={idx}>{point}</li>
            ))}
          </ul>
        </section>
      )}
      
      {/* Objections & Resolutions */}
      {displayData.objections_resolutions && displayData.objections_resolutions.length > 0 && (
        <section className="summary-section">
          <h3 className="summary-section-title">⚠️ Objections & Resolutions</h3>
          {displayData.objections_resolutions.map((item, idx) => (
            <div key={idx} className="objection-item">
              <p className="objection-text">"{item.objection}"</p>
              <p className="objection-response">✓ {item.resolution || 'Not yet resolved'}</p>
            </div>
          ))}
        </section>
      )}
      
      {/* Action Items */}
      {displayData.action_items && displayData.action_items.length > 0 && (
        <section className="summary-section">
          <h3 className="summary-section-title">✓ Action Items</h3>
          {displayData.action_items.map((item, idx) => (
            <div key={idx} className="action-item-card">
              <span className="action-item-icon">📌</span>
              <div>
                <p className="action-item-text">{item.text}</p>
                <p className="action-item-owner">
                  Owner: {item.owner || 'TBD'} {item.due_date && `• Due: ${item.due_date}`}
                </p>
              </div>
            </div>
          ))}
        </section>
      )}
      
      {/* Next Steps */}
      {displayData.next_steps && displayData.next_steps.length > 0 && (
        <section className="summary-section">
          <h3 className="summary-section-title">➡️ Next Steps</h3>
          {displayData.next_steps.map((step, idx) => (
            <div key={idx} className="next-step-item">
              <span>{idx + 1}.</span>
              <span>{step}</span>
            </div>
          ))}
        </section>
      )}
      
      {/* Follow-up Message Draft */}
      {displayData.follow_up_message && (
        <section className="summary-section">
          <h3 className="summary-section-title">📧 Follow-up Message Draft</h3>
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
              <div style={{ fontWeight: '500', marginBottom: '0.5rem', color: 'var(--color-gray-700)' }}>
                Subject: {displayData.follow_up_message.subject}
              </div>
              <button className="copy-section-btn" onClick={() => copyToClipboard(displayData.follow_up_message!.body)}>
                📋 Copy Body
              </button>
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
              {displayData.follow_up_message.body}
            </pre>
          </div>
        </section>
      )}
      
      {/* Action Buttons */}
      <div className="action-buttons">
        {!displayData.summary && (
          <button className="btn-primary" onClick={triggerAnalysis} disabled={isAnalyzing}>
            {isAnalyzing ? 'Analyzing...' : 'Generate Analysis'}
          </button>
        )}
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
