"""Seed mock data for testing AI Insights feature.

Creates:
- 1 Company with deep research data
- 2 Contacts associated with the company

Run with: python -m scripts.seed_mock_data
"""

import asyncio
from datetime import datetime, timezone
from bson import ObjectId

from config.loaded_config import loaded_config
from database.connection_manager import ConnectionManager
from database.collection_dao.companies import CompaniesDao
from database.collection_dao.contacts import ContactsDao


# Mock company data with deep research
MOCK_COMPANY = {
    "name": "Acme Retail Ltd",
    "identifiers": {
        "source_domain": "acmeretail.com",
    },
    "primary_domain": "acmeretail.com",
    "website_url": "https://www.acmeretail.com",
    "industry": "E-commerce & Retail",
    "description": "Acme Retail is a leading multi-channel retail company with 50+ stores and a growing online presence. They specialize in fashion, accessories, and lifestyle products for the Indian market.",
    "employee_count": "500-1000",
    "annual_revenue": "₹500Cr - ₹1000Cr",
    "headquarters": "Mumbai, India",
    "founded_year": 2010,
    "linkedin_url": "https://www.linkedin.com/company/acme-retail",
    
    # Enriched data with web search analysis
    "enriched_data": {
        "web_search_analysis": {
            "research_summary": {
                "about": "Acme Retail Ltd is one of India's fastest-growing omnichannel retail companies, operating 50+ stores across major metros and a rapidly expanding e-commerce platform. They sell fashion, accessories, and lifestyle products targeting the 25-45 age demographic.",
                "recent_news": [
                    "Announced expansion to 50 new retail locations in Q4 2025",
                    "Partnership with major fashion brands for exclusive collections",
                    "New 50,000 sq ft warehouse facility in Bengaluru opening in March 2026",
                    "Series C funding of $25M raised for omnichannel expansion"
                ],
                "key_initiatives": [
                    "Omnichannel transformation - integrating online and offline experiences",
                    "Ship-from-store program rollout across 30 stores",
                    "Mobile app relaunch with AR try-on features",
                    "Sustainability initiative - eco-friendly packaging and sourcing"
                ],
                "tech_stack": [
                    "Shopify Plus",
                    "Custom ERP (legacy)",
                    "SAP (partial implementation)",
                    "Manual warehouse processes",
                    "Multiple marketplace integrations (Myntra, Amazon, Flipkart)"
                ],
                "pain_points": [
                    "15% order cancellation rate due to inventory discrepancies",
                    "No real-time inventory visibility across channels",
                    "Manual warehouse processes causing fulfillment delays",
                    "Legacy OMS struggling with omnichannel requirements",
                    "High return rate (20%) due to sizing issues",
                    "Customer complaints about delivery times"
                ],
            },
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        },
    },
    
    # Deep research data (structured format)
    "deep_research": {
        "last_updated": datetime.now(timezone.utc),
        "data": {
            "company_overview": """Acme Retail Ltd is one of India's fastest-growing omnichannel retail companies, founded in 2010. With 50+ retail stores across major metros and a rapidly expanding e-commerce presence, they have established themselves as a key player in the fashion and lifestyle segment.

The company targets the 25-45 age demographic with a focus on contemporary fashion, accessories, and lifestyle products. Their revenue has grown 40% YoY, reaching ₹800Cr in FY25, with ambitious plans to double this in the next 2 years.

Key strengths include strong brand partnerships, prime retail locations, and a loyal customer base. However, they face challenges in inventory management and fulfillment efficiency as they scale their omnichannel operations.""",
            
            "recent_news": [
                {
                    "title": "Acme Retail announces 50-store expansion",
                    "date": "2025-10-15",
                    "summary": "Company plans to add 50 new stores across Tier 2 and Tier 3 cities",
                    "signal_type": "expansion",
                    "implication": "Growth mode indicates budget availability and need for scalable systems"
                },
                {
                    "title": "Series C funding of $25M closed",
                    "date": "2025-08-20",
                    "summary": "Funding to be used for technology upgrades and omnichannel capabilities",
                    "signal_type": "funding",
                    "implication": "Fresh capital available for technology investments"
                },
                {
                    "title": "New CTO joins from major e-commerce company",
                    "date": "2025-09-01",
                    "summary": "Rahul Mehta appointed as CTO to lead digital transformation",
                    "signal_type": "leadership_change",
                    "implication": "New decision maker focused on technology modernization"
                },
                {
                    "title": "Bengaluru warehouse expansion",
                    "date": "2025-11-10",
                    "summary": "50,000 sq ft facility to support southern region fulfillment",
                    "signal_type": "expansion",
                    "implication": "Infrastructure investment signals commitment to improving fulfillment"
                }
            ],
            
            "key_initiatives": [
                "Omnichannel transformation with unified inventory",
                "Ship-from-store program for faster delivery",
                "Mobile app enhancement with AR features",
                "Warehouse automation project",
                "Sustainability and eco-friendly packaging"
            ],
            
            "inferred_pain_points": [
                "Inventory discrepancies causing 15% order cancellations",
                "No real-time visibility across 50+ stores and warehouses",
                "Manual warehouse operations limiting throughput",
                "Legacy OMS unable to handle omnichannel complexity",
                "Integration challenges with multiple marketplaces",
                "High return rates due to lack of virtual try-on",
                "Customer experience fragmented between online and offline"
            ],
            
            "tech_stack": [
                "Shopify Plus (e-commerce)",
                "Custom legacy ERP",
                "SAP (partial - finance module)",
                "Manual spreadsheet-based inventory tracking",
                "Multiple marketplace seller panels",
                "Tally for accounting"
            ],
            
            "competitive_landscape": "Acme Retail competes with established players like Lifestyle, Shoppers Stop, and online-first brands. Their differentiator is exclusive brand partnerships and strong Tier 1 city presence. However, competitors are ahead in omnichannel capabilities and technology adoption.",
            
            "research_date": datetime.now(timezone.utc).isoformat(),
        }
    },
    
    # Red flags history (empty initially)
    "red_flags_history": [],
    
    # Metadata
    "created_at": datetime.now(timezone.utc),
    "updated_at": datetime.now(timezone.utc),
}


# Mock contacts data
def create_mock_contacts(company_id: ObjectId):
    """Create 2 mock contacts for the company."""
    return [
        {
            "company_id": company_id,
            "first_name": "Rajesh",
            "last_name": "Kumar",
            "email": "rajesh.kumar@acmeretail.com",
            "phone": "+91 98765 43210",
            "job_title": "VP Operations",
            "department": "Operations",
            "seniority": "VP",
            "linkedin_url": "https://www.linkedin.com/in/rajesh-kumar-ops",
            "persona": "Operations Leader",
            "decision_maker": True,
            "priorities": [
                "Reducing order cancellation rate",
                "Improving warehouse efficiency",
                "Enabling ship-from-store",
                "Cost optimization"
            ],
            "communication_style": "Data-driven, appreciates concrete ROI metrics and case studies",
            "notes": "Key decision maker for OMS and WMS. Reports to CEO. Has budget authority for operations technology.",
            "enriched_data": {
                "persona_insights": "Operations-focused executive who values efficiency metrics. Likely to respond well to ROI-focused discussions and competitive benchmarks. Has been in role for 3 years and is under pressure to reduce costs while supporting growth.",
            },
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "company_id": company_id,
            "first_name": "Priya",
            "last_name": "Sharma",
            "email": "priya.sharma@acmeretail.com",
            "phone": "+91 98765 43211",
            "job_title": "Chief Technology Officer",
            "department": "Technology",
            "seniority": "C-Level",
            "linkedin_url": "https://www.linkedin.com/in/priya-sharma-cto",
            "persona": "Technical Decision Maker",
            "decision_maker": True,
            "priorities": [
                "API-first architecture",
                "System integration and data flow",
                "Security and compliance",
                "Scalable infrastructure",
                "Reducing technical debt"
            ],
            "communication_style": "Technical depth preferred, appreciates architectural discussions and integration capabilities",
            "notes": "Newly joined CTO (Sep 2025) from major e-commerce company. Driving digital transformation agenda. Key influencer for all technology decisions.",
            "enriched_data": {
                "persona_insights": "Recently joined with mandate to modernize technology stack. Comes from e-commerce background so understands the space well. Values modern architecture, APIs, and proven integrations. May be skeptical of legacy vendors.",
            },
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
    ]


async def seed_mock_data():
    """Seed mock company and contacts data."""
    print("🌱 Seeding mock data...")
    
    # Initialize database connection
    loaded_config.connection_manager = ConnectionManager(
        mongo_uri=loaded_config.mongo_uri, 
        db_name="linkedin_sdr"
    )
    
    companies_dao = CompaniesDao(loaded_config.connection_manager.mongo_client)
    contacts_dao = ContactsDao(loaded_config.connection_manager.mongo_client)
    
    # Check if company already exists
    existing = await companies_dao.get_company_by_domain("acmeretail.com")
    if existing:
        print(f"⚠️ Company 'Acme Retail Ltd' already exists with ID: {existing['_id']}")
        company_id = existing["_id"]
        
        # Update with latest research data
        await companies_dao.update_company(
            str(company_id),
            {
                "enriched_data": MOCK_COMPANY["enriched_data"],
                "deep_research": MOCK_COMPANY["deep_research"],
                "updated_at": datetime.now(timezone.utc),
            }
        )
        print("✅ Updated company with latest deep research data")
    else:
        # Create new company
        company_id = await companies_dao.create_company(MOCK_COMPANY)
        print(f"✅ Created company 'Acme Retail Ltd' with ID: {company_id}")
    
    # Check for existing contacts
    existing_contacts = await contacts_dao.get_contacts({"company_id": company_id})
    if existing_contacts:
        print(f"⚠️ Found {len(existing_contacts)} existing contacts for company")
        for contact in existing_contacts:
            print(f"   - {contact.get('first_name')} {contact.get('last_name')} ({contact.get('job_title')})")
    else:
        # Create contacts
        mock_contacts = create_mock_contacts(company_id)
        contact_ids = await contacts_dao.create_contacts(mock_contacts)
        print(f"✅ Created {len(contact_ids)} contacts:")
        for i, contact in enumerate(mock_contacts):
            print(f"   - {contact['first_name']} {contact['last_name']} ({contact['job_title']}) - ID: {contact_ids[i]}")
    
    print("\n📊 Summary:")
    print(f"   Company ID: {company_id}")
    print(f"   Company: Acme Retail Ltd")
    print(f"   Domain: acmeretail.com")
    print(f"   Industry: E-commerce & Retail")
    print(f"   Deep Research: ✅ Available")
    print(f"   Contacts: 2 (Rajesh Kumar - VP Ops, Priya Sharma - CTO)")
    
    print("\n🎯 Use this company for testing AI Insights at:")
    print(f"   /client-calls/start → Select 'Acme Retail Ltd'")
    
    # Close connection
    await loaded_config.connection_manager.close_connections()
    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(seed_mock_data())

