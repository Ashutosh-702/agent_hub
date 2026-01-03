import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PageHeader, BackButton, Loader } from '../shared';

// Mock battlecard data
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
  const [battlecard, setBattlecard] = useState<typeof MOCK_BATTLECARD | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [copiedSection, setCopiedSection] = useState<string | null>(null);
  
  useEffect(() => {
    const loadBattlecard = async () => {
      setIsLoading(true);
      await new Promise(resolve => setTimeout(resolve, 1200));
      setBattlecard(MOCK_BATTLECARD);
      setIsLoading(false);
    };
    loadBattlecard();
  }, [battlecardId]);
  
  const copySection = (sectionName: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedSection(sectionName);
    setTimeout(() => setCopiedSection(null), 2000);
  };
  
  if (isLoading) {
    return <Loader text="Generating battlecard..." />;
  }
  
  if (!battlecard) {
    return <div className="form-error">Battlecard not found</div>;
  }
  
  return (
    <div className="battlecard-container">
      <BackButton to="/client-calls/prep" label="Back to Prep" />
      
      <div className="battlecard-header">
        <div>
          <PageHeader
            title={`Battlecard: ${battlecard.company.name}`}
            subtitle={`${battlecard.meetingType.charAt(0).toUpperCase() + battlecard.meetingType.slice(1)} Meeting • Generated ${new Date(battlecard.createdAt).toLocaleDateString()}`}
            variant="inline"
          />
        </div>
        <button className="btn-primary" onClick={() => navigate('/client-calls/start')}>
          Start Meeting
        </button>
      </div>
      
      <div className="battlecard-grid">
        {/* Company Overview */}
        <div className="battlecard-section">
          <div className="battlecard-section-header">
            <span className="icon">{SectionIcons.company}</span>
            <h3>Company Overview</h3>
          </div>
          <div className="battlecard-section-body">
            <p><strong>{battlecard.company.name}</strong></p>
            <p>{battlecard.company.industry} • {battlecard.company.size}</p>
            <p>HQ: {battlecard.company.headquarters}</p>
            <p>Revenue: {battlecard.company.annualRevenue}</p>
          </div>
        </div>
        
        {/* Meeting Attendees */}
        <div className="battlecard-section">
          <div className="battlecard-section-header">
            <span className="icon">{SectionIcons.contacts}</span>
            <h3>Meeting Attendees</h3>
          </div>
          <div className="battlecard-section-body">
            {battlecard.contacts.map((contact, idx) => (
              <div key={idx} style={{ marginBottom: '1rem' }}>
                <p style={{ margin: 0 }}><strong>{contact.name}</strong> - {contact.title}</p>
                <p style={{ margin: '0.25rem 0', fontSize: '0.875rem', color: 'var(--color-gray-500)' }}>
                  {contact.persona}
                </p>
                <p style={{ margin: 0, fontSize: '0.875rem' }}>
                  <em>Style:</em> {contact.communicationStyle}
                </p>
              </div>
            ))}
          </div>
        </div>
        
        {/* Company Research */}
        <div className="battlecard-section">
          <div className="battlecard-section-header">
            <span className="icon">{SectionIcons.research}</span>
            <h3>Company Research</h3>
          </div>
          <div className="battlecard-section-body">
            <p><strong>Recent News:</strong></p>
            <ul>
              {battlecard.companyResearch.recentNews.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
            <p><strong>Known Challenges:</strong></p>
            <ul>
              {battlecard.companyResearch.knownChallenges.map((item, idx) => (
                <li key={idx} style={{ color: 'var(--color-warning)' }}>{item}</li>
              ))}
            </ul>
            <p><strong>Tech Stack:</strong> {battlecard.companyResearch.techStack.join(', ')}</p>
          </div>
        </div>
        
        {/* Product Fit */}
        <div className="battlecard-section">
          <div className="battlecard-section-header">
            <span className="icon">{SectionIcons.products}</span>
            <h3>Product Fit</h3>
          </div>
          <div className="battlecard-section-body">
            {Object.entries(battlecard.productFit).map(([product, fit]) => (
              <div key={product} style={{ marginBottom: '1rem' }}>
                <p><strong>{product}</strong> - <span style={{ color: 'var(--color-success)' }}>High Fit</span></p>
                <ul>
                  {fit.keyFeatures.map((feature, idx) => (
                    <li key={idx}>{feature}</li>
                  ))}
                </ul>
                <p style={{ fontSize: '0.875rem', color: 'var(--color-primary)', fontWeight: 500 }}>
                  💡 {fit.competitiveAdvantage}
                </p>
              </div>
            ))}
          </div>
        </div>
        
        {/* Talking Points */}
        <div className="battlecard-section" style={{ gridColumn: 'span 2' }}>
          <div className="battlecard-section-header">
            <span className="icon">{SectionIcons.talking}</span>
            <h3>Talking Points</h3>
          </div>
          <div className="battlecard-section-body">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1.5rem' }}>
              <div>
                <p style={{ fontWeight: 600, color: 'var(--color-success)' }}>🎯 Opening</p>
                <ul>
                  {battlecard.talkingPoints.opening.map((point, idx) => (
                    <li key={idx}>{point}</li>
                  ))}
                </ul>
              </div>
              <div>
                <p style={{ fontWeight: 600, color: 'var(--color-info)' }}>❓ Discovery Questions</p>
                <ul>
                  {battlecard.talkingPoints.discovery.map((point, idx) => (
                    <li key={idx}>{point}</li>
                  ))}
                </ul>
              </div>
              <div>
                <p style={{ fontWeight: 600, color: 'var(--color-primary)' }}>✨ Value Props</p>
                <ul>
                  {battlecard.talkingPoints.valueProps.map((point, idx) => (
                    <li key={idx}>{point}</li>
                  ))}
                </ul>
              </div>
            </div>
            <button
              className="copy-section-btn"
              onClick={() => copySection('talking', [
                'OPENING:',
                ...battlecard.talkingPoints.opening,
                '',
                'DISCOVERY QUESTIONS:',
                ...battlecard.talkingPoints.discovery,
                '',
                'VALUE PROPS:',
                ...battlecard.talkingPoints.valueProps,
              ].join('\n'))}
            >
              {copiedSection === 'talking' ? '✓ Copied!' : '📋 Copy All Talking Points'}
            </button>
          </div>
        </div>
        
        {/* Objection Handlers */}
        <div className="battlecard-section" style={{ gridColumn: 'span 2' }}>
          <div className="battlecard-section-header">
            <span className="icon">{SectionIcons.objections}</span>
            <h3>Objection Handlers</h3>
          </div>
          <div className="battlecard-section-body">
            {battlecard.objectionHandlers.map((handler, idx) => (
              <div key={idx} className="objection-item">
                <p className="objection-text">"{handler.objection}"</p>
                <p className="objection-response">
                  <strong>Response:</strong> {handler.response}
                </p>
                <p style={{ fontSize: '0.75rem', color: 'var(--color-gray-500)', margin: '0.5rem 0 0' }}>
                  📊 Evidence: {handler.evidence}
                </p>
              </div>
            ))}
            <button
              className="copy-section-btn"
              onClick={() => copySection('objections', battlecard.objectionHandlers.map(h =>
                `Q: ${h.objection}\nA: ${h.response}\nEvidence: ${h.evidence}`
              ).join('\n\n'))}
            >
              {copiedSection === 'objections' ? '✓ Copied!' : '📋 Copy All Objection Handlers'}
            </button>
          </div>
        </div>
        
        {/* Competitor Comparison */}
        <div className="battlecard-section">
          <div className="battlecard-section-header">
            <span className="icon">{SectionIcons.competitors}</span>
            <h3>Competitor Intel</h3>
          </div>
          <div className="battlecard-section-body">
            {Object.entries(battlecard.competitorComparison).map(([competitor, intel]) => (
              <div key={competitor} style={{ marginBottom: '1rem' }}>
                <p><strong>{competitor}</strong></p>
                <p style={{ fontSize: '0.875rem', color: 'var(--color-error)' }}>
                  Their strength: {intel.theirStrength}
                </p>
                <p style={{ fontSize: '0.875rem', color: 'var(--color-success)' }}>
                  Our advantage: {intel.ourAdvantage}
                </p>
                <p style={{ fontSize: '0.875rem', color: 'var(--color-primary)' }}>
                  💡 {intel.counterPoint}
                </p>
              </div>
            ))}
          </div>
        </div>
        
        {/* Next Steps */}
        <div className="battlecard-section">
          <div className="battlecard-section-header">
            <span className="icon">{SectionIcons.nextSteps}</span>
            <h3>Suggested Next Steps</h3>
          </div>
          <div className="battlecard-section-body">
            <ol>
              {battlecard.nextSteps.map((step, idx) => (
                <li key={idx}>{step}</li>
              ))}
            </ol>
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
