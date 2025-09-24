
# Original mapping: Category -> List of departments
DEPARTMENT_CATEGORIES = {
    "Business Development": ["Business Development", "Entrepreneurship"],
    "Consulting": ["Consulting"],
    "Customer Service": ["Customer Success and Support"],
    "Engineering & Technical": ["Engineering"],
    "Finance": ["Finance", "Accounting"],
    "General Management": ["Program and Project Management", "Administrative"],
    "Health Care & Medical": ["Healthcare Services"],
    "Human Resources": ["Human Resources"],
    "Information Technology": ["Information Technology"],
    "Legal": ["Legal"],
    "Marketing": ["Marketing", "Media and Communication"],
    "Operations": ["Operations", "Purchasing", "Quality Assurance"],
    "Other": [
        "Arts and Design",
        "Community and Social Services",
        "Education",
        "Military and Protective Services",
        "Real Estate"
    ],
    "Product": ["Product Management"],
    "Research & Analytics": ["Research"],
    "Sales": ["Sales"]
}

# Reverse mapping: Department -> Category (what you requested)
DEPARTMENT_TO_CATEGORY = {
    # Business Development
    "Business Development": "Business Development",
    "Entrepreneurship": "Business Development",

    # Consulting
    "Consulting": "Consulting",

    # Customer Service
    "Customer Success and Support": "Customer Service",

    # Engineering & Technical
    "Engineering": "Engineering & Technical",

    # Finance
    "Finance": "Finance",
    "Accounting": "Finance",

    # General Management
    "Program and Project Management": "General Management",
    "Administrative": "General Management",

    # Health Care & Medical
    "Healthcare Services": "Health Care & Medical",

    # Human Resources
    "Human Resources": "Human Resources",

    # Information Technology
    "Information Technology": "Information Technology",

    # Legal
    "Legal": "Legal",

    # Marketing
    "Marketing": "Marketing",
    "Media and Communication": "Marketing",

    # Operations
    "Operations": "Operations",
    "Purchasing": "Operations",
    "Quality Assurance": "Operations",

    # Other
    "Arts and Design": "Other",
    "Community and Social Services": "Other",
    "Education": "Other",
    "Military and Protective Services": "Other",
    "Real Estate": "Other",

    # Product
    "Product Management": "Product",

    # Research & Analytics
    "Research": "Research & Analytics",

    # Sales
    "Sales": "Sales"
}
