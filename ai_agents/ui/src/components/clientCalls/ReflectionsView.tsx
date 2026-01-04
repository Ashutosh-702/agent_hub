import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PageHeader, BackButton, Loader } from '../shared';

interface RecommendedFollowUp {
  action: string;
  priority: 'high' | 'medium' | 'low';
  suggested_timeline?: string;
}

interface ProductCompanyScore {
  product_id: string;
  product_name: string;
  score: number;
  reasoning: string;
  key_strengths: string[];
  key_concerns: string[];
}

interface RedFlag {
  flag_name: string;
  evidence: string;
  confidence: number;
  context?: string;
}

interface AIReflections {
  generated_at?: string;
  what_went_well: string[];
  areas_for_improvement: string[];
  what_can_be_improved?: string[];
  key_learnings: string[];
  relationship_status?: string;
  deal_health_score?: number;
  recommended_follow_ups: RecommendedFollowUp[];
  competitive_positioning?: string;
  stakeholder_analysis?: string;
  risk_assessment: string[];
  product_company_scores?: ProductCompanyScore[];
  red_flags_detected?: RedFlag[];
  recommendations?: string[];
  worth_pursuing?: boolean;
  worth_pursuing_reasoning?: string;
}

interface ManualReflections {
  updated_at?: string;
  personal_notes?: string;
  what_went_well: string[];
  what_to_improve: string[];
  key_takeaways: string[];
  follow_up_commitments: string[];
  internal_action_items: string[];
  confidence_level?: string;
  next_call_focus?: string;
}

interface Meeting {
  id: string;
  meeting_name?: string;
  company_domain?: string;
  ended_at?: string;
  product_ids: string[];
  reflections?: {
    ai_generated?: AIReflections;
    manual?: ManualReflections;
  };
}

export const ReflectionsView = () => {
  const { meetingId } = useParams<{ meetingId: string }>();
  const navigate = useNavigate();
  
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  // Manual reflections form state
  const [personalNotes, setPersonalNotes] = useState('');
  const [whatWentWell, setWhatWentWell] = useState<string[]>([]);
  const [whatToImprove, setWhatToImprove] = useState<string[]>([]);
  const [keyTakeaways, setKeyTakeaways] = useState<string[]>([]);
  const [confidenceLevel, setConfidenceLevel] = useState<'low' | 'medium' | 'high' | ''>('');
  const [nextCallFocus, setNextCallFocus] = useState('');
  
  // Input state for list items
  const [newWentWell, setNewWentWell] = useState('');
  const [newToImprove, setNewToImprove] = useState('');
  const [newTakeaway, setNewTakeaway] = useState('');
  
  useEffect(() => {
    if (meetingId) {
      fetch(`/api/v1/meetings/${meetingId}`)
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            const m = data.data;
            setMeeting(m);
            
            // Initialize form with existing manual reflections
            const manual = m.reflections?.manual;
            if (manual) {
              setPersonalNotes(manual.personal_notes || '');
              setWhatWentWell(manual.what_went_well || []);
              setWhatToImprove(manual.what_to_improve || []);
              setKeyTakeaways(manual.key_takeaways || []);
              setConfidenceLevel(manual.confidence_level || '');
              setNextCallFocus(manual.next_call_focus || '');
            }
          }
        })
        .finally(() => setIsLoading(false));
    }
  }, [meetingId]);
  
  const handleRegenerate = async () => {
    setIsRegenerating(true);
    try {
      await fetch(`/api/v1/meetings/${meetingId}/reflections/generate`, { method: 'POST' });
      // Refresh meeting data
      const res = await fetch(`/api/v1/meetings/${meetingId}`);
      const data = await res.json();
      if (data.success) {
        setMeeting(data.data);
      }
    } finally {
      setIsRegenerating(false);
    }
  };
  
  const handleSaveManual = async () => {
    setIsSaving(true);
    try {
      await fetch(`/api/v1/meetings/${meetingId}/reflections/manual`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          personal_notes: personalNotes,
          what_went_well: whatWentWell,
          what_to_improve: whatToImprove,
          key_takeaways: keyTakeaways,
          confidence_level: confidenceLevel || undefined,
          next_call_focus: nextCallFocus || undefined,
        }),
      });
    } finally {
      setIsSaving(false);
    }
  };
  
  const getHealthScoreClass = (score?: number) => {
    if (!score) return '';
    if (score >= 70) return 'high';
    if (score >= 40) return 'medium';
    return 'low';
  };
  
  if (isLoading) {
    return <Loader text="Loading reflections..." />;
  }
  
  const ai = meeting?.reflections?.ai_generated;
  
  return (
    <div className="reflections-detail-container">
      <BackButton to="/client-calls/reflections" label="Back to Reflections" />
      
      <PageHeader 
        title={`Reflections: ${meeting?.meeting_name || meeting?.company_domain || 'Meeting'}`}
        subtitle={meeting?.ended_at ? new Date(meeting.ended_at).toLocaleString() : ''}
      />
      
      <div className="reflections-grid">
        {/* AI Reflections Panel */}
        <div className="reflections-panel">
          <div className="reflections-panel-header">
            <h3>🤖 AI Reflections</h3>
            <button
              className="regenerate-btn"
              onClick={handleRegenerate}
              disabled={isRegenerating}
            >
              {isRegenerating ? '⟳ Regenerating...' : '⟳ Regenerate'}
            </button>
          </div>
          
          <div className="reflections-panel-body">
            {!ai ? (
              <div className="reflections-empty">
                <div className="reflections-empty-icon">🤖</div>
                <h3>No AI reflections yet</h3>
                <p>Click Regenerate to generate insights</p>
                <button
                  className="btn-primary"
                  onClick={handleRegenerate}
                  style={{ marginTop: '1rem' }}
                >
                  Generate Now
                </button>
              </div>
            ) : (
              <>
                {/* Health Score & Status */}
                <div className="reflection-stat-bar">
                  {ai.deal_health_score !== undefined && (
                    <div className="reflection-stat">
                      <div className="reflection-stat-label">Deal Health</div>
                      <div className={`reflection-stat-value ${getHealthScoreClass(ai.deal_health_score)}`}>
                        {ai.deal_health_score}%
                      </div>
                    </div>
                  )}
                  {ai.relationship_status && (
                    <div className="reflection-stat">
                      <div className="reflection-stat-label">Relationship</div>
                      <span className={`relationship-badge ${ai.relationship_status.toLowerCase()}`}>
                        {ai.relationship_status}
                      </span>
                    </div>
                  )}
                </div>
                
                {/* What Went Well */}
                {ai.what_went_well?.length > 0 && (
                  <div className="reflection-section">
                    <h4 className="reflection-section-title success">✓ What Went Well</h4>
                    <ul>
                      {ai.what_went_well.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {/* Areas for Improvement */}
                {ai.areas_for_improvement?.length > 0 && (
                  <div className="reflection-section">
                    <h4 className="reflection-section-title warning">⚠ Areas for Improvement</h4>
                    <ul>
                      {ai.areas_for_improvement.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {/* Key Learnings */}
                {ai.key_learnings?.length > 0 && (
                  <div className="reflection-section">
                    <h4 className="reflection-section-title info">💡 Key Learnings</h4>
                    <ul>
                      {ai.key_learnings.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {/* Recommended Follow-ups */}
                {ai.recommended_follow_ups?.length > 0 && (
                  <div className="reflection-section">
                    <h4 className="reflection-section-title" style={{ color: 'var(--color-gray-800)' }}>
                      📋 Recommended Follow-ups
                    </h4>
                    {ai.recommended_follow_ups.map((fu, idx) => (
                      <div key={idx} className={`follow-up-item ${fu.priority}`}>
                        <span className={`follow-up-priority ${fu.priority}`}>{fu.priority}</span>
                        <div>
                          <div>{fu.action}</div>
                          {fu.suggested_timeline && (
                            <div style={{ fontSize: '0.8rem', color: 'var(--color-gray-500)' }}>
                              {fu.suggested_timeline}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Risk Assessment */}
                {ai.risk_assessment?.length > 0 && (
                  <div className="reflection-section">
                    <h4 className="reflection-section-title error">🚩 Risk Assessment</h4>
                    <ul>
                      {ai.risk_assessment.map((risk, idx) => (
                        <li key={idx}>{risk}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {/* Product x Company Scores */}
                {ai.product_company_scores && ai.product_company_scores.length > 0 && (
                  <div className="reflection-section">
                    <h4 className="reflection-section-title" style={{ color: 'var(--color-primary)' }}>
                      📊 Product x Company Fit Scores
                    </h4>
                    <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
                      {ai.product_company_scores.map((score, idx) => {
                        const scoreClass = score.score >= 70 ? 'high' : score.score >= 50 ? 'medium' : 'low';
                        return (
                          <div key={idx} style={{
                            padding: '1rem',
                            border: '1px solid var(--color-gray-200)',
                            borderRadius: 'var(--border-radius-md)',
                            background: 'var(--color-gray-50)',
                          }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                              <strong>{score.product_name}</strong>
                              <span className={`reflection-stat-value ${scoreClass}`} style={{ fontSize: '1.25rem' }}>
                                {score.score}/100
                              </span>
                            </div>
                            <p style={{ fontSize: '0.875rem', color: 'var(--color-gray-600)', marginBottom: '0.5rem' }}>
                              {score.reasoning}
                            </p>
                            {score.key_strengths.length > 0 && (
                              <div style={{ marginTop: '0.5rem' }}>
                                <strong style={{ fontSize: '0.875rem', color: 'var(--color-success)' }}>Strengths:</strong>
                                <ul style={{ fontSize: '0.875rem', marginTop: '0.25rem' }}>
                                  {score.key_strengths.map((s, i) => (
                                    <li key={i}>{s}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {score.key_concerns.length > 0 && (
                              <div style={{ marginTop: '0.5rem' }}>
                                <strong style={{ fontSize: '0.875rem', color: 'var(--color-warning)' }}>Concerns:</strong>
                                <ul style={{ fontSize: '0.875rem', marginTop: '0.25rem' }}>
                                  {score.key_concerns.map((c, i) => (
                                    <li key={i}>{c}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
                
                {/* Red Flags Detected */}
                {ai.red_flags_detected && ai.red_flags_detected.length > 0 && (
                  <div className="reflection-section">
                    <h4 className="reflection-section-title error">🚩 Red Flags Detected</h4>
                    <div style={{ display: 'grid', gap: '0.75rem' }}>
                      {ai.red_flags_detected.map((flag, idx) => (
                        <div key={idx} style={{
                          padding: '0.75rem',
                          background: 'var(--color-error-light)',
                          borderRadius: 'var(--border-radius-md)',
                          border: '1px solid var(--color-error)',
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                            <strong style={{ color: 'var(--color-error-dark)' }}>{flag.flag_name}</strong>
                            <span style={{ fontSize: '0.75rem', color: 'var(--color-gray-600)' }}>
                              {Math.round(flag.confidence * 100)}% confidence
                            </span>
                          </div>
                          <p style={{ fontSize: '0.875rem', fontStyle: 'italic', marginBottom: '0.25rem' }}>
                            "{flag.evidence}"
                          </p>
                          {flag.context && (
                            <p style={{ fontSize: '0.875rem', color: 'var(--color-gray-600)' }}>
                              {flag.context}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Recommendations */}
                {ai.recommendations && ai.recommendations.length > 0 && (
                  <div className="reflection-section">
                    <h4 className="reflection-section-title" style={{ color: 'var(--color-primary)' }}>
                      💡 Recommendations
                    </h4>
                    <ul>
                      {ai.recommendations.map((rec, idx) => (
                        <li key={idx}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {/* Worth Pursuing */}
                {ai.worth_pursuing !== undefined && (
                  <div className="reflection-section">
                    <h4 className="reflection-section-title" style={{ color: ai.worth_pursuing ? 'var(--color-success)' : 'var(--color-warning)' }}>
                      {ai.worth_pursuing ? '✅ Worth Pursuing' : '⚠️ Consider Deprioritizing'}
                    </h4>
                    {ai.worth_pursuing_reasoning && (
                      <p style={{ fontSize: '0.9rem', lineHeight: 1.6 }}>
                        {ai.worth_pursuing_reasoning}
                      </p>
                    )}
                  </div>
                )}
                
                {/* What Can Be Improved */}
                {ai.what_can_be_improved && ai.what_can_be_improved.length > 0 && (
                  <div className="reflection-section">
                    <h4 className="reflection-section-title warning">🔧 What Can Be Improved</h4>
                    <ul>
                      {ai.what_can_be_improved.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
        
        {/* Manual Reflections Panel */}
        <div className="reflections-panel">
          <div className="reflections-panel-header">
            <h3>✏️ Your Notes</h3>
            <button
              className="save-notes-btn"
              onClick={handleSaveManual}
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
                value={personalNotes}
                onChange={(e) => setPersonalNotes(e.target.value)}
                placeholder="Your thoughts and observations from the meeting..."
                rows={4}
              />
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
                placeholder="What to focus on in the next conversation..."
                rows={2}
              />
            </div>
            
            {/* What Went Well */}
            <div className="manual-notes-section">
              <label className="manual-notes-label">What Went Well</label>
              <div className="list-input-wrapper">
                <input
                  type="text"
                  value={newWentWell}
                  onChange={(e) => setNewWentWell(e.target.value)}
                  placeholder="Add item..."
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && newWentWell.trim()) {
                      setWhatWentWell(prev => [...prev, newWentWell.trim()]);
                      setNewWentWell('');
                    }
                  }}
                />
                <button 
                  className="btn-secondary" 
                  onClick={() => {
                    if (newWentWell.trim()) {
                      setWhatWentWell(prev => [...prev, newWentWell.trim()]);
                      setNewWentWell('');
                    }
                  }}
                  style={{ padding: '0.5rem 1rem' }}
                >
                  Add
                </button>
              </div>
              <div className="list-items">
                {whatWentWell.map((item, idx) => (
                  <div key={idx} className="list-item">
                    <span>{item}</span>
                    <button 
                      className="list-item-remove" 
                      onClick={() => setWhatWentWell(prev => prev.filter((_, i) => i !== idx))}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
            
            {/* What to Improve */}
            <div className="manual-notes-section">
              <label className="manual-notes-label">What to Improve</label>
              <div className="list-input-wrapper">
                <input
                  type="text"
                  value={newToImprove}
                  onChange={(e) => setNewToImprove(e.target.value)}
                  placeholder="Add item..."
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && newToImprove.trim()) {
                      setWhatToImprove(prev => [...prev, newToImprove.trim()]);
                      setNewToImprove('');
                    }
                  }}
                />
                <button 
                  className="btn-secondary" 
                  onClick={() => {
                    if (newToImprove.trim()) {
                      setWhatToImprove(prev => [...prev, newToImprove.trim()]);
                      setNewToImprove('');
                    }
                  }}
                  style={{ padding: '0.5rem 1rem' }}
                >
                  Add
                </button>
              </div>
              <div className="list-items">
                {whatToImprove.map((item, idx) => (
                  <div key={idx} className="list-item">
                    <span>{item}</span>
                    <button 
                      className="list-item-remove" 
                      onClick={() => setWhatToImprove(prev => prev.filter((_, i) => i !== idx))}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Key Takeaways */}
            <div className="manual-notes-section">
              <label className="manual-notes-label">Key Takeaways</label>
              <div className="list-input-wrapper">
                <input
                  type="text"
                  value={newTakeaway}
                  onChange={(e) => setNewTakeaway(e.target.value)}
                  placeholder="Add takeaway..."
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && newTakeaway.trim()) {
                      setKeyTakeaways(prev => [...prev, newTakeaway.trim()]);
                      setNewTakeaway('');
                    }
                  }}
                />
                <button 
                  className="btn-secondary" 
                  onClick={() => {
                    if (newTakeaway.trim()) {
                      setKeyTakeaways(prev => [...prev, newTakeaway.trim()]);
                      setNewTakeaway('');
                    }
                  }}
                  style={{ padding: '0.5rem 1rem' }}
                >
                  Add
                </button>
              </div>
              <div className="list-items">
                {keyTakeaways.map((item, idx) => (
                  <div key={idx} className="list-item">
                    <span>{item}</span>
                    <button 
                      className="list-item-remove" 
                      onClick={() => setKeyTakeaways(prev => prev.filter((_, i) => i !== idx))}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
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
