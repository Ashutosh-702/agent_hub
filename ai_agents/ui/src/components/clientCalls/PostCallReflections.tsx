import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PageHeader, BackButton, Loader } from '../shared';

// Mock reflections data for list view
const MOCK_MEETINGS_WITH_REFLECTIONS = [
  {
    id: 'm1',
    meetingName: 'Discovery Call - Acme Retail',
    company: 'Acme Retail Ltd',
    date: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    duration: 2340,
    aiReflections: {
      dealHealthScore: 85,
      relationshipStatus: 'engaged' as const,
      summary: 'Strong discovery call with clear pain points identified. High engagement from leadership team.',
      hasManualNotes: true,
    },
  },
  {
    id: 'm2',
    meetingName: 'Product Demo - TechStart Inc',
    company: 'TechStart Inc',
    date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    duration: 3600,
    aiReflections: {
      dealHealthScore: 65,
      relationshipStatus: 'warming' as const,
      summary: 'Technical demo went well but pricing concerns remain. Need to address ROI more clearly.',
      hasManualNotes: false,
    },
  },
  {
    id: 'm3',
    meetingName: 'Follow-up Call - Fashion Hub',
    company: 'Fashion Hub',
    date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    duration: 1800,
    aiReflections: {
      dealHealthScore: 45,
      relationshipStatus: 'cold' as const,
      summary: 'Stakeholder change causing delays. New decision maker needs to be brought up to speed.',
      hasManualNotes: true,
    },
  },
];

// Mock detailed reflections for single meeting view
const MOCK_DETAILED_REFLECTIONS = {
  aiGenerated: {
    dealHealthScore: 85,
    relationshipStatus: 'engaged' as const,
    whatWentWell: [
      'Clear articulation of pain points by the prospect',
      'Strong engagement from both technical and business stakeholders',
      'Successful objection handling around migration concerns',
      'Prospect expressed urgency with timeline (before festive season)',
    ],
    areasForImprovement: [
      'Could have explored budget constraints earlier in the conversation',
      'Missed opportunity to discuss success metrics and KPIs',
      'Should have asked more about their decision-making process',
    ],
    competitorInsights: [
      'They mentioned evaluating Unicommerce - emphasize our omnichannel superiority',
      'Previous bad experience with implementation suggests need for strong support messaging',
    ],
    recommendedFollowUps: [
      { action: 'Schedule technical deep-dive with IT team', priority: 'high' as const },
      { action: 'Send ROI calculator with their specific metrics', priority: 'high' as const },
      { action: 'Connect with reference customer in similar industry', priority: 'medium' as const },
      { action: 'Prepare competitive comparison vs Unicommerce', priority: 'low' as const },
    ],
    riskFactors: [
      'Q2 budget cycle may cause delays if not closed quickly',
      'CTO seemed cautious about cloud migration - address security concerns',
    ],
  },
  manual: {
    personalNotes: 'Rajesh seems like the real champion here. Need to equip him with materials to sell internally. Priya (CTO) is more hesitant - arrange a call with our Head of Engineering?',
    keyTakeaways: [
      'Budget approval needs CEO sign-off for deals > 50L',
      'They have a PoC requirement before final decision',
      'Existing Shopify integration is critical',
    ],
    confidenceLevel: 'high' as const,
    nextCallFocus: 'Focus on technical architecture and security compliance. Prepare answers for SOC2 and GDPR questions.',
  },
};

// List view component
const ReflectionsList = () => {
  const navigate = useNavigate();
  
  const getHealthScoreClass = (score: number) => {
    if (score >= 70) return 'high';
    if (score >= 40) return 'medium';
    return 'low';
  };
  
  return (
    <div className="reflections-container">
      <PageHeader
        title="Post Call Reflections"
        subtitle="Review AI insights and your notes from past meetings"
      />
      
      {MOCK_MEETINGS_WITH_REFLECTIONS.length === 0 ? (
        <div className="reflections-empty">
          <div className="reflections-empty-icon">📝</div>
          <h3>No meetings yet</h3>
          <p>Complete a meeting to see reflections here</p>
        </div>
      ) : (
        <div className="reflections-list">
          {MOCK_MEETINGS_WITH_REFLECTIONS.map((meeting) => (
            <div
              key={meeting.id}
              className="reflection-meeting-card"
              onClick={() => navigate(`/client-calls/reflections/${meeting.id}`)}
            >
              <div className="reflection-card-header">
                <div>
                  <h3 className="reflection-card-title">{meeting.meetingName}</h3>
                  <p className="reflection-card-date">
                    {meeting.company} • {new Date(meeting.date).toLocaleDateString()}
                  </p>
                </div>
                <div className="reflection-card-metrics">
                  <div className="health-score">
                    <div className={`health-score-value ${getHealthScoreClass(meeting.aiReflections.dealHealthScore)}`}>
                      {meeting.aiReflections.dealHealthScore}%
                    </div>
                    <div className="health-score-label">Health</div>
                  </div>
                  <span className={`relationship-badge ${meeting.aiReflections.relationshipStatus}`}>
                    {meeting.aiReflections.relationshipStatus}
                  </span>
                </div>
              </div>
              <p className="reflection-card-summary">{meeting.aiReflections.summary}</p>
              <div className="reflection-card-status">
                <span>🤖 AI Reflections</span>
                {meeting.aiReflections.hasManualNotes && <span>✏️ Manual Notes</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Detail view component
const ReflectionsDetail = ({ meetingId }: { meetingId: string }) => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [reflections, setReflections] = useState<typeof MOCK_DETAILED_REFLECTIONS | null>(null);
  const [manualNotes, setManualNotes] = useState('');
  const [keyTakeaways, setKeyTakeaways] = useState<string[]>([]);
  const [newTakeaway, setNewTakeaway] = useState('');
  const [confidenceLevel, setConfidenceLevel] = useState<'low' | 'medium' | 'high'>('medium');
  const [nextCallFocus, setNextCallFocus] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  
  const meeting = MOCK_MEETINGS_WITH_REFLECTIONS.find(m => m.id === meetingId);
  
  useEffect(() => {
    const loadReflections = async () => {
      setIsLoading(true);
      await new Promise(resolve => setTimeout(resolve, 800));
      setReflections(MOCK_DETAILED_REFLECTIONS);
      setManualNotes(MOCK_DETAILED_REFLECTIONS.manual.personalNotes);
      setKeyTakeaways(MOCK_DETAILED_REFLECTIONS.manual.keyTakeaways);
      setConfidenceLevel(MOCK_DETAILED_REFLECTIONS.manual.confidenceLevel);
      setNextCallFocus(MOCK_DETAILED_REFLECTIONS.manual.nextCallFocus);
      setIsLoading(false);
    };
    loadReflections();
  }, [meetingId]);
  
  const handleAddTakeaway = () => {
    if (newTakeaway.trim()) {
      setKeyTakeaways(prev => [...prev, newTakeaway.trim()]);
      setNewTakeaway('');
    }
  };
  
  const handleRemoveTakeaway = (index: number) => {
    setKeyTakeaways(prev => prev.filter((_, i) => i !== index));
  };
  
  const handleSave = async () => {
    setIsSaving(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsSaving(false);
    // Show success toast
  };
  
  const handleRegenerate = async () => {
    setIsRegenerating(true);
    await new Promise(resolve => setTimeout(resolve, 2000));
    setIsRegenerating(false);
    // Reload reflections
  };
  
  if (isLoading) {
    return <Loader text="Loading reflections..." />;
  }
  
  if (!reflections || !meeting) {
    return <div className="form-error">Reflections not found</div>;
  }
  
  const getHealthScoreClass = (score: number) => {
    if (score >= 70) return 'high';
    if (score >= 40) return 'medium';
    return 'low';
  };
  
  return (
    <div className="reflections-detail-container">
      <BackButton to="/client-calls/reflections" label="Back to Reflections" />
      <PageHeader
        title={meeting.meetingName}
        subtitle={`${meeting.company} • ${new Date(meeting.date).toLocaleDateString()}`}
      />
      
      <div className="reflections-grid">
        {/* AI Generated Reflections Panel */}
        <div className="reflections-panel">
          <div className="reflections-panel-header">
            <h3>🤖 AI-Generated Insights</h3>
            <button
              className="regenerate-btn"
              onClick={handleRegenerate}
              disabled={isRegenerating}
            >
              {isRegenerating ? '⟳ Regenerating...' : '⟳ Regenerate'}
            </button>
          </div>
          
          <div className="reflections-panel-body">
            {/* Health Score & Status */}
            <div className="reflection-stat-bar">
              <div className="reflection-stat">
                <div className="reflection-stat-label">Deal Health</div>
                <div className={`reflection-stat-value ${getHealthScoreClass(reflections.aiGenerated.dealHealthScore)}`}>
                  {reflections.aiGenerated.dealHealthScore}%
                </div>
              </div>
              <div className="reflection-stat">
                <div className="reflection-stat-label">Relationship</div>
                <span className={`relationship-badge ${reflections.aiGenerated.relationshipStatus}`}>
                  {reflections.aiGenerated.relationshipStatus}
                </span>
              </div>
            </div>
            
            {/* What Went Well */}
            <div className="reflection-section">
              <h4 className="reflection-section-title success">✓ What Went Well</h4>
              <ul>
                {reflections.aiGenerated.whatWentWell.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
            
            {/* Areas for Improvement */}
            <div className="reflection-section">
              <h4 className="reflection-section-title warning">⚠ Areas for Improvement</h4>
              <ul>
                {reflections.aiGenerated.areasForImprovement.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
            
            {/* Competitor Insights */}
            {reflections.aiGenerated.competitorInsights.length > 0 && (
              <div className="reflection-section">
                <h4 className="reflection-section-title info">🏢 Competitor Insights</h4>
                <ul>
                  {reflections.aiGenerated.competitorInsights.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {/* Risk Factors */}
            {reflections.aiGenerated.riskFactors.length > 0 && (
              <div className="reflection-section">
                <h4 className="reflection-section-title error">🚩 Risk Factors</h4>
                <ul>
                  {reflections.aiGenerated.riskFactors.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {/* Recommended Follow-ups */}
            <div className="reflection-section">
              <h4 className="reflection-section-title" style={{ color: 'var(--color-gray-800)' }}>
                📋 Recommended Follow-ups
              </h4>
              {reflections.aiGenerated.recommendedFollowUps.map((item, idx) => (
                <div key={idx} className={`follow-up-item ${item.priority}`}>
                  <span className={`follow-up-priority ${item.priority}`}>{item.priority}</span>
                  <span>{item.action}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        {/* Manual Reflections Panel */}
        <div className="reflections-panel">
          <div className="reflections-panel-header">
            <h3>✏️ Your Notes</h3>
            <button
              className="save-notes-btn"
              onClick={handleSave}
              disabled={isSaving}
            >
              {isSaving ? 'Saving...' : 'Save Notes'}
            </button>
          </div>
          
          <div className="reflections-panel-body">
            {/* Personal Notes */}
            <div className="manual-notes-section">
              <label className="manual-notes-label">Personal Notes</label>
              <textarea
                className="manual-notes-textarea"
                value={manualNotes}
                onChange={(e) => setManualNotes(e.target.value)}
                placeholder="Your thoughts and observations from the meeting..."
                rows={4}
              />
            </div>
            
            {/* Key Takeaways */}
            <div className="manual-notes-section">
              <label className="manual-notes-label">Key Takeaways</label>
              <div className="list-input-wrapper">
                <input
                  type="text"
                  value={newTakeaway}
                  onChange={(e) => setNewTakeaway(e.target.value)}
                  placeholder="Add a takeaway..."
                  onKeyDown={(e) => e.key === 'Enter' && handleAddTakeaway()}
                />
                <button className="btn-secondary" onClick={handleAddTakeaway} style={{ padding: '0.5rem 1rem' }}>
                  Add
                </button>
              </div>
              <div className="list-items">
                {keyTakeaways.map((item, idx) => (
                  <div key={idx} className="list-item">
                    <span>{item}</span>
                    <button className="list-item-remove" onClick={() => handleRemoveTakeaway(idx)}>
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Confidence Level */}
            <div className="manual-notes-section">
              <label className="manual-notes-label">Deal Confidence</label>
              <div className="confidence-selector">
                {(['low', 'medium', 'high'] as const).map((level) => (
                  <button
                    key={level}
                    className={`confidence-btn ${confidenceLevel === level ? 'selected' : ''}`}
                    onClick={() => setConfidenceLevel(level)}
                  >
                    {level}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Next Call Focus */}
            <div className="manual-notes-section">
              <label className="manual-notes-label">Focus for Next Call</label>
              <textarea
                className="manual-notes-textarea"
                value={nextCallFocus}
                onChange={(e) => setNextCallFocus(e.target.value)}
                placeholder="What should you focus on in the next conversation?"
                rows={3}
              />
            </div>
          </div>
        </div>
      </div>
      
      <div className="action-buttons">
        <button className="btn-primary" onClick={() => navigate(`/client-calls/summary/${meetingId}`)}>
          View Full Summary
        </button>
        <button className="btn-secondary" onClick={() => navigate('/client-calls')}>
          Back to Client Calls
        </button>
      </div>
    </div>
  );
};

// Main component
export const PostCallReflections = () => {
  const { meetingId } = useParams<{ meetingId: string }>();
  
  if (meetingId) {
    return <ReflectionsDetail meetingId={meetingId} />;
  }
  
  return <ReflectionsList />;
};
