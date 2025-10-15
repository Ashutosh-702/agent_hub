"""
Lusha Industry Configuration
Mapping between Lusha industries and CoreSignal industries
"""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class SubIndustry:
    """Sub-industry configuration"""
    value: str
    id: int
    coresignal: Optional[List[str]] = None


@dataclass
class MainIndustry:
    """Main industry configuration"""
    main_industry: str
    main_industry_id: int
    sub_industries: List[SubIndustry]


# Lusha Industry Configuration
LUSHA_CONFIG = [
    MainIndustry(
        main_industry="Hospitality",
        main_industry_id=1,
        sub_industries=[
            SubIndustry(value="Restaurants", id=2),
            SubIndustry(value="Food & Beverage Services", id=1),
            SubIndustry(value="Hotels & Motels", id=3),
            SubIndustry(value="Other (Hospitality)", id=778)
        ]
    ),

    MainIndustry(
        main_industry="Administrative & Support Services",
        main_industry_id=2,
        sub_industries=[
            SubIndustry(
                value="Facilities Services",
                id=6,
                coresignal=["Recreational Facilities", "Skiing Facilities"]
            ),
            SubIndustry(
                value="Translation & Localization",
                id=10,
                coresignal=["Translation and Localization",
                            "Translation & Localization"]
            ),
            SubIndustry(
                value="Events Services",
                id=5,
                coresignal=["Events Services"]
            ),
            SubIndustry(
                value="Administrative & Support Services",
                id=4,
                coresignal=[
                    "Design Services",
                    "Information Technology & Services",
                    "Advertising Services",
                    "Food and Beverage Services",
                    "Financial Services",
                    "Business Consulting and Services",
                    "IT Services and IT Consulting",
                    "Environmental Services",
                    "Information Services",
                    "Consumer Services",
                    "Human Resources Services",
                    "Wellness and Fitness Services",
                    "Legal Services",
                    "Public Relations and Communications Services",
                    "Events Services",
                    "Printing Services",
                    "Philanthropic Fundraising Services",
                    "Individual and Family Services",
                    "Government Relations Services",
                    "Facilities Services",
                    "Strategic Management Services",
                    "Research Services",
                    "Veterinary Services",
                    "Wireless Services",
                    "Services for Renewable Energy",
                    "Professional Services",
                    "Marketing Services",
                    "Security Systems Services",
                    "Engineering Services",
                    "Individual & Family Services",
                    "Digital Accessibility Services",
                    "Recreational Facilities & Services",
                    "IT System Design Services",
                    "Health and Human Services",
                    "Executive Search Services",
                    "Personal Care Services",
                    "Community Services",
                    "Water, Waste, Steam, and Air Conditioning Services",
                    "Urban Transit Services",
                    "Taxi and Limousine Services",
                    "Services for the Elderly and Disabled",
                    "Real Estate and Equipment Rental Services",
                    "IT System Data Services",
                    "Pet Services",
                    "Landscaping Services",
                    "Blockchain Services",
                    "Emergency and Relief Services",
                    "Vocational Rehabilitation Services",
                    "Accommodation and Food Services",
                    "Administrative and Support Services",
                    "Surveying and Mapping Services",
                    "Equipment Rental Services",
                    "Shuttles and Special Needs Transportation Services",
                    "Security Guards and Patrol Services",
                    "IT System Training and Support",
                    "Home Health Care Services",
                    "Child Day Care Services",
                    "Janitorial Services",
                    "Household Services",
                    "Mobile Food Services",
                    "Laundry and Drycleaning Services",
                    "Interurban and Rural Bus Services",
                    "Postal Services",
                    "Temporary Help Services",
                    "Ambulance Services",
                    "Claims Adjusting, Actuarial Services",
                    "Personal and Laundry Services",
                    "School and Employee Bus Services"
                ]
            ),
            SubIndustry(
                value="Other (Administrative & Support Services)", id=789),
            SubIndustry(
                value="Travel Arrangements",
                id=11,
                coresignal=["Travel Arrangements", "Leisure, Travel & Tourism"]
            ),
            SubIndustry(
                value="Security & Investigations",
                id=8,
                coresignal=[
                    "Security and Investigations",
                    "Computer and Network Security",
                    "Security & Investigations",
                    "Computer & Network Security"
                ]
            ),
            SubIndustry(
                value="Staffing & Recruiting",
                id=9,
                coresignal=["Staffing and Recruiting", "Staffing & Recruiting"]
            ),
            SubIndustry(value="Fundraising", id=7, coresignal=["Fundraising"]),
            SubIndustry(
                value="Writing & Editing",
                id=12,
                coresignal=["Writing and Editing", "Writing & Editing"]
            )
        ]
    ),

    MainIndustry(
        main_industry="Construction",
        main_industry_id=3,
        sub_industries=[
            SubIndustry(value="Civil Engineering", id=16,
                        coresignal=["Civil Engineering"]),
            SubIndustry(value="Other (Construction)", id=791),
            SubIndustry(value="Construction", id=13,
                        coresignal=["Construction"]),
            SubIndustry(value="Building Construction", id=15,
                        coresignal=["Building Construction"])
        ]
    ),

    MainIndustry(
        main_industry="Consumer Services",
        main_industry_id=4,
        sub_industries=[
            SubIndustry(value="Other (Consumer Services)", id=792),
            SubIndustry(
                value="Philanthropic Fundraising Services",
                id=18,
                coresignal=[
                    "Philanthropic Fundraising Services", "Philanthropy"]
            ),
            SubIndustry(value="Repair & Maintenance", id=19,
                        coresignal=["Repair and Maintenance"]),
            SubIndustry(value="Personal care services", id=17,
                        coresignal=["Personal Care Services"])
        ]
    ),

    MainIndustry(
        main_industry="Organizations",
        main_industry_id=5,
        sub_industries=[
            SubIndustry(
                value="Political Organizations",
                id=20,
                coresignal=["Political Organizations",
                            "Political Organization"]
            ),
            SubIndustry(value="Religious Institutions", id=22,
                        coresignal=["Religious Institutions"]),
            SubIndustry(
                value="Civic & Social Organizations",
                id=21,
                coresignal=["Civic and Social Organizations",
                            "Civic & Social Organization"]
            ),
            SubIndustry(value="Other (Organizations)", id=793)
        ]
    ),

    MainIndustry(
        main_industry="Education",
        main_industry_id=6,
        sub_industries=[
            SubIndustry(value="Other (Education)", id=794),
            SubIndustry(
                value="Primary & Secondary Education",
                id=25,
                coresignal=["Primary and Secondary Education",
                            "Primary/Secondary Education"]
            ),
            SubIndustry(
                value="E-Learning Providers",
                id=23,
                coresignal=["E-Learning Providers", "E-learning"]
            ),
            SubIndustry(value="Higher Education", id=24,
                        coresignal=["Higher Education"]),
            SubIndustry(
                value="Training",
                id=26,
                coresignal=["Professional Training & Coaching",
                            "Technical and Vocational Training"]
            ),
            SubIndustry(value="Schools", id=27, coresignal=["Education"])
        ]
    ),

    MainIndustry(
        main_industry="Entertainment",
        main_industry_id=7,
        sub_industries=[
            SubIndustry(
                value="Performing Arts",
                id=31,
                coresignal=["Performing Arts",
                            "Theater Companies", "Dance Companies"]
            ),
            SubIndustry(
                value="Recreational Facilities",
                id=33,
                coresignal=["Recreational Facilities",
                            "Recreational Facilities & Services"]
            ),
            SubIndustry(
                value="Museums, Historical Sites, & Zoos",
                id=29,
                coresignal=[
                    "Museums, Historical Sites, and Zoos",
                    "Museums",
                    "Historical Sites",
                    "Zoos and Botanical Gardens"
                ]
            ),
            SubIndustry(
                value="Wellness & Fitness Services",
                id=35,
                coresignal=["Wellness and Fitness Services",
                            "Health, Wellness & Fitness"]
            ),
            SubIndustry(
                value="Gambling Facilities & Casinos",
                id=34,
                coresignal=["Gambling Facilities and Casinos",
                            "Gambling & Casinos"]
            ),
            SubIndustry(
                value="Entertainment Providers",
                id=28,
                coresignal=["Entertainment Providers", "Entertainment"]
            ),
            SubIndustry(
                value="Sports",
                id=32,
                coresignal=[
                    "Sports",
                    "Sports Teams and Clubs",
                    "Sports and Recreation Instruction",
                    "Spectator Sports"
                ]
            ),
            SubIndustry(
                value="Musicians, Artists & Writers",
                id=30,
                coresignal=["Musicians", "Artists and Writers"]
            ),
            SubIndustry(value="Other (Entertainment)", id=795)
        ]
    ),

    MainIndustry(
        main_industry="Farming, Ranching, Forestry",
        main_industry_id=8,
        sub_industries=[
            SubIndustry(
                value="Farming, Ranching, Forestry",
                id=36,
                coresignal=[
                    "Farming, Ranching, Forestry",
                    "Farming",
                    "Forestry and Logging",
                    "Ranching and Fisheries"
                ]
            )
        ]
    ),

    MainIndustry(
        main_industry="Finance",
        main_industry_id=9,
        sub_industries=[
            SubIndustry(
                value="International Trade & Development",
                id=43,
                coresignal=["International Trade & Development",
                            "International Trade and Development"]
            ),
            SubIndustry(value="Capital Markets", id=38,
                        coresignal=["Capital Markets"]),
            SubIndustry(
                value="Venture Capital & Private Equity Principals",
                id=41,
                coresignal=["Venture Capital and Private Equity Principals",
                            "Venture Capital & Private Equity"]
            ),
            SubIndustry(
                value="Insurance",
                id=44,
                coresignal=["Insurance", "Insurance Agencies and Brokerages",
                            "Insurance and Employee Benefit Funds"]
            ),
            SubIndustry(value="Investment Banking", id=39,
                        coresignal=["Investment Banking"]),
            SubIndustry(value="Banking", id=42, coresignal=["Banking"]),
            SubIndustry(
                value="Investment Management",
                id=40,
                coresignal=["Investment Management", "Funds and Trusts"]
            ),
            SubIndustry(value="Other (Finance)", id=797),
            SubIndustry(
                value="Financial Services",
                id=37,
                coresignal=["Financial Services",
                            "Investment Advice", "Credit Intermediation"]
            )
        ]
    ),

    MainIndustry(
        main_industry="Government",
        main_industry_id=10,
        sub_industries=[
            SubIndustry(
                value="Government Relations Services",
                id=58,
                coresignal=["Government Relations Services",
                            "Government Relations"]
            ),
            SubIndustry(
                value="International Affairs",
                id=54,
                coresignal=["International Affairs",
                            "Military and International Affairs"]
            ),
            SubIndustry(value="Public Safety", id=49,
                        coresignal=["Public Safety"]),
            SubIndustry(
                value="Legislative Offices",
                id=57,
                coresignal=["Legislative Offices", "Legislative Office"]
            ),
            SubIndustry(value="Government Administration", id=45,
                        coresignal=["Government Administration"]),
            SubIndustry(
                value="Education Administration Programs",
                id=50,
                coresignal=["Education Administration Programs"]
            ),
            SubIndustry(value="Military", id=53, coresignal=[
                        "Military", "Armed Forces"]),
            SubIndustry(
                value="Administration of Justice",
                id=46,
                coresignal=["Administration of Justice", "Courts of Law"]
            ),
            SubIndustry(value="Other (Government)", id=779),
            SubIndustry(
                value="Public Policy Offices",
                id=55,
                coresignal=["Public Policy Offices", "Public Policy"]
            ),
            SubIndustry(
                value="Health & Human Services",
                id=51,
                coresignal=["Health and Human Services", "Public Health"]
            ),
            SubIndustry(
                value="Housing & Community Development",
                id=52,
                coresignal=["Housing and Community Development",
                            "Community Development and Urban Planning"]
            ),
            SubIndustry(value="Executive Offices", id=56, coresignal=[
                        "Executive Offices", "Executive Office"]),
            SubIndustry(value="Law Enforcement", id=48,
                        coresignal=["Law Enforcement"]),
            SubIndustry(value="Fire Protection", id=47,
                        coresignal=["Fire Protection"])
        ]
    ),

    MainIndustry(
        main_industry="Hospitals, Healthcare & Clinics",
        main_industry_id=11,
        sub_industries=[
            SubIndustry(value="Mental Health Care", id=64,
                        coresignal=["Mental Health Care"]),
            SubIndustry(
                value="Individual & Family Services",
                id=61,
                coresignal=["Individual & Family Services",
                            "Individual and Family Services"]
            ),
            SubIndustry(value="Alternative Medicine", id=62,
                        coresignal=["Alternative Medicine"]),
            SubIndustry(
                value="Other (Hospitals, Healthcare & Clinics)", id=780),
            SubIndustry(
                value="Medical Practices",
                id=65,
                coresignal=["Medical Practices", "Medical Practice"]
            ),
            SubIndustry(
                value="Hospitals & Healthcare",
                id=59,
                coresignal=["Hospitals and Health Care",
                            "Hospital & Health Care", "Hospitals"]
            ),
            SubIndustry(value="Community Services", id=60,
                        coresignal=["Community Services"]),
            SubIndustry(
                value="Nursing Homes & Residential Care Facilities",
                id=66,
                coresignal=["Nursing Homes and Residential Care Facilities"]
            ),
            SubIndustry(value="Home Health Care Services", id=63,
                        coresignal=["Home Health Care Services"])
        ]
    ),

    MainIndustry(
        main_industry="Manufacturing",
        main_industry_id=12,
        sub_industries=[
            SubIndustry(
                value="Food & Beverage",
                id=76,
                coresignal=["Food and Beverage Manufacturing",
                            "Food Production", "Beverage Manufacturing"]
            ),
            SubIndustry(
                value="Pharmaceuticals",
                id=71,
                coresignal=["Pharmaceuticals", "Pharmaceutical Manufacturing"]
            ),
            SubIndustry(
                value="Medical Equipment",
                id=80,
                coresignal=[
                    "Medical Equipment Manufacturing", "Medical Device"]
            ),
            SubIndustry(
                value="Apparel",
                id=67,
                coresignal=["Apparel Manufacturing", "Apparel & Fashion",
                            "Fashion Accessories Manufacturing"]
            ),
            SubIndustry(
                value="Chemicals & Related Products",
                id=69,
                coresignal=["Chemicals", "Chemical Manufacturing",
                            "Chemical Raw Materials Manufacturing"]
            ),
            SubIndustry(
                value="Plastics & Rubber Products",
                id=82,
                coresignal=["Plastics and Rubber Product Manufacturing",
                            "Plastics", "Rubber Products Manufacturing"]
            ),
            SubIndustry(
                value="Paper & Forest Product",
                id=81,
                coresignal=["Paper and Forest Product Manufacturing",
                            "Paper & Forest Products"]
            ),
            SubIndustry(
                value="Furniture",
                id=77,
                coresignal=[
                    "Furniture",
                    "Furniture and Home Furnishings Manufacturing",
                    "Household and Institutional Furniture Manufacturing"
                ]
            ),
            SubIndustry(
                value="Computer Hardware",
                id=73,
                coresignal=["Computer Hardware",
                            "Computer Hardware Manufacturing"]
            ),
            SubIndustry(value="Tobacco", id=85, coresignal=[
                        "Tobacco Manufacturing", "Tobacco"]),
            SubIndustry(value="Shipbuilding", id=89,
                        coresignal=["Shipbuilding"]),
            SubIndustry(
                value="Appliances, Electrical, & Electronics",
                id=68,
                coresignal=["Appliances, Electrical, and Electronics Manufacturing",
                            "Electrical & Electronic Manufacturing"]
            ),
            SubIndustry(value="Railroad Equipment", id=88, coresignal=[
                        "Railroad Equipment Manufacturing"]),
            SubIndustry(value="Computer Equipment & Electronics", id=72, coresignal=[
                        "Computers and Electronics Manufacturing"]),
            SubIndustry(
                value="Personal Care Products",
                id=70,
                coresignal=["Personal Care Product Manufacturing", "Cosmetics"]
            ),
            SubIndustry(value="Fabricated Metal Products", id=75,
                        coresignal=["Fabricated Metal Products"]),
            SubIndustry(value="Sporting Goods", id=83, coresignal=[
                        "Sporting Goods", "Sporting Goods Manufacturing"]),
            SubIndustry(value="Textile", id=84, coresignal=[
                        "Textile Manufacturing", "Textiles"]),
            SubIndustry(
                value="Glass, Ceramics, Clay & Concrete",
                id=78,
                coresignal=[
                    "Glass, Ceramics and Concrete Manufacturing", "Glass, Ceramics & Concrete"]
            ),
            SubIndustry(
                value="Motor Vehicles",
                id=87,
                coresignal=["Motor Vehicle Manufacturing",
                            "Motor Vehicle Parts Manufacturing"]
            ),
            SubIndustry(
                value="Industrial Machinery & Equipment",
                id=79,
                coresignal=["Industrial Machinery Manufacturing",
                            "Machinery", "Automation Machinery Manufacturing"]
            ),
            SubIndustry(
                value="Semiconductor & Renewable Energy Semiconductor",
                id=74,
                coresignal=[
                    "Semiconductor Manufacturing",
                    "Renewable Energy Semiconductor Manufacturing",
                    "Semiconductors"
                ]
            ),
            SubIndustry(value="Other (Manufacturing)", id=781),
            SubIndustry(
                value="Aerospace & Defense",
                id=86,
                coresignal=[
                    "Aviation & Aerospace",
                    "Defense & Space",
                    "Defense and Space Manufacturing",
                    "Aviation and Aerospace Component Manufacturing"
                ]
            )
        ]
    ),

    MainIndustry(
        main_industry="Oil, Gas & Mining",
        main_industry_id=13,
        sub_industries=[
            SubIndustry(value="Oil & Gas", id=91, coresignal=[
                        "Oil & Energy", "Oil and Gas"]),
            SubIndustry(value="Mining", id=90, coresignal=[
                        "Mining", "Mining & Metals", "Metal Ore Mining"]),
            SubIndustry(value="Other (Oil, Gas & Mining)", id=782)
        ]
    ),

    MainIndustry(
        main_industry="Business Services",
        main_industry_id=14,
        sub_industries=[
            SubIndustry(
                value="Biotechnology Research Services",
                id=106,
                coresignal=["Biotechnology Research",
                            "Biotechnology", "Nanotechnology Research"]
            ),
            SubIndustry(value="Photography Services",
                        id=105, coresignal=["Photography"]),
            SubIndustry(
                value="Environmental Services",
                id=98,
                coresignal=["Environmental Services",
                            "Environmental Quality Programs"]
            ),
            SubIndustry(
                value="Business Consulting & Services",
                id=97,
                coresignal=[
                    "Business Consulting and Services",
                    "Professional Services",
                    "Operations Consulting",
                    "Strategic Management Services"
                ]
            ),
            SubIndustry(
                value="Human Resources Services",
                id=99,
                coresignal=["Human Resources Services",
                            "Human Resources", "Executive Search Services"]
            ),
            SubIndustry(
                value="Public Relations & Communications Services",
                id=94,
                coresignal=["Public Relations and Communications Services",
                            "Public Relations & Communications"]
            ),
            SubIndustry(value="IT Consulting & IT Services", id=103,
                        coresignal=["IT Services and IT Consulting"]),
            SubIndustry(
                value="Advertising & Marketing Services",
                id=93,
                coresignal=["Marketing & Advertising",
                            "Advertising Services", "Marketing Services"]
            ),
            SubIndustry(value="Market Research Services",
                        id=95, coresignal=["Market Research"]),
            SubIndustry(value="Law Firms & Legal Services", id=104,
                        coresignal=["Legal Services", "Law Practice"]),
            SubIndustry(
                value="Outsourcing & Offshoring Consulting",
                id=100,
                coresignal=["Outsourcing and Offshoring Consulting",
                            "Outsourcing/Offshoring"]
            ),
            SubIndustry(value="Other (Business Services)", id=783),
            SubIndustry(value="Veterinary Services", id=108, coresignal=[
                        "Veterinary Services", "Veterinary"]),
            SubIndustry(value="Research Services", id=107,
                        coresignal=["Research Services", "Research"]),
            SubIndustry(
                value="Architecture & Planning",
                id=96,
                coresignal=["Architecture & Planning",
                            "Architecture and Planning"]
            ),
            SubIndustry(
                value="Design Services",
                id=101,
                coresignal=["Design Services", "Design", "Graphic Design"]
            ),
            SubIndustry(value="Accounting & Services",
                        id=92, coresignal=["Accounting"])
        ]
    ),

    MainIndustry(
        main_industry="Real Estate",
        main_industry_id=15,
        sub_industries=[
            SubIndustry(
                value="Real Estate",
                id=109,
                coresignal=[
                    "Real Estate",
                    "Commercial Real Estate",
                    "Real Estate Agents and Brokers",
                    "Leasing Non-residential Real Estate",
                    "Leasing Residential Real Estate",
                    "Real Estate and Equipment Rental Services"
                ]
            )
        ]
    ),

    MainIndustry(
        main_industry="Retail",
        main_industry_id=16,
        sub_industries=[
            SubIndustry(
                value="Retail Apparel & Fashion",
                id=113,
                coresignal=["Retail Apparel and Fashion", "Apparel & Fashion"]
            ),
            SubIndustry(value="Retail Luxury Goods & Jewelry",
                        id=110, coresignal=["Luxury Goods & Jewelry"]),
            SubIndustry(value="Other (Retail)", id=785),
            SubIndustry(value="Grocery Retail", id=112, coresignal=[
                        "Retail Groceries", "Supermarkets"]),
            SubIndustry(value="Retail Office Equipment", id=114,
                        coresignal=["Retail Office Equipment"]),
            SubIndustry(value="Food & Beverage Retail", id=111,
                        coresignal=["Food and Beverage Retail"]),
            SubIndustry(value="Retail", id=115, coresignal=[
                        "Retail", "Online and Mail Order Retail"])
        ]
    ),

    MainIndustry(
        main_industry="Technology, Information & Media",
        main_industry_id=17,
        sub_industries=[
            SubIndustry(
                value="Book & Newspaper Publishing",
                id=116,
                coresignal=[
                    "Book and Periodical Publishing",
                    "Newspaper Publishing",
                    "Book Publishing",
                    "Periodical Publishing"
                ]
            ),
            SubIndustry(
                value="Internet Publishing",
                id=123,
                coresignal=["Internet Publishing",
                            "Online Media", "Internet News", "Blogs"]
            ),
            SubIndustry(
                value="Computer & Mobile Games",
                id=126,
                coresignal=["Computer Games",
                            "Mobile Games", "Mobile Gaming Apps"]
            ),
            SubIndustry(value="Blockchain Services", id=121,
                        coresignal=["Blockchain Services"]),
            SubIndustry(
                value="Software Development",
                id=129,
                coresignal=[
                    "Software Development",
                    "Computer Software",
                    "IT System Custom Software Development",
                    "Embedded Software Products",
                    "Desktop Computing Software Products",
                    "Mobile Computing Software Products"
                ]
            ),
            SubIndustry(
                value="Other (Technology, Information & Media)", id=786),
            SubIndustry(
                value="Movies, Videos & Sound",
                id=118,
                coresignal=[
                    "Movies, Videos, and Sound",
                    "Movies and Sound Recording",
                    "Sound Recording",
                    "Motion Pictures & Film"
                ]
            ),
            SubIndustry(value="Information Services", id=122,
                        coresignal=["Information Services"]),
            SubIndustry(
                value="Internet Shop & Marketplace",
                id=124,
                coresignal=["Internet Marketplace Platforms",
                            "Online and Mail Order Retail"]
            ),
            SubIndustry(
                value="Broadcast Media Production & Distribution",
                id=117,
                coresignal=[
                    "Broadcast Media Production and Distribution",
                    "Broadcast Media",
                    "Radio and Television Broadcasting",
                    "Cable and Satellite Programming"
                ]
            ),
            SubIndustry(value="Social Networking Platforms", id=125,
                        coresignal=["Social Networking Platforms"]),
            SubIndustry(
                value="Computer & Network Security Services",
                id=128,
                coresignal=[
                    "Computer and Network Security",
                    "Computer & Network Security",
                    "Data Security Software Products"
                ]
            ),
            SubIndustry(
                value="Computer Networking Products",
                id=127,
                coresignal=["Computer Networking Products",
                            "Computer Networking"]
            ),
            SubIndustry(
                value="Data Infrastructure & Analytics",
                id=120,
                coresignal=[
                    "Data Infrastructure and Analytics",
                    "Business Intelligence Platforms",
                    "Climate Data and Analytics"
                ]
            ),
            SubIndustry(
                value="Telecommunications",
                id=119,
                coresignal=[
                    "Telecommunications",
                    "Telecommunications Carriers",
                    "Wireless",
                    "Wireless Services",
                    "Media and Telecommunications"
                ]
            )
        ]
    ),

    MainIndustry(
        main_industry="Transportation, Logistics, Supply Chain & Storage",
        main_industry_id=18,
        sub_industries=[
            SubIndustry(
                value="Other (Transportation, Logistics, Supply Chain & Storage)", id=787),
            SubIndustry(
                value="Airlines, Airports & Air Services",
                id=130,
                coresignal=["Airlines and Aviation", "Airlines/Aviation"]
            ),
            SubIndustry(value="Maritime Transportation", id=133,
                        coresignal=["Maritime Transportation", "Maritime"]),
            SubIndustry(value="Truck Transportation", id=134,
                        coresignal=["Truck Transportation"]),
            SubIndustry(
                value="Freight & Package Transportation",
                id=131,
                coresignal=["Freight and Package Transportation",
                            "Package/Freight Delivery"]
            ),
            SubIndustry(
                value="Ground Passenger Transportation",
                id=132,
                coresignal=[
                    "Ground Passenger Transportation",
                    "Taxi and Limousine Services",
                    "Urban Transit Services",
                    "Rail Transportation"
                ]
            ),
            SubIndustry(
                value="Warehousing & Storage",
                id=135,
                coresignal=[
                    "Warehousing and Storage",
                    "Warehousing",
                    "Logistics & Supply Chain",
                    "Transportation, Logistics, Supply Chain and Storage"
                ]
            )
        ]
    ),

    MainIndustry(
        main_industry="Utilities",
        main_industry_id=19,
        sub_industries=[
            SubIndustry(value="Utilities", id=136, coresignal=["Utilities"])
        ]
    ),

    MainIndustry(
        main_industry="Wholesale",
        main_industry_id=20,
        sub_industries=[
            SubIndustry(value="Other (Wholesale)", id=790),
            SubIndustry(value="Wholesale", id=137, coresignal=["Wholesale"]),
            SubIndustry(value="Wholesale Building Materials", id=138,
                        coresignal=["Wholesale Building Materials"]),
            SubIndustry(
                value="Wholesale Import & Export",
                id=139,
                coresignal=["Wholesale Import and Export", "Import & Export"]
            )
        ]
    )
]
