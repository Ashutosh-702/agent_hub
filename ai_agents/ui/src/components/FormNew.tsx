import { useState, useRef, useEffect } from 'react';
import Select from 'react-select';

const bqCategories = [  "mining", "energy", "utilities", "hospitality", "media", "entertainment", "gaming", "sports",  "insurance", "banking", "finance", "fintech", "real estate", "education", "legal", "construction",  "retail", "ecommerce", "wholesale", "manufacturing", "logistics", "supply chain", "automotive", "biotech","fashion", "apparel", "beauty", "pharmaceutical", "chemicals", "defense", "aerospace", "cloud computing","artificial intelligence", "machine learning", "blockchain", "iot", "cybersecurity", "saas", "big data","data analytics", "erp", "crm", "cms", "robotics", "augmented reality", "virtual reality", "3d printing","5g", "digital twins", "biometrics", "edge computing", "computer vision", "speech recognition", "b2b","b2c", "d2c", "marketplace", "subscription", "on-demand", "freemium", "licensing", "outsourcing","franchise", "reseller", "aggregator", "consulting", "marketing", "advertising", "seo", "ppc","content marketing", "email marketing", "affiliate marketing", "influencer marketing", "customer service","tech support", "field service", "delivery", "installation", "training", "research", "ui design","ux design", "graphic design", "product management", "project management", "account management","data science", "machine intelligence", "computer science", "web development", "frontend", "backend","full stack", "qa", "devops", "infrastructure", "sre", "hr", "talent acquisition", "payroll","employee engagement", "compliance", "legal ops", "procurement", "finance ops", "fp&a","customer success", "sales enablement", "lead generation", "crm automation", "call center","crm systems", "product analytics", "session replay", "conversion rate", "churn prevention","loyalty programs", "payment gateway", "checkout optimization", "personalization engine","recommendation engine", "A/B testing", "multivariate testing", "data lake", "data warehouse","data mart", "etl", "elt", "pipeline orchestration", "notebooks", "BI tools", "dashboards","reporting", "OKRs", "KPIs", "north star metric", "unit economics", "CAC", "LTV", "retention","activation", "user onboarding", "feature flags", "experimentation", "feedback loops","interview scheduling", "ATS", "HRIS", "learning management", "security compliance", "ISO27001","SOC 2", "GDPR", "HIPAA", "PCI", "pen testing", "bug bounty", "vulnerability scanning","threat detection", "endpoint protection", "SIEM", "cloud security", "identity management","SSO", "MFA", "IAM", "zero trust", "network segmentation", "firewalls", "api gateway","rate limiting", "auth", "oauth", "jwt", "webhooks", "scheduling", "notifications","email infrastructure", "SMS", "push notifications", "in-app messaging", "chatbot","voice assistant", "natural language", "translation", "localization", "internationalization","geolocation", "maps", "places api", "routing", "ETA", "tracking", "fleet management","sensors", "hardware", "firmware", "bluetooth", "nfc", "qr code", "barcodes","inventory", "stock keeping", "pricing engine", "discount rules", "campaigns","voucher system", "gift cards", "wallet", "cashback", "referrals", "growth hacks","network effects", "virality", "influencer campaigns", "ugc", "reviews", "ratings","moderation", "spam detection", "toxicity", "image classification", "object detection","OCR", "document parsing", "pdf processing", "excel import", "csv export", "json apis","graphql", "rest apis", "rate limiting", "api keys", "token management", "permissions","roles", "audit logs", "billing", "invoicing", "tax", "gst", "vat", "accounting","bookkeeping", "audit", "legal", "notarization", "identity verification", "kyc","aml", "fraud detection", "risk scoring", "credit scoring", "insurance underwriting","claims", "policy management", "loan origination", "mortgages", "real estate listing","property management", "tenant screening", "lease signing", "rent collection","facility management", "maintenance requests", "smart locks", "access control","surveillance", "home automation", "climate control", "lighting", "voice control","scene management", "automation rules", "trigger events", "logging", "alerts","uptime monitoring", "status page", "incident response", "pager", "on-call","runbooks", "playbooks", "postmortems", "rca", "escalations", "sla tracking","user permissions", "session management", "cookie consent", "privacy policy","terms of use", "legal disclaimers", "dmca", "copyright", "trademark","patent", "ip strategy", "legal entity", "business registration","cap table", "equity management", "vesting", "esop", "fundraising","pitch deck", "data room", "term sheet", "safe", "convertible note","valuation", "dilution", "burn rate", "runway", "revenue model","pricing strategy", "customer segmentation", "target audience", "personas","user research", "usability testing", "click tracking", "heatmaps", "session recordings","interviews", "surveys", "net promoter score", "customer satisfaction","churn analysis", "cohort analysis", "funnel analysis", "retention curve","virality curve", "growth loops", "network analysis", "graph db","relational db", "nosql", "mongodb", "postgres", "mysql", "dynamodb","redis", "elastic search", "solr", "kafka", "rabbitmq", "sqs", "sns","pubsub", "event bus", "event sourcing", "cqrs", "command pattern","observer pattern", "factory pattern", "singleton", "builder","adapter", "proxy", "decorator", "chain of responsibility","mediator", "mvc", "mvvm", "clean architecture", "hexagonal architecture","domain driven design", "test driven development", "behavior driven development","unit testing", "integration testing", "e2e testing", "load testing", "performance testing","security testing", "accessibility", "wcag", "screen readers", "keyboard navigation","focus trap", "tab order", "semantic html", "aria labels", "contrast ratio","color blindness", "font scaling", "dark mode", "rtl support", "l10n", "i18n"];

// Demo industries for now
const industries = ["Real Estate","Design Services","Retail","Chemical Manufacturing","Broadcast Media Production and Distribution","Telecommunications","Retail Art Supplies","Wholesale Import and Export","Fine Art","Information Technology & Services","Advertising Services","Food and Beverage Services","Technology, Information and Internet","E-learning","Financial Services","Non-profit Organizations","Software Development","Computer Networking Products","Government Relations","Packaging & Containers","Education Administration Programs","Capital Markets","Manufacturing","Higher Education","Renewables & Environment","Retail Apparel and Fashion","Accounting","Construction","Law Practice","Business Consulting and Services","Alternative Medicine","Agriculture, Construction, Mining Machinery Manufacturing","Executive Offices","Restaurants","Online Audio and Video Media","International Trade and Development","Performing Arts","Management Consulting","Professional Training & Coaching","IT Services and IT Consulting","Environmental Services","Music","Food & Beverages","Hospitality","Internet","Wholesale","Oil and Gas","Design","Professional Training and Coaching","Investment Management","Apparel & Fashion","Book and Periodical Publishing","Information Services","Mining","Photography","Transportation/Trucking/Railroad","Appliances, Electrical, and Electronics Manufacturing","Furniture and Home Furnishings Manufacturing","Hospitals and Health Care","Entertainment Providers","Consumer Services","Food Production","Human Resources Services","Staffing and Recruiting","Machinery Manufacturing","Wellness and Fitness Services","Legal Services","Civil Engineering","Religious Institutions","Transportation, Logistics, Supply Chain and Storage","Public Relations and Communications Services","Sports","Events Services","Artists and Writers","Venture Capital and Private Equity Principals","Medical Equipment Manufacturing","Automotive","Consumer Electronics","Architecture and Planning","Insurance","Health, Wellness & Fitness","Market Research","Writing and Editing","Media Production","Musicians","Personal Care Product Manufacturing","Mental Health Care","International Trade & Development","Printing Services","Biotechnology Research","Motor Vehicle Manufacturing","Computer Hardware","Industrial Machinery Manufacturing","Biotechnology","Spectator Sports","Retail Luxury Goods and Jewelry","Movies, Videos, and Sound","Wine & Spirits","Philanthropic Fundraising Services","Medical Device","Plastics Manufacturing","Entertainment","Newspaper Publishing","Education","Travel Arrangements","Law Enforcement","Commercial Real Estate","Renewable Energy Semiconductor Manufacturing","Arts & Crafts","International Affairs","Banking","Industrial Automation","Dairy Product Manufacturing","Human Resources","Retail Office Equipment","Truck Transportation","Airlines and Aviation","Packaging and Containers Manufacturing","Defense & Space","Beverage Manufacturing","Graphic Design","Automation Machinery Manufacturing","Individual and Family Services","Pharmaceutical Manufacturing","Research","Business Supplies & Equipment","Farming","Hospital & Health Care","Medical Practices","Government Administration","Wholesale Building Materials","Consumer Goods","Security and Investigations","Furniture","Education Management","Pharmaceuticals","Government Relations Services","Oil & Energy","Public Safety","Fundraising","Facilities Services","Non-profit Organization Management","Venture Capital & Private Equity","Computer and Network Security","Translation and Localization","Primary and Secondary Education","Investment Advice","Gambling Facilities and Casinos","Online Media","Civic and Social Organizations","Mechanical Or Industrial Engineering","Semiconductors","Glass, Ceramics and Concrete Manufacturing","Glass, Ceramics & Concrete","Leisure, Travel & Tourism","Strategic Management Services","Research Services","Other","Utilities","Think Tanks","Writing & Editing","Import & Export","Gambling & Casinos","Veterinary","Translation & Localization","Defense and Space Manufacturing","Textile Manufacturing","Sporting Goods","Staffing & Recruiting","Aviation and Aerospace Component Manufacturing","Broadcast Media","Veterinary Services","E-Learning Providers","Sports Teams and Clubs","Food and Beverage Manufacturing","Recreational Facilities","Electrical & Electronic Manufacturing","Movies and Sound Recording","Judiciary","Food and Beverage Retail","Outsourcing and Offshoring Consulting","Paper and Forest Product Manufacturing","Logistics & Supply Chain","Investment Banking","Political Organizations","Computer Software","Animation","Maritime Transportation","Warehousing and Storage","Libraries","Leasing Non-residential Real Estate","Philanthropy","Sporting Goods Manufacturing","Luxury Goods & Jewelry","Maritime","Museums, Historical Sites, and Zoos","Ranching","Cosmetics","Computers and Electronics Manufacturing","Textiles","Building Materials","Civic & Social Organization","Aviation & Aerospace","Architecture & Planning","Alternative Dispute Resolution","Wireless Services","Computer Games","Freight and Package Transportation","Public Policy Offices","Publishing","Printing","Sports and Recreation Instruction","Fisheries","Nanotechnology Research","Building Construction","Public Relations & Communications","Program Development","Animation and Post-production","Armed Forces","Computer Hardware Manufacturing","Computer Networking","Paper & Forest Products","Security & Investigations","Computer & Network Security","Services for Renewable Energy","Chemicals","IT System Custom Software Development","Semiconductor Manufacturing","Operations Consulting","Professional Services","Marketing & Advertising","Tobacco Manufacturing","Warehousing","Executive Office","Machinery","Internet Marketplace Platforms","Outsourcing/Offshoring","Insurance Agencies and Brokerages","Marketing Services","Technology, Information and Media","Commercial and Industrial Machinery Maintenance","Railroad Equipment Manufacturing","Administration of Justice","Primary/Secondary Education","Security Systems Services","Solar Electric Power Generation","Internet Publishing","Political Organization","Legislative Offices","Retail Appliances, Electrical, and Electronic Equipment","Engineering Services","Medical Practice","Newspapers","Public Policy","Renewable Energy Power Generation","Motor Vehicle Parts Manufacturing","Media and Telecommunications","Individual & Family Services","Shipbuilding","Golf Courses and Country Clubs","Rail Transportation","Retail Groceries","Real Estate Agents and Brokers","Wholesale Motor Vehicles and Parts","Electric Power Generation","Wholesale Furniture and Home Furnishings","Vehicle Repair and Maintenance","Digital Accessibility Services","Recreational Facilities & Services","IT System Design Services","Retail Furniture and Home Furnishings","Health and Human Services","Mining & Metals","Retail Books and Printed News","Fabricated Metal Products","Book Publishing","Package/Freight Delivery","Leather Product Manufacturing","Dentists","Tobacco","Economic Programs","Military","Ground Passenger Transportation","Plastics","Dairy","Physicians","Space Research and Technology","Executive Search Services","Wholesale Paper Products","Repair and Maintenance","Personal Care Services","Community Services","Retail Motor Vehicles","Supermarkets","Wireless","Periodical Publishing","Plastics and Rubber Product Manufacturing","Retail Health and Personal Care Products","Data Infrastructure and Analytics","Interior Design","Bars, Taverns, and Nightclubs","Water, Waste, Steam, and Air Conditioning Services","Urban Transit Services","Zoos and Botanical Gardens","Nanotechnology","Airlines/Aviation","Railroad Manufacture","IT System Operations and Maintenance","Leasing Residential Real Estate","Fishery","Blogs","Museums & Institutions","Taxi and Limousine Services","Wind Electric Power Generation","Holding Companies","Motion Pictures & Film","Retail Building Materials and Garden Equipment","Medical and Diagnostic Laboratories","Retail Art Dealers","Electric Lighting Equipment Manufacturing","Social Networking Platforms","Commercial and Industrial Equipment Rental","Language Schools","Animal Feed Manufacturing","Funds and Trusts","Business Content","Theater Companies","Internet News","Services for the Elderly and Disabled","Real Estate and Equipment Rental Services","Skiing Facilities","IT System Data Services","Pet Services","Waste Collection","Forestry and Logging","Data Security Software Products","Landscaping Services","Architectural and Structural Metal Manufacturing","Embedded Software Products","Baked Goods Manufacturing","Trusts and Estates","Wholesale Computer Equipment","Soap and Cleaning Product Manufacturing","Wholesale Drugs and Sundries","Blockchain Services","Metal Treatments","Public Health","Industry Associations","Transportation Equipment Manufacturing","Metalworking Machinery Manufacturing","Primary Metal Manufacturing","Hotels and Motels","Hydroelectric Power Generation","Transportation Programs","Housing and Community Development","Specialty Trade Contractors","Chiropractors","Conservation Programs","Biomass Electric Power Generation","Bed-and-Breakfasts, Hostels, Homestays","Physical, Occupational and Speech Therapists","Building Structure and Exterior Contractors","Online and Mail Order Retail","Communications Equipment Manufacturing","Fashion Accessories Manufacturing","Wholesale Appliances, Electrical, and Electronics","Wholesale Alcoholic Beverages","Office Furniture and Fixtures Manufacturing","Nursing Homes and Residential Care Facilities","Farming, Ranching, Forestry","Business Intelligence Platforms","Professional Organizations","Fire Protection","Electrical Equipment Manufacturing","HVAC and Refrigeration Equipment Manufacturing","Measuring and Control Instrument Manufacturing","Emergency and Relief Services","Retail Recyclable Materials & Used Merchandise","Vocational Rehabilitation Services","Wholesale Food and Beverage","Wholesale Metals and Minerals","Spring and Wire Product Manufacturing","Wholesale Hardware, Plumbing, Heating Equipment","Accessible Architecture and Design","Nonmetallic Mineral Mining","Glass Product Manufacturing","Subdivision of Land","Museums","Accommodation and Food Services","Wholesale Machinery","Wineries","Electric Power Transmission, Control, and Distribution","Electronic and Precision Equipment Maintenance","Wholesale Luxury Goods and Jewelry","Building Equipment Contractors","Administrative and Support Services","Hospitals","Artificial Rubber and Synthetic Fiber Manufacturing","Environmental Quality Programs","Wholesale Recyclable Materials","Commercial and Service Industry Machinery Manufacturing","Agricultural Chemical Manufacturing","Wood Product Manufacturing","Nuclear Electric Power Generation","Residential Building Construction","Surveying and Mapping Services","Household Appliance Manufacturing","Sound Recording","Wholesale Chemical and Allied Products","Footwear Manufacturing","Meat Products Manufacturing","Waste Treatment and Disposal","Equipment Rental Services","Shuttles and Special Needs Transportation Services","Cosmetology and Barber Schools","Security Guards and Patrol Services","Technical and Vocational Training","IT System Training and Support","Legislative Office","Home Health Care Services","Wholesale Raw Farm Products","Climate Data and Analytics","Mobile Computing Software Products","Apparel Manufacturing","Rubber Products Manufacturing","Mobile Gaming Apps","Mattress and Blinds Manufacturing","Audio and Video Equipment Manufacturing","Retail Musical Instruments","Sugar and Confectionery Product Manufacturing","Wholesale Petroleum and Petroleum Products","Horticulture","Paint, Coating, and Adhesive Manufacturing","Retail Florists","Highway, Street, and Bridge Construction","Desktop Computing Software Products","Performing Arts and Spectator Sports","Insurance and Employee Benefit Funds","Community Development and Urban Planning","Renewable Energy Equipment Manufacturing","Telephone Call Centers","IT System Testing and Evaluation","Climate Technology Product Manufacturing","Construction Hardware Manufacturing","Chemical Raw Materials Manufacturing","Water Supply and Irrigation Systems","Distilleries","Metal Ore Mining","Wholesale Photography Equipment and Supplies","Child Day Care Services","Dance Companies","Courts of Law","Utilities Administration","Radio and Television Broadcasting","Building Finishing Contractors","Sheet Music Publishing","Geothermal Electric Power Generation","Retail Gasoline","Loan Brokers","Historical Sites","Air, Water, and Waste Program Management","Utility System Construction","Collection Agencies","Pipeline Transportation","Accessible Hardware Manufacturing","Janitorial Services","Caterers","Retail Pharmacies","Retail Office Supplies and Gifts","Household Services","Nonresidential Building Construction","Alternative Fuel Vehicle Manufacturing","Engines and Power Transmission Equipment Manufacturing","Mobile Food Services","Satellite Telecommunications","Sightseeing Transportation","Metal Valve, Ball, and Roller Manufacturing","Amusement Parks and Arcades","Laundry and Drycleaning Services","Wholesale Footwear","Securities and Commodity Exchanges","Fine Arts Schools","Turned Products and Fastener Manufacturing","Oil, Gas, and Mining","Robot Manufacturing","Telecommunications Carriers","Seafood Product Manufacturing","Office Administration","Optometrists","Wholesale Apparel and Sewing Supplies","Oil Extraction","Boilers, Tanks, and Shipping Container Manufacturing","Robotics Engineering","Housing Programs","Military and International Affairs","Cable and Satellite Programming","Clay and Refractory Products Manufacturing","Insurance Carriers","Flight Training","Fossil Fuel Electric Power Generation","Household and Institutional Furniture Manufacturing","Interurban and Rural Bus Services","Ranching and Fisheries","Natural Gas Extraction","Postal Services","Reupholstery and Furniture Repair","Temporary Help Services","Consumer Goods Rental","Steam and Air-Conditioning Supply","Coal Mining","Ambulance Services","Women's Handbag Manufacturing","Pension Funds","Fruit and Vegetable Preserves Manufacturing","Credit Intermediation","Regenerative Design","Circuses and Magic Shows","Magnetic and Optical Media Manufacturing","Claims Adjusting, Actuarial Services","Oil and Coal Product Manufacturing","IT System Installation and Disposal","Natural Gas Distribution","Personal and Laundry Services","Footwear and Leather Goods Repair","Correctional Institutions","Breweries","Mobile Games","Racetracks","Outpatient Care Centers","Abrasives and Nonmetallic Minerals Manufacturing","School and Employee Bus Services","Public Assistance Programs","Savings Institutions","Family Planning Centers","Cutlery and Handtool Manufacturing","Lime and Gypsum Products Manufacturing","Secretarial Schools","null","Smart Meter Manufacturing","Fuel Cell Manufacturing"];


const employeeCounts = ['1-10', '11-50', '51-200', '201+'];
const optionalQuestions = new Set([8,9]);
const regions = [
  'North America',
  'South America', 
  'Europe',
  'Asia Pacific',
  'Middle East',
  'Africa',
  'Central America',
  'Caribbean'
];

const countries = [
  'United States',
  'Canada',
  'United Kingdom',
  'Germany',
  'France',
  'India',
  'China',
  'Japan',
  'Australia',
  'Brazil',
  'Mexico',
  'Italy',
  'Spain',
  'Netherlands',
  'Sweden',
  'Singapore',
  'South Korea',
  'Switzerland',
  'Belgium',
  'Austria'
];

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
      el.style.height = `${Math.max(el.scrollHeight,450)}px`;
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
      rows={1}
      style={{minHeight:'450px'}}
    />
  );
};

const stepQuestions = [
  // SDR Company Relevance Prompt (7)
  // "Please provide a comprehensive and detailed outline of the relevance criteria for companies you aim to target. \n\n\n\n\n\n\nThe more specific and exhaustive your criteria, the higher the likelihood that we can identify and prioritize the most relevant companies for outreach.",
  "<div class='question-main'>Please provide a comprehensive and detailed outline of the relevance criteria for companies you aim to target.</div><div class='question-subtitle'>The more specific and exhaustive your criteria, the higher the likelihood that we can identify and prioritize the most relevant companies for outreach.<p></p>Note:  A relevant company must be a retailer that specializes in or has significant operations in selling or renting furniture, mattresses, or other heavy/bulky home goods items.</div>",
"<div class='question-main'>Please provide mandatory criterias that a company must have to qualify as a relevant company for outreach.</div><div class='question-subtitle'>The more specific and exhaustive details you share, the higher will be the likelihood that we can identify and prioritize the most relevant companies for outreach.<p></p>Note: Primary business must involve furniture, mattresses, or heavy/bulky home goods (sofas, beds, tables, chairs, wardrobes, appliances, outdoor furniture) Must have either e-commerce presence (online store with delivery capabilities) OR physical retail storesMust serve end consumers (B2C model)</div>",
"<div class='question-main'>Please share qualifying business models that are relevant to this outreach campaign.</div><div class='question-subtitle'>The more specific and exhaustive details you share, the higher will be the likelihood that we can identify and prioritize the most relevant companies for outreach.<p></p>Note: Direct furniture/mattress sales (online or in-store). Furniture rental services. Made-to-order/custom furniture providers. Hybrid models combining sales and rental. </div>",
"<div class='question-main'>What are the key positive indicators that signal a company is a strong fit for your target profile?</div><div class='question-subtitle'>Please specify any attributes, characteristics, or patterns that, if present, confirm the company aligns with what you're looking for. The more specific and exhaustive details you share, the higher will be the likelihood that we can identify and prioritize the most relevant companies for outreach.<p></p>Note: Multiple physical store locations. Established e-commerce platform with delivery logistics. Offers both ready-made and customizable options. Provides white-glove delivery or assembly services. Has dedicated sections for living room, bedroom, dining room furniture. Offers financing or rental plans. Serves metropolitan areas</div>",
"<div class='question-main'>What are some exclusion criteria that the AI should apply to immediately disqualify a company as not relevant?</div><div class='question-subtitle'>Please specify any attributes or red flags that should lead to automatic exclusion. The more specific and exhaustive details you share, the higher will be the likelihood that we can identify and prioritize the most relevant companies for outreach.<p></p>Note: Pure B2B furniture suppliers without consumer presence. Interior design services without furniture sales. Pure marketplace platforms without own inventory. Companies focusing only on small home decor items without furniture. Office furniture specialists without home furniture offerings. </div>",
"<div class='question-main'>Please share a few reference companies along with the specific characteristics that make them relevant. This will help the AI better understand and identify similar companies during the targeting process.</div><div class='question-subtitle'>The more specific and exhaustive details you share, the higher will be the likelihood that we can identify and prioritize the most relevant companies for outreach.<p></p>Note: The Sleep Company: Mattress specialist with e-commerce focus. West Elm/Pottery Barn: Multi-location furniture retailers with strong e-commerce and physical presence. CityFurnish/Rentickle: Furniture rental services targeting urban consumers. </div>",
"<div class='question-main'>Do you have any additional validations that need to be ensured to ensure the company is relevant?</div>",
  // Company Shortlisting (6)
  "<div class='question-main'>Which industries or verticals are in scope?</div>", // step 7
  "<div class='question-main'>Target company size by head-count?</div>", // step 8
  "<div class='question-main'>Target company size by annual revenue?</div>", // step 9 (currency + min + max)
  "<div class='question-main'>Location</div>", // step 10
  "<div class='question-main'>Keywords</div>", // step 11
  "<div class='question-main'>Categories</div>", // step 12

  // Persona Prompt (3)
  "<div class='question-main'>Job titles or role keywords</div>", // step 13
  "<div class='question-main'>Seniority level</div>", // step 14
  "<div class='question-main'>Department</div>", // step 15

  // SDR Setup (3)
  "<div class='question-main'>Please share the email ID of the person against whom the contact should be saved in Hubspot</div>", // step 16
  "<div class='question-main'>Please share the name product for which you are targeting this outreach</div>", // step 17
  "<div class='question-main'>Please share the business team for whom you are initiating the outreach</div>", // step 18
  "<div class='question-main'>Please share your own email id</div>" //step 19
];

export const Form = () => {
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

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const updated = [...form];
    updated[step] = e.target.value;
    setForm(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const payload = {
  web_prompt: [
    ...form.slice(0, 7),
  ].filter(Boolean).join('\n\n'),

  persona_prompt: [
    form[13], 
    form[14],
    form[15]  
  ].filter(Boolean).join('\n\n'),

  industry: form[7],
  employee_count: form[8] || 'null',
  currency: form[21] || 'null', 
  revenue_min: form[9] || 'null',
  revenue_max: form[20] || 'null',
  location: form[10] ,
  location_type: locationType,
  keywords: 'null', //form[11]
  categories: 'null', //form[12]
  hubspot_email: form[16],
  product_name: form[17],
  business_team: form[18],
  user_email: form[19]
};

  
    console.log('Payload:', payload);

    try {
      const response = await fetch('http://localhost:8000/api/v1/sheets/upload_data_from_form', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
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

    if (step === 9) {
      // For revenue step, check if both min and max are filled
      return form[9] && form[20] && form[21]; // min, max, currency
    }
    if (step === 10) {
      // For location step, check if location type is selected and locations are chosen
      return locationType && form[10] && form[10].trim();
    }
    return form[step] && form[step].toString().trim();
  };

  return (
    <div className="fullscreen-container" >
      <form onSubmit={handleSubmit} className="step-form full-width-height" >
        <h1 className="form-title">Company Info Form</h1>
        <div className="progress-bar">
          <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
        </div>

        {!submitted && (
          <div className="step">
            <div className="question-text" dangerouslySetInnerHTML={{ __html: stepQuestions[step] }}/>
            {optionalQuestions.has(step) && (
                      <p className="optional-indicator">(Optional)</p>
                    )}
            {/* Steps 0-6: Text areas */}
            {step >= 0 && step <= 6 && (
              <AutoResizeTextarea 
                value={form[step]} 
                onChange={handleChange} 
                name={`step_${step}`} 
                placeholder="Type your answer here..." 
                
              />
            )}

            {/* Step 7: Industries */}
            {step === 7 && (
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
            )}

            {/* Step 8: Employee Count */}
            {step === 8 && (
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

            {/* Step 9: Revenue (Currency + Min + Max) */}
            {step === 9 && (
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <Select 
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
                />
                <input 
                  type="number" 
                  placeholder="Min (M)" 
                  className="number-input" 
                  value={form[9] || ''} 
                  onChange={(e) => { 
                    const updated = [...form]; 
                    updated[9] = e.target.value; 
                    setForm(updated); 
                  }} 
                />
                <input 
                  type="number" 
                  placeholder="Max (M)" 
                  className="number-input" 
                  value={form[20] || ''} 
                  onChange={(e) => { 
                    const updated = [...form]; 
                    updated[20] = e.target.value; 
                    setForm(updated); 
                  }} 
                />
              </div>
            )}

            {/* Step 10: Location */}
            {step === 10 && (
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
                          updated[10] = ''; // Clear previous selection
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
                          updated[10] = ''; // Clear previous selection
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
                    value={form[10] ? form[10].split(',').map(val => ({ label: val, value: val })) : []} 
                    onChange={(selected) => { 
                      const updated = [...form]; 
                      updated[10] = selected.map(opt => opt.value).join(','); 
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
                    value={form[10] ? form[10].split(',').map(val => ({ label: val, value: val })) : []} 
                    onChange={(selected) => { 
                      const updated = [...form]; 
                      updated[10] = selected.map(opt => opt.value).join(','); 
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
                options={[
                  { label: 'Fynd_Global', value: 'Fynd_Global' }, 
                  { label: 'Fynd_Commerce', value: 'Fynd_Commerce' }
                ]} 
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
                disabled={!isStepValid()}
                className="submit-button"
              >
                Submit
              </button>
            )}
          </div>
        )}

        {submitted && (
          <p className="success-message">✅ Submitted successfully!</p>
        )}
      </form>
    </div>
  );
};