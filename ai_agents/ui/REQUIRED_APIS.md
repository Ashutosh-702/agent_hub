# Required APIs for the UI

This doc lists backend APIs the UI depends on, split into:
- **Already Available (exists today)**: the backend already has these and the UI already calls them.
- **To Build (missing)**: the UI currently uses **mock data** for these and needs real APIs.

---

## Already Available (exists today)

- **GET** `/api/v1/campaigns?page=1&limit=12`
- **GET** `/api/v1/campaign_details_with_companies?campaign_id=...&company_status=true|false&page=1&limit=10`
- **GET** `/api/v1/companies?page=1&limit=10&name=acme`
- **GET** `/api/v1/company_details_with_contacts?company_id=...&page=1&limit=5`
- **POST** `/api/v1/sheets/upload_data_from_form` (legacy create-campaign form)

---

## To Build (missing)

### A) Campaign manual shortlisting updates (currently mocked)

#### 1) Manual shortlist update (company)
Used only when `shortlisting_approach` is `manual_company` OR `overall_manual`.

- **PATCH** `/api/v1/campaign_company_status`

Request:

```json
{ "campaign_company_id": "string", "company_status": true }
```

Response:

```json
{ "success": true }
```

#### 2) Manual shortlist update (contact)
Used only when:
- user navigated from **Campaign → Company**, and
- campaign `shortlisting_approach` is `overall_manual`

- **PATCH** `/api/v1/contact_shortlist_status`

Request:

```json
{ "contact_id": "string", "shortlisted": true }
```

Response:

```json
{ "success": true }
```

---

### B) Prospecting Wizard (Figma) (currently mocked)

#### 3) Start “Find Prospects” job
- **POST** `/api/v1/prospecting/start_import_job`

Request:

```json
{
  "filters": {
    "industry": ["SaaS"],
    "region": ["US"],
    "company_size": "50-200",
    "titles": ["VP Engineering"]
  }
}
```

Response:

```json
{ "success": true, "data": { "job_id": "string" } }
```

#### 4) Import job status/progress (Import Job screen)
- **GET** `/api/v1/prospecting/import_job_status?job_id=...`

Response:

```json
{
  "success": true,
  "data": {
    "job_id": "string",
    "status": "running|completed|failed",
    "progress_pct": 42,
    "steps": {
      "searching_apollo": "done|active|pending",
      "dedupe": "done|active|pending",
      "group_by_company": "done|active|pending"
    }
  }
}
```

#### 5) Import job result stats (Contacts/Companies found)
- **GET** `/api/v1/prospecting/import_job_result?job_id=...`

Response:

```json
{ "success": true, "data": { "job_id": "string", "contacts_found": 384, "companies_found": 52 } }
```

#### 6) Prospects by company (Review Prospects expandable table)
- **GET** `/api/v1/prospecting/prospects_by_company?job_id=...&page=1&limit=20&query=...`

Response:

```json
{
  "success": true,
  "data": {
    "companies": [
      {
        "company_id": "string",
        "company_name": "TechCorp Inc",
        "company_domain": "techcorp.com",
        "region": "US",
        "size": "500-1000",
        "contacts_count": 3,
        "contacts": [
          { "contact_id": "string", "name": "Sarah Chen", "title": "VP of Engineering", "confidence": "high" }
        ]
      }
    ]
  },
  "pagination": { "page_size": 20, "page_number": 1, "has_next": false, "total_records": 1 }
}
```

#### 7) Save review selections (companies + contacts)
- **POST** `/api/v1/prospecting/save_selection`

Request:

```json
{
  "job_id": "string",
  "selected_company_ids": ["string"],
  "selected_contact_ids": ["string"]
}
```

Response:

```json
{ "success": true }
```

#### 8) Convert job → campaign (optional; replaces redirect to legacy form)
- **POST** `/api/v1/campaigns/create_from_prospecting_job`

Request:

```json
{
  "job_id": "string",
  "selected_company_ids": ["string"],
  "selected_contact_ids": ["string"],
  "ownership": {
    "hubspot_email": "string",
    "product_name": "string",
    "business_team": "string",
    "user_email": "string"
  },
  "shortlisting_approach": "overall_ai"
}
```

Response:

```json
{ "success": true, "data": { "campaign_id": "string" } }
```


