import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PageHeader, BackButton, Loader } from '../shared';

// Mock battlecard data (kept for reference, not used in production)
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const MOCK_BATTLECARD = {
  id: 'bc-1',
  company: {
    name: 'Acme Retail Ltd',
    industry: 'E-commerce & Retail',
    size: '500-1000 employees',
    website: 'www.acme-retail.com',
    headquarters: 'Mumbai, India',
    annualRevenue: '₹500Cr - ₹1000Cr',
  },
  meetingType: 'discovery',
  contacts: [
    {
      name: 'Rajesh Kumar',
      title: 'VP Operations',
      persona: 'Operations Leader',
      priorities: ['Efficiency', 'Cost reduction', 'Scalability'],
      communicationStyle: 'Data-driven, appreciates concrete ROI metrics',
    },
    {
      name: 'Priya Sharma',
      title: 'Chief Technology Officer',
      persona: 'Technical Decision Maker',
      priorities: ['Integration capabilities', 'Security', 'Modern architecture'],
      communicationStyle: 'Technical depth, prefers architectural discussions',
    },
  ],
  companyResearch: {
    recentNews: [
      'Announced expansion to 50 new retail locations (Q4 2025)',
      'Partnership with major fashion brands for exclusive lines',
      'New warehouse facility in Bengaluru opening soon',
    ],
    knownChallenges: [
      'Inventory discrepancies causing 15% order cancellation rate',
      'Manual processes in warehouse operations',
      'Lack of real-time visibility across channels',
      'Legacy OMS struggling with omnichannel requirements',
    ],
    competitors: ['Unicommerce', 'Increff', 'Vinculum'],
    techStack: ['Shopify', 'Custom ERP', 'SAP (partial)'],
  },
  products: ['Fynd OMS', 'Fynd WMS'],
  productFit: {
    'Fynd OMS': {
      relevance: 'High',
      keyFeatures: [
        'Real-time inventory sync across all channels',
        'Intelligent order routing for faster fulfillment',
        'Omnichannel capabilities (BOPIS, ship-from-store)',
        'Pre-built Shopify integration',
      ],
      competitiveAdvantage: 'Only solution with native omnichannel + WMS integration',
    },
    'Fynd WMS': {
      relevance: 'High',
      keyFeatures: [
        'Mobile-first warehouse operations',
        'Zone-based picking optimization',
        'Real-time inventory tracking',
        'Seamless OMS integration',
      ],
      competitiveAdvantage: 'Unified platform reduces implementation complexity',
    },
  },
  talkingPoints: {
    opening: [
      'Congratulations on the upcoming expansion to 50+ stores - exciting growth!',
      'We\'ve helped similar retailers like Fashion Retail Co achieve 40% reduction in order cancellations',
      'I\'d love to understand more about your current fulfillment challenges',
    ],
    discovery: [
      'What\'s driving the urgency to address these challenges now?',
      'How are inventory discrepancies impacting your customer experience?',
      'What does success look like for this project?',
      'Who else would be involved in evaluating and implementing a solution?',
      'What\'s your timeline for making a decision?',
    ],
    valueProps: [
      'Reduce order cancellations by up to 40% with real-time inventory accuracy',
      'Enable ship-from-store to increase delivery speed and reduce costs',
      'Single platform for OMS + WMS means faster implementation and unified data',
      'API-first architecture integrates seamlessly with your existing Shopify setup',
    ],
  },
  objectionHandlers: [
    {
      objection: 'We\'re concerned about migration complexity from our legacy system',
      response: 'We use a phased migration approach - many clients run in parallel for 2-4 weeks. Our dedicated implementation team has handled 50+ similar migrations. We can share a detailed migration plan in the proposal.',
      evidence: 'Fashion Retail Co completed migration in 6 weeks with zero downtime',
    },
    {
      objection: 'How does this integrate with our custom ERP?',
      response: 'Our API-first architecture means we can integrate with any ERP. We have pre-built connectors for SAP and a flexible webhook system. Our solutions team can do a quick technical assessment.',
      evidence: 'Successfully integrated with 15+ custom ERPs across clients',
    },
    {
      objection: 'Your pricing seems higher than competitors',
      response: 'When you factor in the unified OMS + WMS platform, you\'re actually saving on multiple vendor costs, integration overhead, and ongoing maintenance. The TCO is typically 20-30% lower.',
      evidence: 'Happy to build an ROI model with your specific metrics',
    },
    {
      objection: 'We need to see it work at our scale first',
      response: 'Absolutely understand. We offer a pilot program where you can test with a subset of stores before full rollout. No long-term commitment required for the pilot.',
      evidence: 'Most enterprise clients start with a 3-store pilot',
    },
  ],
  competitorComparison: {
    Unicommerce: {
      theirStrength: 'Strong marketplace integrations',
      ourAdvantage: 'Native WMS + omnichannel capabilities they lack',
      counterPoint: 'If they mention Unicommerce, highlight our ship-from-store and unified warehouse management',
    },
    Increff: {
      theirStrength: 'Good inventory planning features',
      ourAdvantage: 'End-to-end fulfillment, not just inventory',
      counterPoint: 'Increff focuses on planning; we handle the entire order lifecycle',
    },
  },
  nextSteps: [
    'Schedule a technical deep-dive with IT team',
    'Share architecture document and integration capabilities',
    'Provide customer references in retail industry',
    'Propose pilot program scope and timeline',
  ],
  createdAt: new Date().toISOString(),
};

// Section icons
const SectionIcons: Record<string, string> = {
  company: '🏢',
  contacts: '👥',
  research: '🔍',
  products: '📦',
  talking: '💬',
  objections: '⚠️',
  competitors: '🏆',
  nextSteps: '➡️',
};

export const BattlecardView = () => {
  const { battlecardId } = useParams<{ battlecardId: string }>();
  const navigate = useNavigate();
  const [battlecard, setBattlecard] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [copiedSection, setCopiedSection] = useState<string | null>(null);
  
  useEffect(() => {
    const loadBattlecard = async () => {
      if (!battlecardId) return;
      
      setIsLoading(true);
      try {
        // Fetch meeting to get battlecard
        const res = await fetch(`/api/v1/meetings/${battlecardId}`);
        const data = await res.json();
        
        if (data.success) {
          const meeting = data.data;
          if (meeting.battlecard) {
            setBattlecard(meeting.battlecard);
          } else {
            // Generate battlecard if not exists
            await generateBattlecard();
          }
        }
      } catch (error) {
        console.error('Error loading battlecard:', error);
      } finally {
        setIsLoading(false);
      }
    };
    loadBattlecard();
  }, [battlecardId]);
  
  const generateBattlecard = async () => {
    if (!battlecardId) return;
    
    setIsGenerating(true);
    try {
      const res = await fetch(`/api/v1/meetings/${battlecardId}/battlecard`, {
        method: 'POST',
      });
      const data = await res.json();
      
      if (data.success) {
        setBattlecard(data.data);
      }
    } catch (error) {
      console.error('Error generating battlecard:', error);
    } finally {
      setIsGenerating(false);
    }
  };
  
  const copySection = (sectionName: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedSection(sectionName);
    setTimeout(() => setCopiedSection(null), 2000);
  };
  
  if (isLoading || isGenerating) {
    return <Loader text={isGenerating ? "Generating battlecard..." : "Loading battlecard..."} />;
  }
  
  if (!battlecard) {
    return (
      <div className="battlecard-container">
        <BackButton to="/client-calls/prep" label="Back to Prep" />
        <div className="form-error" style={{ margin: '2rem' }}>
          <p>Battlecard not found</p>
          <button className="btn-primary" onClick={generateBattlecard} style={{ marginTop: '1rem' }}>
            Generate Battlecard
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="battlecard-container">
      <BackButton to="/client-calls/prep" label="Back to Prep" />
      
      <div className="battlecard-header">
        <div>
          <PageHeader
            title={`Battlecard: ${battlecard.company_snapshot?.title || 'Meeting Preparation'}`}
            subtitle={`Generated ${battlecard.generated_at ? new Date(battlecard.generated_at).toLocaleDateString() : 'Just now'}`}
            variant="inline"
          />
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn-secondary" onClick={generateBattlecard} disabled={isGenerating}>
            {isGenerating ? 'Regenerating...' : '⟳ Regenerate'}
          </button>
          <button className="btn-primary" onClick={() => navigate('/client-calls/start')}>
            Start Meeting
          </button>
        </div>
      </div>
      
      <div className="battlecard-grid">
        {/* Company Overview */}
        <div className="battlecard-section">
          <div className="battlecard-section-header">
            <span className="icon">{SectionIcons.company}</span>
            <h3>Company Overview</h3>
          </div>
          <div className="battlecard-section-body">
            {battlecard.company_snapshot ? (
              <>
                <div dangerouslySetInnerHTML={{ __html: battlecard.company_snapshot.content?.replace(/\n/g, '<br/>') || '' }} />
                {battlecard.company_snapshot.bullet_points && battlecard.company_snapshot.bullet_points.length > 0 && (
                  <ul style={{ marginTop: '0.5rem' }}>
                    {battlecard.company_snapshot.bullet_points.map((point: string, idx: number) => (
                      <li key={idx}>{point}</li>
                    ))}
                  </ul>
                )}
              </>
            ) : (
              <p>Company overview will be generated from deep research</p>
            )}
          </div>
        </div>
        
        {/* Meeting Attendees */}
        <div className="battlecard-section">
          <div className="battlecard-section-header">
            <span className="icon">{SectionIcons.contacts}</span>
            <h3>Meeting Attendees</h3>
          </div>
          <div className="battlecard-section-body">
            {battlecard.contact_snapshot ? (
              <>
                <div dangerouslySetInnerHTML={{ __html: battlecard.contact_snapshot.content?.replace(/\n/g, '<br/>') || '' }} />
                {battlecard.contact_snapshot.bullet_points && battlecard.contact_snapshot.bullet_points.length > 0 && (
                  <ul style={{ marginTop: '0.5rem' }}>
                    {battlecard.contact_snapshot.bullet_points.map((point: string, idx: number) => (
                      <li key={idx}>{point}</li>
                    ))}
                  </ul>
                )}
              </>
            ) : (
              <p style={{ fontSize: '0.875rem', color: 'var(--color-gray-500)' }}>
                Contact information will be generated from contact data
              </p>
            )}
          </div>
        </div>
        
        {/* Company Research */}
        <div className="battlecard-section">
          <div className="battlecard-section-header">
            <span className="icon">{SectionIcons.research}</span>
            <h3>Company Research</h3>
          </div>
          <div className="battlecard-section-body">
            {battlecard.company_snapshot ? (
              <>
                <p><strong>Recent News & Signals:</strong></p>
                <p style={{ fontSize: '0.875rem', color: 'var(--color-gray-600)' }}>
                  Recent news and important signals will appear here from deep research
                </p>
                <p><strong>Key Initiatives:</strong></p>
                <p style={{ fontSize: '0.875rem', color: 'var(--color-gray-600)' }}>
                  Key initiatives will be extracted from company research
                </p>
              </>
            ) : (
              <p style={{ fontSize: '0.875rem', color: 'var(--color-gray-500)' }}>
                Company research will be generated from deep research pipeline
              </p>
            )}
          </div>
        </div>
        
        {/* Product Fit */}
        <div className="battlecard-section">
          <div className="battlecard-section-header">
            <span className="icon">{SectionIcons.products}</span>
            <h3>Product Fit</h3>
          </div>
          <div className="battlecard-section-body">
            {battlecard.why_now_product_fit ? (
              <>
                <div dangerouslySetInnerHTML={{ __html: battlecard.why_now_product_fit.content?.replace(/\n/g, '<br/>') || '' }} />
                {battlecard.why_now_product_fit.bullet_points && battlecard.why_now_product_fit.bullet_points.length > 0 && (
                  <ul style={{ marginTop: '0.5rem' }}>
                    {battlecard.why_now_product_fit.bullet_points.map((point: string, idx: number) => (
                      <li key={idx}>{point}</li>
                    ))}
                  </ul>
                )}
              </>
            ) : (
              <p style={{ fontSize: '0.875rem', color: 'var(--color-gray-500)' }}>
                Product fit analysis will be generated based on company research and product knowledge
              </p>
            )}
          </div>
        </div>
        
        {/* Talking Points */}
        <div className="battlecard-section" style={{ gridColumn: 'span 2' }}>
          <div className="battlecard-section-header">
            <span className="icon">{SectionIcons.talking}</span>
            <h3>Talking Points</h3>
          </div>
          <div className="battlecard-section-body">
            {battlecard.talking_points && battlecard.talking_points.length > 0 ? (
              <>
                <ul>
                  {battlecard.talking_points.map((point: string, idx: number) => (
                    <li key={idx}>{point}</li>
                  ))}
                </ul>
                <button
                  className="copy-section-btn"
                  onClick={() => copySection('talking', battlecard.talking_points.join('\n'))}
                >
                  {copiedSection === 'talking' ? '✓ Copied!' : '📋 Copy All Talking Points'}
                </button>
              </>
            ) : (
              <p style={{ fontSize: '0.875rem', color: 'var(--color-gray-500)' }}>
                Talking points will be AI-generated based on company research and products
              </p>
            )}
          </div>
        </div>
        
        {/* Objection Handlers */}
        <div className="battlecard-section" style={{ gridColumn: 'span 2' }}>
          <div className="battlecard-section-header">
            <span className="icon">{SectionIcons.objections}</span>
            <h3>Objection Handlers</h3>
          </div>
          <div className="battlecard-section-body">
            {battlecard.likely_objections && battlecard.likely_objections.length > 0 ? (
              <>
                {battlecard.likely_objections.map((handler: any, idx: number) => (
                  <div key={idx} className="objection-item">
                    <p className="objection-text">"{handler.objection || handler.objection_text}"</p>
                    <p className="objection-response">
                      <strong>Response:</strong> {handler.response || handler.suggested_response}
                    </p>
                  </div>
                ))}
                <button
                  className="copy-section-btn"
                  onClick={() => copySection('objections', battlecard.likely_objections.map((h: any) =>
                    `Q: ${h.objection || h.objection_text}\nA: ${h.response || h.suggested_response}`
                  ).join('\n\n'))}
                >
                  {copiedSection === 'objections' ? '✓ Copied!' : '📋 Copy All Objection Handlers'}
                </button>
              </>
            ) : (
              <p style={{ fontSize: '0.875rem', color: 'var(--color-gray-500)' }}>
                Objection handlers will be AI-generated based on company situation and product knowledge
              </p>
            )}
          </div>
        </div>
        
        {/* Competitor Comparison */}
        <div className="battlecard-section">
          <div className="battlecard-section-header">
            <span className="icon">{SectionIcons.competitors}</span>
            <h3>Competitor Intel</h3>
          </div>
          <div className="battlecard-section-body">
            {battlecard.key_risks && battlecard.key_risks.length > 0 ? (
              <>
                <p><strong>Competitive Intelligence:</strong></p>
                <ul>
                  {battlecard.key_risks.map((risk: string, idx: number) => (
                    <li key={idx}>{risk}</li>
                  ))}
                </ul>
              </>
            ) : (
              <p style={{ fontSize: '0.875rem', color: 'var(--color-gray-500)' }}>
                Competitor intelligence will be generated based on detected competitors and product knowledge
              </p>
            )}
          </div>
        </div>
        
        {/* Next Steps */}
        <div className="battlecard-section">
          <div className="battlecard-section-header">
            <span className="icon">{SectionIcons.nextSteps}</span>
            <h3>Suggested Next Steps</h3>
          </div>
          <div className="battlecard-section-body">
            {battlecard.suggested_next_steps && battlecard.suggested_next_steps.length > 0 ? (
              <ol>
                {battlecard.suggested_next_steps.map((step: string, idx: number) => (
                  <li key={idx}>{step}</li>
                ))}
              </ol>
            ) : (
              <p style={{ fontSize: '0.875rem', color: 'var(--color-gray-500)' }}>
                Next steps will be AI-generated based on deal stage and signals
              </p>
            )}
          </div>
        </div>
      </div>
      
      <div className="action-buttons">
        <button className="btn-success" onClick={() => navigate('/client-calls/start')}>
          Start Meeting Now
        </button>
        <button className="btn-secondary" onClick={() => window.print()}>
          🖨️ Print Battlecard
        </button>
      </div>
    </div>
  );
};
