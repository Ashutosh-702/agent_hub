import json
import os
from openai import OpenAI
from typing import Dict, List, Any
from dotenv import load_dotenv
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=api_key)

def analyze_prompt(prompt: str) -> Dict[str, Any]:
    """Use GPT to analyze prompt and generate comprehensive questions"""
    client = get_openai_client()
    system_prompt = """You are an AI Sales Development Assistant.

Your task is to help users define highly detailed B2B company targeting criteria. You will:
1. Extract clear filters from the user's prompt.
2. Ask follow-up questions for anything missing.
3. Output a structured JSON object for downstream API filtering and enrichment.

---

🎯 SUPPORTED FILTER FIELDS (only use these):

- `industry`: must be one of the predefined industries (see below)
- `hq_country`: e.g. "India", "United States" (Headquarted in which country/region)
- `employee_range`: e.g. "1-10", "11-50", "51-200", "201-1000", "1000+"
- `is_b2b`: true or false
- `categories_and_keywords`: freeform tags like "AI", "ecommerce", "B2B SaaS"

❌ DO NOT include:
- Contact titles, funding stage, tech stack, pricing model, sales motion, intent, product features — these are handled in enrichment only.

---

🧾 OUTPUT FORMAT (must be JSON):
{
  "questions": [...],
  "enhanced_initial_input": {
    "original": "...",
    "enhanced": "...",
    "extracted_criteria": {
      "industry": "...",
      "employee_range": "...",
      "hq_country": "...",
      "is_b2b": true,
      "categories_and_keywords": [...]
    }
  },
  "relevance_criteria_template": {
    "mandatory_fields": [],
    "scoring_criteria": {},
    "validation_questions": []
  }
}

---

🔍 QUESTION GENERATION:

If a required filter is missing, return a `questions` list where each question includes:
- `id`
- `question`
- `input_type` ("single_select", "free_text", etc.)
- `options` (only if select type)
- `validation`

---

✅ VALID INDUSTRIES:

Use this industry list for extraction and options (exact matches only):
["Real Estate" "Design Services", "Retail", "Chemical Manufacturing", "Broadcast Media Production and Distribution", "Telecommunications", "Retail Art Supplies", "Wholesale Import and Export", "Fine Art", "Information Technology & Services", "Advertising Services", "Food and Beverage Services", "Technology, Information and Internet", "E-learning", "Financial Services", "Non-profit Organizations", "Software Development", "Computer Networking Products", "Government Relations", "Packaging & Containers", "Education Administration Programs", "Capital Markets", "Manufacturing", "Higher Education", "Renewables & Environment", "Retail Apparel and Fashion", "Accounting", "Construction", "Law Practice", "Business Consulting and Services", "Alternative Medicine", "Agriculture, Construction, Mining Machinery Manufacturing", "Executive Offices", "Restaurants", "Online Audio and Video Media", "International Trade and Development", "Performing Arts", "Management Consulting", "Professional Training & Coaching", "IT Services and IT Consulting", "Environmental Services", "Music", "Food & Beverages", "Hospitality", "Internet", "Wholesale", "Oil and Gas", "Design", "Professional Training and Coaching", "Investment Management", "Apparel & Fashion", "Book and Periodical Publishing", "Information Services", "Mining", "Photography", "Transportation/Trucking/Railroad", "Appliances, Electrical, and Electronics Manufacturing", "Furniture and Home Furnishings Manufacturing", "Hospitals and Health Care", "Entertainment Providers", "Consumer Services", "Food Production", "Human Resources Services", "Staffing and Recruiting", "Machinery Manufacturing", "Wellness and Fitness Services", "Legal Services", "Civil Engineering", "Religious Institutions", "Transportation, Logistics, Supply Chain and Storage", "Public Relations and Communications Services", "Sports", "Events Services", "Artists and Writers", "Venture Capital and Private Equity Principals", "Medical Equipment Manufacturing", "Automotive", "Consumer Electronics", "Architecture and Planning", "Insurance", "Health, Wellness & Fitness", "Market Research", "Writing and Editing", "Media Production", "Musicians", "Personal Care Product Manufacturing", "Mental Health Care", "International Trade & Development", "Printing Services", "Biotechnology Research", "Motor Vehicle Manufacturing", "Computer Hardware", "Industrial Machinery Manufacturing", "Biotechnology", "Spectator Sports", "Retail Luxury Goods and Jewelry", "Movies, Videos, and Sound", "Wine & Spirits", "Philanthropic Fundraising Services", "Medical Device", "Plastics Manufacturing", "Entertainment", "Newspaper Publishing", "Education", "Travel Arrangements", "Law Enforcement", "Commercial Real Estate", "Renewable Energy Semiconductor Manufacturing", "Arts & Crafts", "International Affairs", "Banking", "Industrial Automation", "Dairy Product Manufacturing", "Human Resources", "Retail Office Equipment", "Truck Transportation", "Airlines and Aviation", "Packaging and Containers Manufacturing", "Defense & Space", "Beverage Manufacturing", "Graphic Design", "Automation Machinery Manufacturing", "Individual and Family Services", "Pharmaceutical Manufacturing", "Research", "Business Supplies & Equipment", "Farming", "Hospital & Health Care", "Medical Practices", "Government Administration", "Wholesale Building Materials", "Consumer Goods", "Security and Investigations", "Furniture", "Education Management", "Pharmaceuticals", "Government Relations Services", "Oil & Energy", "Public Safety", "Fundraising", "Facilities Services", "Non-profit Organization Management", "Venture Capital & Private Equity", "Computer and Network Security", "Translation and Localization", "Primary and Secondary Education", "Investment Advice", "Gambling Facilities and Casinos", "Online Media", "Civic and Social Organizations", "Mechanical Or Industrial Engineering", "Semiconductors", "Glass, Ceramics and Concrete Manufacturing", "Glass, Ceramics & Concrete", "Leisure, Travel & Tourism", "Strategic Management Services", "Research Services", "Other", "Utilities", "Think Tanks", "Writing & Editing", "Import & Export", "Gambling & Casinos", "Veterinary", "Translation & Localization", "Defense and Space Manufacturing", "Textile Manufacturing", "Sporting Goods", "Staffing & Recruiting", "Aviation and Aerospace Component Manufacturing", "Broadcast Media", "Veterinary Services", "E-Learning Providers", "Sports Teams and Clubs", "Food and Beverage Manufacturing", "Recreational Facilities", "Electrical & Electronic Manufacturing", "Movies and Sound Recording", "Judiciary", "Food and Beverage Retail", "Outsourcing and Offshoring Consulting", "Paper and Forest Product Manufacturing", "Logistics & Supply Chain", "Investment Banking", "Political Organizations", "Computer Software", "Animation", "Maritime Transportation", "Warehousing and Storage", "Libraries", "Leasing Non-residential Real Estate", "Philanthropy", "Sporting Goods Manufacturing", "Luxury Goods & Jewelry", "Maritime", "Museums, Historical Sites, and Zoos", "Ranching", "Cosmetics", "Computers and Electronics Manufacturing", "Textiles", "Building Materials", "Civic & Social Organization", "Aviation & Aerospace", "Architecture & Planning", "Alternative Dispute Resolution", "Wireless Services", "Computer Games", "Freight and Package Transportation", "Public Policy Offices", "Publishing", "Printing", "Sports and Recreation Instruction", "Fisheries", "Nanotechnology Research", "Building Construction", "Public Relations & Communications", "Program Development", "Animation and Post-production", "Armed Forces", "Computer Hardware Manufacturing", "Computer Networking", "Paper & Forest Products", "Security & Investigations", "Computer & Network Security", "Services for Renewable Energy", "Chemicals", "IT System Custom Software Development", "Semiconductor Manufacturing", "Operations Consulting", "Professional Services", "Marketing & Advertising", "Tobacco Manufacturing", "Warehousing", "Executive Office", "Machinery", "Internet Marketplace Platforms", "Outsourcing/Offshoring", "Insurance Agencies and Brokerages", "Marketing Services", "Technology, Information and Media", "Commercial and Industrial Machinery Maintenance", "Railroad Equipment Manufacturing", "Administration of Justice", "Primary/Secondary Education", "Security Systems Services", "Solar Electric Power Generation", "Internet Publishing", "Political Organization", "Legislative Offices", "Retail Appliances, Electrical, and Electronic Equipment", "Engineering Services", "Medical Practice", "Newspapers", "Public Policy", "Renewable Energy Power Generation", "Motor Vehicle Parts Manufacturing", "Media and Telecommunications", "Individual & Family Services", "Shipbuilding", "Golf Courses and Country Clubs", "Rail Transportation", "Retail Groceries", "Real Estate Agents and Brokers", "Wholesale Motor Vehicles and Parts", "Electric Power Generation", "Wholesale Furniture and Home Furnishings", "Vehicle Repair and Maintenance", "Digital Accessibility Services", "Recreational Facilities & Services", "IT System Design Services", "Retail Furniture and Home Furnishings", "Health and Human Services", "Mining & Metals", "Retail Books and Printed News", "Fabricated Metal Products", "Book Publishing", "Package/Freight Delivery", "Leather Product Manufacturing", "Dentists", "Tobacco", "Economic Programs", "Military", "Ground Passenger Transportation", "Plastics", "Dairy", "Physicians", "Space Research and Technology", "Executive Search Services", "Wholesale Paper Products", "Repair and Maintenance", "Personal Care Services", "Community Services", "Retail Motor Vehicles", "Supermarkets", "Wireless", "Periodical Publishing", "Plastics and Rubber Product Manufacturing", "Retail Health and Personal Care Products", "Data Infrastructure and Analytics", "Interior Design", "Bars, Taverns, and Nightclubs", "Water, Waste, Steam, and Air Conditioning Services", "Urban Transit Services", "Zoos and Botanical Gardens", "Nanotechnology", "Airlines/Aviation", "Railroad Manufacture", "IT System Operations and Maintenance", "Leasing Residential Real Estate", "Fishery", "Blogs", "Museums & Institutions", "Taxi and Limousine Services", "Wind Electric Power Generation", "Holding Companies", "Motion Pictures & Film", "Retail Building Materials and Garden Equipment", "Medical and Diagnostic Laboratories", "Retail Art Dealers", "Electric Lighting Equipment Manufacturing", "Social Networking Platforms", "Commercial and Industrial Equipment Rental", "Language Schools", "Animal Feed Manufacturing", "Funds and Trusts", "Business Content", "Theater Companies", "Internet News", "Services for the Elderly and Disabled", "Real Estate and Equipment Rental Services", "Skiing Facilities", "IT System Data Services", "Pet Services", "Waste Collection", "Forestry and Logging", "Data Security Software Products", "Landscaping Services", "Architectural and Structural Metal Manufacturing", "Embedded Software Products", "Baked Goods Manufacturing", "Trusts and Estates", "Wholesale Computer Equipment", "Soap and Cleaning Product Manufacturing", "Wholesale Drugs and Sundries", "Blockchain Services", "Metal Treatments", "Public Health", "Industry Associations", "Transportation Equipment Manufacturing", "Metalworking Machinery Manufacturing", "Primary Metal Manufacturing", "Hotels and Motels", "Hydroelectric Power Generation", "Transportation Programs", "Housing and Community Development", "Specialty Trade Contractors", "Chiropractors", "Conservation Programs", "Biomass Electric Power Generation", "Bed-and-Breakfasts, Hostels, Homestays", "Physical, Occupational and Speech Therapists", "Building Structure and Exterior Contractors", "Online and Mail Order Retail", "Communications Equipment Manufacturing", "Fashion Accessories Manufacturing", "Wholesale Appliances, Electrical, and Electronics", "Wholesale Alcoholic Beverages", "Office Furniture and Fixtures Manufacturing", "Nursing Homes and Residential Care Facilities", "Farming, Ranching, Forestry", "Business Intelligence Platforms", "Professional Organizations", "Fire Protection", "Electrical Equipment Manufacturing", "HVAC and Refrigeration Equipment Manufacturing", "Measuring and Control Instrument Manufacturing", "Emergency and Relief Services", "Retail Recyclable Materials & Used Merchandise", "Vocational Rehabilitation Services", "Wholesale Food and Beverage", "Wholesale Metals and Minerals", "Spring and Wire Product Manufacturing", "Wholesale Hardware, Plumbing, Heating Equipment", "Accessible Architecture and Design", "Nonmetallic Mineral Mining", "Glass Product Manufacturing", "Subdivision of Land", "Museums", "Accommodation and Food Services", "Wholesale Machinery", "Wineries", "Electric Power Transmission, Control, and Distribution", "Electronic and Precision Equipment Maintenance", "Wholesale Luxury Goods and Jewelry", "Building Equipment Contractors", "Administrative and Support Services", "Hospitals", "Artificial Rubber and Synthetic Fiber Manufacturing", "Environmental Quality Programs", "Wholesale Recyclable Materials", "Commercial and Service Industry Machinery Manufacturing", "Agricultural Chemical Manufacturing", "Wood Product Manufacturing", "Nuclear Electric Power Generation", "Residential Building Construction", "Surveying and Mapping Services", "Household Appliance Manufacturing", "Sound Recording", "Wholesale Chemical and Allied Products", "Footwear Manufacturing", "Meat Products Manufacturing", "Waste Treatment and Disposal", "Equipment Rental Services", "Shuttles and Special Needs Transportation Services", "Cosmetology and Barber Schools", "Security Guards and Patrol Services", "Technical and Vocational Training", "IT System Training and Support", "Legislative Office", "Home Health Care Services", "Wholesale Raw Farm Products", "Climate Data and Analytics", "Mobile Computing Software Products", "Apparel Manufacturing", "Rubber Products Manufacturing", "Mobile Gaming Apps", "Mattress and Blinds Manufacturing", "Audio and Video Equipment Manufacturing", "Retail Musical Instruments", "Sugar and Confectionery Product Manufacturing", "Wholesale Petroleum and Petroleum Products", "Horticulture", "Paint, Coating, and Adhesive Manufacturing", "Retail Florists", "Highway, Street, and Bridge Construction", "Desktop Computing Software Products", "Performing Arts and Spectator Sports", "Insurance and Employee Benefit Funds", "Community Development and Urban Planning", "Renewable Energy Equipment Manufacturing", "Telephone Call Centers", "IT System Testing and Evaluation", "Climate Technology Product Manufacturing", "Construction Hardware Manufacturing", "Chemical Raw Materials Manufacturing", "Water Supply and Irrigation Systems", "Distilleries", "Metal Ore Mining", "Wholesale Photography Equipment and Supplies", "Child Day Care Services", "Dance Companies", "Courts of Law", "Utilities Administration", "Radio and Television Broadcasting", "Building Finishing Contractors", "Sheet Music Publishing", "Geothermal Electric Power Generation", "Retail Gasoline", "Loan Brokers", "Historical Sites", "Air, Water, and Waste Program Management", "Utility System Construction", "Collection Agencies", "Pipeline Transportation", "Accessible Hardware Manufacturing", "Janitorial Services", "Caterers", "Retail Pharmacies", "Retail Office Supplies and Gifts", "Household Services", "Nonresidential Building Construction", "Alternative Fuel Vehicle Manufacturing", "Engines and Power Transmission Equipment Manufacturing", "Mobile Food Services", "Satellite Telecommunications", "Sightseeing Transportation", "Metal Valve, Ball, and Roller Manufacturing", "Amusement Parks and Arcades", "Laundry and Drycleaning Services", "Wholesale Footwear", "Securities and Commodity Exchanges", "Fine Arts Schools", "Turned Products and Fastener Manufacturing", "Oil, Gas, and Mining", "Robot Manufacturing", "Telecommunications Carriers", "Seafood Product Manufacturing", "Office Administration", "Optometrists", "Wholesale Apparel and Sewing Supplies", "Oil Extraction", "Boilers, Tanks, and Shipping Container Manufacturing", "Robotics Engineering", "Housing Programs", "Military and International Affairs", "Cable and Satellite Programming", "Clay and Refractory Products Manufacturing", "Insurance Carriers", "Flight Training", "Fossil Fuel Electric Power Generation", "Household and Institutional Furniture Manufacturing", "Interurban and Rural Bus Services", "Ranching and Fisheries", "Natural Gas Extraction", "Postal Services", "Reupholstery and Furniture Repair", "Temporary Help Services", "Consumer Goods Rental", "Steam and Air-Conditioning Supply", "Coal Mining", "Ambulance Services", "Women's Handbag Manufacturing", "Pension Funds", "Fruit and Vegetable Preserves Manufacturing", "Credit Intermediation", "Regenerative Design", "Circuses and Magic Shows", "Magnetic and Optical Media Manufacturing", "Claims Adjusting, Actuarial Services", "Oil and Coal Product Manufacturing", "IT System Installation and Disposal", "Natural Gas Distribution", "Personal and Laundry Services", "Footwear and Leather Goods Repair", "Correctional Institutions", "Breweries", "Mobile Games", "Racetracks", "Outpatient Care Centers", "Abrasives and Nonmetallic Minerals Manufacturing", "School and Employee Bus Services", "Public Assistance Programs", "Savings Institutions", "Family Planning Centers", "Cutlery and Handtool Manufacturing", "Lime and Gypsum Products Manufacturing", "Secretarial Schools", "null", "Smart Meter Manufacturing", "Fuel Cell Manufacturing"]

Do not create custom industries. Only use these.

---

Your goal is to extract everything CoreSignal can search on, ask only about what's missing, and structure it perfectly. Do not include explanations or extra commentary — output just the JSON.
"""

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""Analyze the following user query and return a JSON object that contains:
1. An `enhanced_initial_input` section with:
   - `original`: the original query
   - `enhanced`: a fully expanded version with specific company filters
   - `extracted_criteria`: parsed structured info (industries, size, etc.)
2. A list of `questions` needed to complete the relevance criteria

User query: "{prompt}"

Return the output as a raw JSON object only. Do not include explanations."""}
        ],
        temperature=0,
        max_tokens=4000
    )
    
    try:
        # print("AGENT RAN:", response)
        result = response.choices[0].message.content
        return json.loads(result)
    except:
        return {
            "questions": [
                {
                    "id": "q1",
                    "category": "Company Demographics",
                    "question": "What industry are you targeting?",
                    "why_important": "Industry classification helps identify companies with similar business models and challenges",
                    "input_type": "single_select",
                    "options": ["Technology", "Healthcare", "Finance", "Manufacturing", "Other"],
                    "validation": {"required": True}
                },
                {
                    "id": "q2", 
                    "category": "Company Demographics",
                    "question": "What company size are you targeting?",
                    "why_important": "Company size affects decision-making processes and budget availability",
                    "input_type": "single_select",
                    "options": ["Startup (1-10)", "Small (11-50)", "Medium (51-200)", "Large (201-1000)", "Enterprise (1000+)"],
                    "validation": {"required": True}
                }
            ],
            "enhanced_initial_input": {
                "original": prompt,
                "enhanced": prompt,
                "extracted_criteria": {}
            },
            "relevance_criteria_template": {
                "mandatory_fields": ["industry", "company_size"],
                "scoring_criteria": {},
                "validation_questions": []
            }
        }

def enhance_prompt(prompt: str, answers: Dict[str, str]) -> Dict[str, str]:
    """Use GPT to combine original prompt with answers"""
    client = get_openai_client()
    
    system_prompt = """
You are a prompt enhancement assistant. 

Combine the original user prompt with the user's answers to create an enhanced, detailed prompt for lead generation. Don't add data that isn't already implied in the original prompt or answers.

Make the enhanced prompt natural and comprehensive, incorporating all the details from both the original prompt and the answers.
NOTE: No additional context or explanations should be added.

Return only the enhanced prompt as a string.
"""

    user_content = f"""
Original prompt: {prompt}

User answers: {answers}

Create an enhanced prompt that combines both.
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=0,
        max_tokens=300
    )
    
    enhanced_prompt = response.choices[0].message.content.strip()
    return {"enhanced_prompt": enhanced_prompt} 
