import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Select from 'react-select';
import { useCreateCampaignMutation } from '../store';
import lushaJson from '../assets/lusha_industry_config.json';
const bqCategories = [  "mining", "energy", "utilities", "hospitality", "media", "entertainment", "gaming", "sports",  "insurance", "banking", "finance", "fintech", "real estate", "education", "legal", "construction",  "retail", "ecommerce", "wholesale", "manufacturing", "logistics", "supply chain", "automotive", "biotech","fashion", "apparel", "beauty", "pharmaceutical", "chemicals", "defense", "aerospace", "cloud computing","artificial intelligence", "machine learning", "blockchain", "iot", "cybersecurity", "saas", "big data","data analytics", "erp", "crm", "cms", "robotics", "augmented reality", "virtual reality", "3d printing","5g", "digital twins", "biometrics", "edge computing", "computer vision", "speech recognition", "b2b","b2c", "d2c", "marketplace", "subscription", "on-demand", "freemium", "licensing", "outsourcing","franchise", "reseller", "aggregator", "consulting", "marketing", "advertising", "seo", "ppc","content marketing", "email marketing", "affiliate marketing", "influencer marketing", "customer service","tech support", "field service", "delivery", "installation", "training", "research", "ui design","ux design", "graphic design", "product management", "project management", "account management","data science", "machine intelligence", "computer science", "web development", "frontend", "backend","full stack", "qa", "devops", "infrastructure", "sre", "hr", "talent acquisition", "payroll","employee engagement", "compliance", "legal ops", "procurement", "finance ops", "fp&a","customer success", "sales enablement", "lead generation", "crm automation", "call center","crm systems", "product analytics", "session replay", "conversion rate", "churn prevention","loyalty programs", "payment gateway", "checkout optimization", "personalization engine","recommendation engine", "A/B testing", "multivariate testing", "data lake", "data warehouse","data mart", "etl", "elt", "pipeline orchestration", "notebooks", "BI tools", "dashboards","reporting", "OKRs", "KPIs", "north star metric", "unit economics", "CAC", "LTV", "retention","activation", "user onboarding", "feature flags", "experimentation", "feedback loops","interview scheduling", "ATS", "HRIS", "learning management", "security compliance", "ISO27001","SOC 2", "GDPR", "HIPAA", "PCI", "pen testing", "bug bounty", "vulnerability scanning","threat detection", "endpoint protection", "SIEM", "cloud security", "identity management","SSO", "MFA", "IAM", "zero trust", "network segmentation", "firewalls", "api gateway","rate limiting", "auth", "oauth", "jwt", "webhooks", "scheduling", "notifications","email infrastructure", "SMS", "push notifications", "in-app messaging", "chatbot","voice assistant", "natural language", "translation", "localization", "internationalization","geolocation", "maps", "places api", "routing", "ETA", "tracking", "fleet management","sensors", "hardware", "firmware", "bluetooth", "nfc", "qr code", "barcodes","inventory", "stock keeping", "pricing engine", "discount rules", "campaigns","voucher system", "gift cards", "wallet", "cashback", "referrals", "growth hacks","network effects", "virality", "influencer campaigns", "ugc", "reviews", "ratings","moderation", "spam detection", "toxicity", "image classification", "object detection","OCR", "document parsing", "pdf processing", "excel import", "csv export", "json apis","graphql", "rest apis", "rate limiting", "api keys", "token management", "permissions","roles", "audit logs", "billing", "invoicing", "tax", "gst", "vat", "accounting","bookkeeping", "audit", "legal", "notarization", "identity verification", "kyc","aml", "fraud detection", "risk scoring", "credit scoring", "insurance underwriting","claims", "policy management", "loan origination", "mortgages", "real estate listing","property management", "tenant screening", "lease signing", "rent collection","facility management", "maintenance requests", "smart locks", "access control","surveillance", "home automation", "climate control", "lighting", "voice control","scene management", "automation rules", "trigger events", "logging", "alerts","uptime monitoring", "status page", "incident response", "pager", "on-call","runbooks", "playbooks", "postmortems", "rca", "escalations", "sla tracking","user permissions", "session management", "cookie consent", "privacy policy","terms of use", "legal disclaimers", "dmca", "copyright", "trademark","patent", "ip strategy", "legal entity", "business registration","cap table", "equity management", "vesting", "esop", "fundraising","pitch deck", "data room", "term sheet", "safe", "convertible note","valuation", "dilution", "burn rate", "runway", "revenue model","pricing strategy", "customer segmentation", "target audience", "personas","user research", "usability testing", "click tracking", "heatmaps", "session recordings","interviews", "surveys", "net promoter score", "customer satisfaction","churn analysis", "cohort analysis", "funnel analysis", "retention curve","virality curve", "growth loops", "network analysis", "graph db","relational db", "nosql", "mongodb", "postgres", "mysql", "dynamodb","redis", "elastic search", "solr", "kafka", "rabbitmq", "sqs", "sns","pubsub", "event bus", "event sourcing", "cqrs", "command pattern","observer pattern", "factory pattern", "singleton", "builder","adapter", "proxy", "decorator", "chain of responsibility","mediator", "mvc", "mvvm", "clean architecture", "hexagonal architecture","domain driven design", "test driven development", "behavior driven development","unit testing", "integration testing", "e2e testing", "load testing", "performance testing","security testing", "accessibility", "wcag", "screen readers", "keyboard navigation","focus trap", "tab order", "semantic html", "aria labels", "contrast ratio","color blindness", "font scaling", "dark mode", "rtl support", "l10n", "i18n"];

const employeeCounts = ['1-10', '11-50', '51-200', '201-500','501-1000','1001-5000','5001-10000','10000+'];
const optionalQuestions = new Set([1,2]);
const regions = [
  'North America',
  'South America', 
  'Europe',
  'APAC',
  'EMEA',
  'Africa',
  'LATAM'

];

const countries = [ "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Ivory Coast", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe" ];

type IndustryStepProps = {
  form: string[];
  setForm: (v: string[]) => void;
  step: number;
};

function IndustryStep({ form, setForm, step }: IndustryStepProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>(
    () =>
      lushaJson.reduce((acc, main) => {
        acc[main.main_industry] = true;
        return acc;
      }, {} as Record<string, boolean>)
  );

  const q = searchQuery.trim().toLowerCase();
  const hasQuery = q.length > 0;

  const toggleCollapse = (mainName: string) => {
    setCollapsedGroups(prev => ({
      ...prev,
      [mainName]: !prev[mainName],
    }));
  };

  // Helpers for selection string
  const getSelected = () =>
    form[step] ? form[step].split(';').map(v => v.trim()).filter(Boolean) : [];

  const setSelected = (vals: string[]) => {
    const updated = [...form];
    updated[step] = vals.join(';');
    setForm(updated);
  };

  const toggleMain = (allSubs: string[]) => {
    const selected = getSelected();
    const allSelected = allSubs.length > 0 && allSubs.every(v => selected.includes(v));
    let updated = [...selected];
    if (allSelected) {
      updated = updated.filter(v => !allSubs.includes(v));
    } else {
      allSubs.forEach(v => {
        if (!updated.includes(v)) updated.push(v);
      });
    }
    setSelected(updated);
  };

  const toggleSub = (subValue: string) => {
    const selected = getSelected();
    let updated = [...selected];
    if (updated.includes(subValue)) {
      updated = updated.filter(v => v !== subValue);
    } else {
      updated.push(subValue);
    }
    setSelected(updated);
  };

  // Filtering mains by main name OR any sub name
  const mainsToShow = lushaJson.filter(main => {
    if (!hasQuery) return true;
    const mainMatch = main.main_industry.toLowerCase().includes(q);
    const subMatch = main.sub_industries.some((s: any) => s.value.toLowerCase().includes(q));
    return mainMatch || subMatch;
  });

  // Helper to highlight matches (optional; add CSS below)
  const highlight = (text: string) => {
    if (!hasQuery) return text;
    const idx = text.toLowerCase().indexOf(q);
    if (idx === -1) return text;
    const before = text.slice(0, idx);
    const match = text.slice(idx, idx + q.length);
    const after = text.slice(idx + q.length);
    return (
      <>
        {before}
        <span className="match">{match}</span>
        {after}
      </>
    );
  };

  return (
    <div className="industry-tree">
      <input
        type="text"
        className="industry-search"
        placeholder="Search industries..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
      />

      {mainsToShow.map(main => {
        // If searching, only show subs that match the query (unless main itself matches; then show all)
        const mainMatches = hasQuery && main.main_industry.toLowerCase().includes(q);
        const subs = hasQuery && !mainMatches
          ? main.sub_industries.filter((s: any) => s.value.toLowerCase().includes(q))
          : main.sub_industries;

        const selected = getSelected();
        const allSubs = subs.map((s: any) => s.value); // operate on visible subs when searching
        const allSubsSelected = allSubs.length > 0 && allSubs.every(v => selected.includes(v));
        const someSubsSelected = allSubs.some(v => selected.includes(v)) && !allSubsSelected;

        // While searching, auto-expand groups with matches
        const isCollapsed = hasQuery ? false : !!collapsedGroups[main.main_industry];

        return (
          <div key={main.main_industry} className="industry-group">
            <div
              className="industry-main"
              onClick={() => !hasQuery && toggleCollapse(main.main_industry)}
              title={hasQuery ? 'Expanded due to search' : 'Click to collapse/expand'}
            >
              <span className={`collapse-icon ${isCollapsed ? 'collapsed' : ''}`}>
                ▶
              </span>
              <input
                type="checkbox"
                ref={(el) => {
                  if (el) el.indeterminate = someSubsSelected;
                }}
                checked={allSubsSelected}
                onChange={(e) => {
                  e.stopPropagation();
                  // When not searching, toggle all actual subs in the group
                  // When searching, toggle only the visible subs (so UX matches what user sees)
                  const targetSubs = hasQuery
                    ? subs.map((s: any) => s.value)
                    : main.sub_industries.map((s: any) => s.value);
                  toggleMain(targetSubs);
                }}
              />
              <span>{highlight(main.main_industry)}</span>
            </div>

            {!isCollapsed && (
              <div className="industry-sub-list">
                {subs.map((sub: any) => (
                  <label key={sub.value} className="industry-sub">
                    <input
                      type="checkbox"
                      checked={selected.includes(sub.value)}
                      onChange={() => toggleSub(sub.value)}
                    />
                    <span>{highlight(sub.value)}</span>
                  </label>
                ))}
                {subs.length === 0 && hasQuery && (
                  <div className="industry-sub empty">No matching sub-industries</div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

const AutoResizeTextarea = ({
  value,
  onChange,
  placeholder,
  name,
}: {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  placeholder?: string;
  name: string;
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';

      const viewportHeight = window.innerHeight;
      const rect = el.getBoundingClientRect();
      const spaceBelow = viewportHeight - rect.top - 80;
      const idealHeight = Math.min(spaceBelow, Math.max(el.scrollHeight, 425));
      el.style.height = `${idealHeight}px`;
    }
  }, [value]);

  return (
    <textarea
      ref={textareaRef}
      className="text-input"
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      name={name}
      style={{ minHeight: '150px', resize: 'none' }}
    />
  );
};

const stepQuestions = [
  // SDR Company Relevance Prompt (7)
  // "Please provide a comprehensive and detailed outline of the relevance criteria for companies you aim to target. \n\n\n\n\n\n\nThe more specific and exhaustive your criteria, the higher the likelihood that we can identify and prioritize the most relevant companies for outreach.",
  "<div class='question-main'>Which industries or verticals are in scope?</div>", // step 7 // new 0
  "<div class='question-main'>Target company size by head-count?</div>", // step 8 //new 1
  "<div class='question-main'>Target company size by annual revenue?</div>", // step 9 (currency + min + max) //new 2
  "<div class='question-main'>Location</div>", // step 10 //new 3
  // new 4 5 6 7 8 9 
"<div class='question-main'>Please provide a comprehensive and detailed outline of the relevance criteria for companies you aim to target.</div><div class='question-subtitle'><span style='color:black;'>Example:  A relevant company must be a retailer that specializes in or has significant operations in selling or renting furniture, mattresses, or other heavy/bulky home goods items.</span><br/><br/>The more specific and exhaustive your criteria, the higher the likelihood that we can identify and prioritize the most relevant companies for outreach.</div>",
"<div class='question-main'>Please provide mandatory criterias that a company must have to qualify as a relevant company for outreach.</div><div class='question-subtitle'><span style='color:black;'>Example: Primary business must involve furniture, mattresses, or heavy/bulky home goods (sofas, beds, tables, chairs, wardrobes, appliances, outdoor furniture). Must have either e-commerce presence (online store with delivery capabilities) OR physical retail stores. Must serve end consumers (B2C model)</span><br/><br/>The more specific and exhaustive details you share, the higher will be the likelihood that we can identify and prioritize the most relevant companies for outreach.</div>",
"<div class='question-main'>Please share qualifying business models that are relevant to this outreach campaign.</div><div class='question-subtitle'><span style='color:black;'>Example: Direct furniture/mattress sales (online or in-store). Furniture rental services. Made-to-order/custom furniture providers. Hybrid models combining sales and rental.</span><br/><br/>The more specific and exhaustive details you share, the higher will be the likelihood that we can identify and prioritize the most relevant companies for outreach.</div>", 
"<div class='question-main'>What are the key positive indicators that signal a company is a strong fit for your target profile? Please specify any attributes, characteristics, or patterns that, if present, confirm the company aligns with what you're looking for.</div><div class='question-subtitle'><span style='color:black;'>Example: Multiple physical store locations. Established e-commerce platform with delivery logistics. Offers both ready-made and customizable options. Provides white-glove delivery or assembly services. Has dedicated sections for living room, bedroom, dining room furniture. Offers financing or rental plans. Serves metropolitan areas.</span><br/><br/>The more specific and exhaustive details you share, the higher will be the likelihood that we can identify and prioritize the most relevant companies for outreach.</div>", 
"<div class='question-main'>What are some exclusion criteria that the AI should apply to immediately disqualify a company as not relevant? Please specify any attributes or red flags that should lead to automatic exclusion.</div><div class='question-subtitle'><span style='color:black;'>Example: Pure B2B furniture suppliers without consumer presence. Interior design services without furniture sales. Pure marketplace platforms without own inventory. Companies focusing only on small home decor items without furniture. Office furniture specialists without home furniture offerings.</span><br/><br/>The more specific and exhaustive details you share, the higher will be the likelihood that we can identify and prioritize the most relevant companies for outreach.</div>", 
"<div class='question-main'>Please share a few reference companies along with the specific characteristics that make them relevant. This will help the AI better understand and identify similar companies during the targeting process.</div><div class='question-subtitle'><span style='color:black;'>Example: The Sleep Company: Mattress specialist with e-commerce focus. West Elm/Pottery Barn: Multi-location furniture retailers with strong e-commerce and physical presence. CityFurnish/Rentickle: Furniture rental services targeting urban consumers.</span><br/><br/>The more specific and exhaustive details you share, the higher will be the likelihood that we can identify and prioritize the most relevant companies for outreach.</div>",
// new 10
"<div class='question-main'>Do you have any additional validations that need to be ensured to ensure the company is relevant?</div><div class='question-subtitle'>Company is relevant if it meets ALL mandatory criteria AND demonstrates at least 2 positive indicators while avoiding ALL exclusion criteria.</div>",
  // Company Shortlisting (6)
  "<div class='question-main'>Keywords</div>", // step 11
  "<div class='question-main'>Categories</div>", // step 12

  // Persona Prompt (3)
  "<div class='question-main'>People to be searched</div><div class='question-subtitle'><span style='color:black;'>Example: VP Security, CISO, Security Architect.</span></div>", // step 13
  "<div class='question-main'>Seniority level of people you want to search</div><div class='question-subtitle'><span style='color:black;'>Example: Director+”, “IC OK if title contains 'Data Scientist'.</span></div>", // step 14
  "<div class='question-main'>Department(s) of people you want to search for</div>", // step 15

  // SDR Setup (3)
  "<div class='question-main'>Please share the email ID of the person against whom the contact should be saved in Hubspot</div>", // step 16
  "<div class='question-main'>Please share the name product for which you are targeting this outreach</div>", // step 17
  "<div class='question-main'>Please share the business team for whom you are initiating the outreach</div>", // step 18
  "<div class='question-main'>Please share your own email id</div>" //step 19
];

export const Form = () => {
  const navigate = useNavigate();
  const [createCampaign, { isLoading: isSubmitting }] = useCreateCampaignMutation();
  const [submittedId, setSubmittedId] = useState<string | null>(null);
  // Create form array with extra slots for currency, min revenue, max revenue, location type
  const [form, setForm] = useState<string[]>(Array(24).fill(''));
  const [step, setStep] = useState(0);
  const [submitted, setSubmitted] = useState(false);
  const [locationType, setLocationType] = useState<'region' | 'country' | ''>('');
  const progress = ((step + 1) / stepQuestions.length) * 100;

  const handleNext = () => {
    if (step < stepQuestions.length - 1) {
      let nextStep = step + 1;
      if (step === 10) {
        nextStep = 13;
      }
      setStep(nextStep);
    }
  };

  const handlePrevious = () => {
  if (step > 0) {
    let prevStep = step - 1;
    if (step === 13) {
      prevStep = 10;
    }
    setStep(prevStep);
  }
};

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const updated = [...form];
    updated[step] = e.target.value;
    setForm(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const payload = {
      web_prompt: [
        form[4] && `Comprehensive Outline: ${form[4]}`,
        form[5] && `Mandatory Criteria: ${form[5]}`,
        form[6] && `Relevant Business Models: ${form[6]}`,
        form[7] && `Positive Indicators: ${form[7]}`,
        form[8] && `Exclusion Criteria: ${form[8]}`,
        form[9] && `Reference Companies: ${form[9]}`,
        form[10] && `Other Validations by user: ${form[10]}`
      ].filter(Boolean).join('\n\n'),

      persona_prompt: [
        form[13] && `Job Title(s) of People to be searched: ${form[13]}`, 
        form[14] && `Seniority Level(s): ${form[14]}`,
        form[15] && `Department(s) of people to be searched: ${form[15]}`
      ].filter(Boolean).join('\n\n'),

      industry: form[0],
      employee_count: form[1] || 'null',
      currency: "USD", 
      revenue_min: form[21] || 'null',
      revenue_max: form[22] || 'null',
      location: form[3],
      location_type: locationType,
      keywords: 'null',
      categories: 'null',
      hubspot_email: form[16],
      product_name: form[17],
      business_team: form[18],
      user_email: form[19]
    };

    console.log('Payload:', payload);

    try {
      const result = await createCampaign(payload).unwrap();
      
      if (result.success && result.data?.campaign_id) {
        setSubmittedId(result.data.campaign_id);
        setSubmitted(true);
        setForm(Array(24).fill(''));
        setLocationType('');
        setStep(0);
      } else {
        alert('❌ Failed to submit');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('❌ Failed to submit');
    }
  };

  const isStepValid = () => {
    if (optionalQuestions.has(step)) {
    return true;
  }

    if (step === 2) {
      // For revenue step, check if both min and max are filled
      return form[9] && form[20]; // min, max, currency
    }
    if (step === 3) {
      // For location step, check if location type is selected and locations are chosen
      return locationType && form[step] && form[step].trim();
    }
    return form[step] && form[step].toString().trim();
  };

  return (
    <div className="fullscreen-container" >
      <form onSubmit={handleSubmit} className="step-form full-width-height" >
        <button
          type="button"
          className="back-to-campaigns-btn"
          onClick={() => navigate('/campaign')}
        >
          ← Back to Campaigns
        </button>
        <h1 className="form-title">Create New Campaign</h1>
        <div className="progress-bar">
          <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
        </div>

        {!submitted && (
          <div className="step">
            <div className="question-text" dangerouslySetInnerHTML={{ __html: stepQuestions[step] }}/>
            {optionalQuestions.has(step) && (
                      <p className="optional-indicator">(Optional)</p>
                    )}
            {/* Steps 4-10: Text areas */}
            {step >= 4 && step <= 10 && (
              <AutoResizeTextarea 
                value={form[step]} 
                onChange={handleChange} 
                name={`step_${step}`} 
                placeholder="Type your answer here..." 
                
              />
            )}

            {/* Step 0: Industries */}
            {/* {step === 0 && (
              <Select 
                isMulti 
                name={`step_${step}`} 
                options={industries.map(ind => ({ label: ind, value: ind }))} 
                value={form[step] ? form[step].split(',').map(val => ({ label: val, value: val })) : []} 
                onChange={(selected) => { 
                  const updated = [...form]; 
                  updated[step] = selected.map(opt => opt.value).join(','); 
                  setForm(updated); 
                }} 
                placeholder="Select industries..." 
              />
            )} */}
              {step === 0 && (
  <IndustryStep form={form} setForm={setForm} step={0} />
)}

            {/* Step 1: Employee Count */}
            {step === 1 && (
              <Select 
                isMulti 
                name={`step_${step}`} 
                options={employeeCounts.map(opt => ({ label: opt, value: opt }))} 
                value={form[step] ? form[step].split(',').map(val => ({ label: val, value: val })) : []} 
                onChange={(selected) => { 
                  const updated = [...form]; 
                  updated[step] = selected.map(opt => opt.value).join(','); 
                  setForm(updated); 
                }} 
                placeholder="Select company sizes..." 
              />
            )}

            {/* Step 2: Revenue (Currency + Min + Max) */}
            {step === 2 && (
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                {/* <Select 
                  name="currency" 
                  options={["USD", "EUR", "INR", "GBP"].map(c => ({ label: c, value: c }))} 
                  value={form[21] ? { label: form[21], value: form[21] } : null} 
                  onChange={(selected) => { 
                    const updated = [...form]; 
                    updated[21] = selected?.value || ''; 
                    setForm(updated); 
                  }} 
                  placeholder="Currency" 
                  className="currency-dropdown" 
                /> */}
                <input 
                  type="number" 
                  placeholder="Min (USD in Millions)" 
                  className="number-input" 
                  value={form[21] || ''} 
                  onChange={(e) => { 
                    const updated = [...form]; 
                    updated[21] = e.target.value; 
                    setForm(updated); 
                  }} 
                  min={0}
                  max={form[22] || ''}
                />
                <input 
                  type="number" 
                  placeholder="Max (USD in Millions)" 
                  className="number-input" 
                  value={form[22] || ''} 
                  onChange={(e) => { 
                    const updated = [...form]; 
                    updated[22] = e.target.value; 
                    setForm(updated); 
                  }} 
                  min={form[21] || ''}
                />
              </div>
            )}

            {/* Step 3: Location */}
            {step === 3 && (
              <div>
                <div style={{ marginBottom: '15px' }}>
                  <label style={{ display: 'block', marginBottom: '10px', fontWeight: 'bold' }}>
                    Select location type:
                  </label>
                  <div style={{ display: 'flex', gap: '15px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                      <input
                        type="radio"
                        name="locationType"
                        value="region"
                        checked={locationType === 'region'}
                        onChange={() => {
                          setLocationType('region');
                          const updated = [...form];
                          updated[step] = ''; // Clear previous selection
                          setForm(updated);
                        }}
                        style={{ marginRight: '5px' }}
                      />
                      Region
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                      <input
                        type="radio"
                        name="locationType"
                        value="country"
                        checked={locationType === 'country'}
                        onChange={() => {
                          setLocationType('country');
                          const updated = [...form];
                          updated[step] = ''; // Clear previous selection
                          setForm(updated);
                        }}
                        style={{ marginRight: '5px' }}
                      />
                      Country
                    </label>
                  </div>
                </div>

                {locationType === 'region' && (
                  <Select 
                    isMulti 
                    name="regions" 
                    options={regions.map(region => ({ label: region, value: region }))} 
                    value={form[step] ? form[step].split(',').map(val => ({ label: val, value: val })) : []} 
                    onChange={(selected) => { 
                      const updated = [...form]; 
                      updated[step] = selected.map(opt => opt.value).join(','); 
                      setForm(updated); 
                    }} 
                    placeholder="Select regions..." 
                  />
                )}

                {locationType === 'country' && (
                  <Select 
                    isMulti 
                    name="countries" 
                    options={countries.map(country => ({ label: country, value: country }))} 
                    value={form[step] ? form[step].split(',').map(val => ({ label: val, value: val })) : []} 
                    onChange={(selected) => { 
                      const updated = [...form]; 
                      updated[step] = selected.map(opt => opt.value).join(','); 
                      setForm(updated); 
                    }} 
                    placeholder="Select countries..." 
                  />
                )}
              </div>
            )}

            {/* Step 11: Keywords */}
            {step === 11 && (
              <Select 
                isMulti 
                name={`step_${step}`} 
                options={["ecommerce", "furniture", "sustainability", "D2C", "omnichannel", "logistics"].map(k => ({ label: k, value: k }))} 
                value={form[step] ? form[step].split(',').map(val => ({ label: val, value: val })) : []} 
                onChange={(selected) => { 
                  const updated = [...form]; 
                  updated[step] = selected.map(opt => opt.value).join(','); 
                  setForm(updated); 
                }} 
                placeholder="Select keywords" 
              />
            )}

            {/* Step 12: Categories */}
            {step === 12 && (
              <Select 
                isMulti 
                name={`step_${step}`} 
                options={bqCategories.map(cat => ({ label: cat, value: cat }))} 
                value={form[step] ? form[step].split(',').map(val => ({ label: val, value: val })) : []} 
                onChange={(selected) => { 
                  const updated = [...form]; 
                  updated[step] = selected.map(opt => opt.value).join(','); 
                  setForm(updated); 
                }} 
                placeholder="Select categories" 
              />
            )}

            {/* Step 13: Job titles */}
            {step === 13 && (
              <AutoResizeTextarea 
                value={form[step]} 
                onChange={handleChange} 
                name={`step_${step}`} 
                placeholder="Job titles or role keywords" 
              />
            )}

            {/* Step 14: Seniority */}
            {step === 14 && (
              <AutoResizeTextarea 
                value={form[step]} 
                onChange={handleChange} 
                name={`step_${step}`} 
                placeholder="Seniority level" 
              />
            )}

            {/* Step 15: Department */}
            {step === 15 && (
              <Select 
                isMulti 
                name={`step_${step}`} 
                options={["Accounting", "Administrative", "Arts and Design", "Business Development", "Community and Social Services", "Consulting", "Education", "Engineering", "Entrepreneurship", "Finance", "Healthcare Services", "Human Resources", "Information Technology", "Legal", "Marketing", "Media and Communication", "Military and Protective Services", "Operations", "Product Management", "Program and Project Management", "Purchasing", "Quality Assurance", "Real Estate", "Research", "Sales", "Customer Success and Support"].map(dep => ({ label: dep, value: dep }))} 
                value={form[step] ? form[step].split(',').map(val => ({ label: val, value: val })) : []} 
                onChange={(selected) => { 
                  const updated = [...form]; 
                  updated[step] = selected.map(opt => opt.value).join(','); 
                  setForm(updated); 
                }} 
                placeholder="Select departments" 
              />
            )}

            {/* Step 16: Email */}
            {step === 16 && (
              <AutoResizeTextarea 
                value={form[step]} 
                onChange={handleChange} 
                name={`step_${step}`} 
                placeholder="Enter your Hubspot's Account Email ID" 
              />
            )}

            {/* Step 17: Product */}
            {step === 17 && (
              <Select 
                name={`step_${step}`} 
                options={["GaaS", "DaaS", "Storefront", "StoreOS", "Konnect", "Commerce B2B", "OMS", "WMS", "TMS", "Fynd Logistics", "AI PIM", "PixelBin", "GlamAR"].map(n => ({ label: n, value: n }))}
                value={form[step] ? { label: form[step], value: form[step] } : null} 
                onChange={(selected) => { 
                  const updated = [...form]; 
                  updated[step] = selected?.value || ''; 
                  setForm(updated); 
                }} 
                placeholder="Select a product" 
              />
            )}

            {/* Step 18: Business Teams */}
            {step === 18 && (
              <Select 
                isMulti 
                name={`step_${step}`} 
                options={[
                  { label: 'Commerce India', value: 'Commerce India' }, 
                  { label: 'Commerce Global', value: 'Commerce Global' }
                ]} 
                value={form[step] ? form[step].split(',').map(val => ({ label: val, value: val })) : []} 
                onChange={(selected) => { 
                  const updated = [...form]; 
                  updated[step] = selected.map(opt => opt.value).join(','); 
                  setForm(updated); 
                }} 
                placeholder="Select business teams" 
              />
            )}
            {step === 19 && (
              <AutoResizeTextarea 
                value={form[step]} 
                onChange={handleChange}
                name={`step_${step}`} 
                placeholder="Enter your email id and submit" 
              />
            )}
            
            <div className="button-group">
                {step > 0 && (
                  <button
                    type="button"
                    className="prev-button"
                    onClick={handlePrevious}
                  >
                    Previous
                  </button>
                )}
                {step < stepQuestions.length - 1 ? (
                  <button
                    type="button"
                    disabled={!isStepValid()}
                    className="next-button"
                    onClick={handleNext}
                  >
                    Next
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={!isStepValid() || isSubmitting}
                    className="submit-button"
                  >
                    {isSubmitting ? 'Submitting...' : 'Submit'}
                  </button>
                )}
              </div>
          </div>
        )}

        {submitted && (
              <div className="success-message">
                ✅ Submitted successfully!
                {submittedId && (
                  <div style={{ marginTop: 8 }}>
                    <strong>Please store this Campaign ID and share with the technical team for updates:</strong> <code>{submittedId}</code>
                  </div>
                )}
              </div>
            )}
      </form>
    </div>
  );
};