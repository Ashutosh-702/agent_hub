# AI SDR - API Specifications

## Document Information

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Created | December 28, 2024 |
| Base URL | `/api/v1/wizard` |
| Database Reference | `docs/database-design-ai-sdr.md` |

---

## Table of Contents

1. [Overview](#1-overview)
2. [Authentication APIs](#2-authentication-apis)
3. [Campaign Management APIs](#3-campaign-management-apis)
4. [Step 1: Prospecting APIs](#4-step-1-prospecting-apis)
5. [Step 2: Company Qualification APIs](#5-step-2-company-qualification-apis)
6. [Step 3: Contact Qualification APIs](#6-step-3-contact-qualification-apis)
7. [Step 4: HubSpot Sync APIs](#7-step-4-hubspot-sync-apis)
8. [Step 5: Personalization APIs](#8-step-5-personalization-apis)
9. [Step 6: Enrollment APIs](#9-step-6-enrollment-apis)
10. [Job Management APIs](#10-job-management-apis)
11. [API Summary Table](#11-api-summary-table)

---

## 1. Overview

### 1.1 Common Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | `Bearer <token>` |
| `Content-Type` | Yes (POST/PUT/PATCH) | `application/json` |
| `X-Request-ID` | No | Client-generated request ID |

### 1.2 Response Format

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "pagination": {
    "cursor": "eyJsYXN0X2lkIjoi...",
    "has_more": true,
    "total_count": 150
  }
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [{ "field": "email", "message": "Invalid format" }]
  }
}
```

### 1.3 Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `UNAUTHORIZED` | 401 | Invalid/missing auth |
| `FORBIDDEN` | 403 | No access |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid params |
| `CONFLICT` | 409 | State conflict |
| `CONFIRMATION_REQUIRED` | 409 | Needs user confirmation |
| `RATE_LIMITED` | 429 | Too many requests |
| `REGENERATION_LIMIT_EXCEEDED` | 429 | Max 5 regenerations |
| `JOB_FAILED` | 500 | Background job failed |
| `EXTERNAL_SERVICE_ERROR` | 502 | Third-party API error |

### 1.4 Cursor Pagination

All list endpoints use cursor-based pagination:
- Request: `?cursor=<base64_encoded>&limit=10`
- Response includes `pagination.cursor` for next page
- Cursor encodes: `{ last_id: ObjectId, last_created_at: Date }`

---

## 2. Authentication APIs

### 2.1 Login

**POST** `/api/v1/auth/login`

**UI Mapping:** Login form submission

**Request:**
```json
{
  "email": "admin@fynd.com",
  "password": "admin123"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": "user_001",
      "email": "admin@fynd.com",
      "name": "Admin User"
    },
    "expires_at": "2025-01-28T10:30:00Z"
  }
}
```

**Implementation Notes:**
- Hardcoded credentials: `admin@fynd.com` / `admin123`
- Token expires in 24 hours
- Store `user_id` in JWT payload

---

### 2.2 Validate Token

**GET** `/api/v1/auth/validate`

**UI Mapping:** App initialization, route guards

**Response (200):**
```json
{
  "success": true,
  "data": {
    "valid": true,
    "user": {
      "id": "user_001",
      "email": "admin@fynd.com",
      "name": "Admin User"
    }
  }
}
```

---

## 3. Campaign Management APIs

### 3.1 List Campaigns

**GET** `/api/v1/wizard/campaigns`

**UI Mapping:** Campaign List View - Table data

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `cursor` | string | null | Pagination cursor |
| `limit` | int | 10 | Max 50 |
| `status` | string | null | Filter by status |

**Database Query:**
```javascript
db.wizard_campaigns.find({
  is_deleted: false,
  "ownership.user_id": "<user_id>",
  ...(cursor ? { _id: { $lt: ObjectId(cursor) } } : {}),
  ...(status ? { status } : {})
})
.sort({ created_at: -1 })
.limit(limit + 1)
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "campaigns": [
      {
        "id": "camp_abc123",
        "name": "Q1 2025 Enterprise Outreach",
        "status": "company_qualification",
        "current_step": 2,
        "created_at": "2024-12-25T10:30:00Z",
        "updated_at": "2024-12-26T14:20:00Z",
        "metrics": {
          "companies_prospected": 120,
          "companies_qualified": 45,
          "contacts_qualified": 89,
          "contacts_synced": 34,
          "contacts_personalized": 30,
          "contacts_enrolled": 25
        },
        "ownership": {
          "user_id": "user_001",
          "user_email": "john@company.com",
          "product_name": "Enterprise Suite"
        }
      }
    ]
  },
  "pagination": {
    "cursor": "eyJsYXN0X2lkIjoiY2FtcF9hYmMxMjMifQ==",
    "has_more": true,
    "total_count": 45
  }
}
```

---

### 3.2 Create Campaign

**POST** `/api/v1/wizard/campaigns`

**UI Mapping:** "New Campaign" button

**Request:**
```json
{
  "name": "Q1 2025 Enterprise Outreach"
}
```

**Database Operation:**
```javascript
db.wizard_campaigns.insertOne({
  name: request.name,
  status: "draft",
  current_step: 1,
  ownership: {
    user_id: auth.user_id,
    user_email: auth.user_email
  },
  metrics: { /* all zeros - see default values */ },
  is_deleted: false,
  created_at: new Date(),
  updated_at: new Date()
})
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "campaign": {
      "id": "camp_xyz789",
      "name": "Q1 2025 Enterprise Outreach",
      "status": "draft",
      "current_step": 1,
      "created_at": "2024-12-27T10:30:00Z"
    }
  }
}
```

---

### 3.3 Get Campaign Details

**GET** `/api/v1/wizard/campaigns/{campaign_id}`

**UI Mapping:** Wizard initialization, Campaign Details View

**Database Query:**
```javascript
db.wizard_campaigns.findOne({
  _id: ObjectId(campaign_id),
  is_deleted: false
})
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "campaign": {
      "id": "camp_xyz789",
      "name": "Q1 2025 Enterprise Outreach",
      "status": "company_qualification",
      "current_step": 2,
      "filters": {
        "industries": ["Software & Technology"],
        "regions": ["North America"],
        "employee_counts": ["51-200", "201-500"],
        "revenue_min": 1000000,
        "revenue_max": 50000000
      },
      "company_qualification": {
        "mode": "ai",
        "criteria": {
          "has_engineering_team": true,
          "is_hiring_technical": false,
          "uses_cloud_solutions": true,
          "recent_funding": true,
          "growth_phase": false
        }
      },
      "metrics": { /* ... */ },
      "ownership": { /* ... */ },
      "created_at": "2024-12-27T10:30:00Z",
      "updated_at": "2024-12-27T14:30:00Z"
    }
  }
}
```

---

### 3.4 Update Campaign

**PATCH** `/api/v1/wizard/campaigns/{campaign_id}`

**UI Mapping:** Update campaign name, ownership details

**Request:**
```json
{
  "name": "Updated Campaign Name",
  "ownership": {
    "product_name": "Enterprise Suite Pro",
    "hubspot_email": "sales@company.com",
    "business_team": "North America"
  }
}
```

**Database Operation:**
```javascript
db.wizard_campaigns.updateOne(
  { _id: ObjectId(campaign_id), is_deleted: false },
  {
    $set: {
      name: request.name,
      "ownership.product_name": request.ownership.product_name,
      "ownership.hubspot_email": request.ownership.hubspot_email,
      "ownership.business_team": request.ownership.business_team,
      updated_at: new Date()
    }
  }
)
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "campaign": {
      "id": "camp_xyz789",
      "name": "Updated Campaign Name",
      "updated_at": "2024-12-27T15:00:00Z"
    }
  }
}
```

---

### 3.5 Navigate Campaign Step

**POST** `/api/v1/wizard/campaigns/{campaign_id}/navigate`

**UI Mapping:** Stepper clicks (backward), Continue buttons (forward)

**Request:**
```json
{
  "target_step": 1,
  "confirm_reset": true
}
```

**Business Logic:**
1. If `target_step > current_step`: Just update step (forward navigation)
2. If `target_step < current_step`: Requires `confirm_reset: true`
   - Delete companies from step 2+
   - Delete contacts from step 3+
   - Delete personalizations from step 5+
   - Reset metrics

**Database Operations (Backward with Reset):**
```javascript
// 1. Calculate affected steps
const affected_steps = range(target_step + 1, current_step + 1);

// 2. Soft delete companies (if step 2+ affected)
if (affected_steps.includes(2)) {
  db.wizard_companies.updateMany(
    { campaign_id: ObjectId(campaign_id) },
    { $set: { is_deleted: true, deleted_at: new Date() } }
  );
}

// 3. Soft delete contacts (if step 3+ affected)
if (affected_steps.includes(3)) {
  db.wizard_contacts.updateMany(
    { campaign_id: ObjectId(campaign_id) },
    { $set: { is_deleted: true, deleted_at: new Date() } }
  );
}

// 4. Soft delete personalizations (if step 5+ affected)
if (affected_steps.includes(5)) {
  db.wizard_personalizations.updateMany(
    { campaign_id: ObjectId(campaign_id) },
    { $set: { is_deleted: true, deleted_at: new Date() } }
  );
}

// 5. Update campaign
db.wizard_campaigns.updateOne(
  { _id: ObjectId(campaign_id) },
  {
    $set: {
      current_step: target_step,
      status: getStatusForStep(target_step),
      // Reset metrics for affected steps
      "metrics.companies_qualified": 0,
      // ... other metric resets
      updated_at: new Date()
    }
  }
)
```

**Response (200 - Success):**
```json
{
  "success": true,
  "data": {
    "campaign": {
      "id": "camp_xyz789",
      "status": "prospecting",
      "current_step": 1
    },
    "reset_steps": [2, 3, 4, 5, 6],
    "message": "Steps 2-6 have been reset"
  }
}
```

**Response (409 - Confirmation Required):**
```json
{
  "success": false,
  "error": {
    "code": "CONFIRMATION_REQUIRED",
    "message": "Navigating backward will reset all subsequent steps",
    "details": [{
      "field": "confirm_reset",
      "message": "Set confirm_reset to true to proceed"
    }],
    "affected_steps": [2, 3, 4, 5, 6],
    "affected_data": {
      "companies_to_reset": 45,
      "contacts_to_reset": 89
    }
  }
}
```

---

### 3.6 Delete Campaign

**DELETE** `/api/v1/wizard/campaigns/{campaign_id}`

**UI Mapping:** Delete campaign action

**Database Operations:**
```javascript
// Soft delete cascade
const campaign_id = ObjectId(campaign_id);
const deleted_at = new Date();

db.wizard_campaigns.updateOne(
  { _id: campaign_id },
  { $set: { is_deleted: true, deleted_at } }
);

db.wizard_companies.updateMany(
  { campaign_id },
  { $set: { is_deleted: true, deleted_at } }
);

db.wizard_contacts.updateMany(
  { campaign_id },
  { $set: { is_deleted: true, deleted_at } }
);

db.wizard_personalizations.updateMany(
  { campaign_id },
  { $set: { is_deleted: true, deleted_at } }
);
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "deleted": true,
    "campaign_id": "camp_xyz789"
  }
}
```

---

## 4. Step 1: Prospecting APIs

### 4.1 Fetch Prospects

**POST** `/api/v1/wizard/campaigns/{campaign_id}/prospects/fetch`

**UI Mapping:** "Find Prospects" button, "Update Search" button

**Request:**
```json
{
  "filters": {
    "industries": ["Software & Technology", "Healthcare"],
    "regions": ["North America", "Europe"],
    "employee_counts": ["51-200", "201-500"],
    "revenue_min": 1000000,
    "revenue_max": 50000000
  }
}
```

**Business Logic:**
1. Create async job
2. Save filters to campaign
3. Worker calls Apollo API
4. Worker saves companies and contacts to database

**Database Operations:**
```javascript
// 1. Update campaign with filters
db.wizard_campaigns.updateOne(
  { _id: ObjectId(campaign_id) },
  {
    $set: {
      filters: request.filters,
      status: "prospecting",
      updated_at: new Date()
    }
  }
)

// 2. Create job
db.wizard_jobs.insertOne({
  campaign_id: ObjectId(campaign_id),
  type: "prospect_fetch",
  status: "pending",
  progress: { current: 0, total: 0, percentage: 0 },
  input: { filters: request.filters },
  created_at: new Date()
})
```

**Worker Process:**
```javascript
// 1. Call Apollo API with filters
const apolloResults = await apolloApi.searchCompanies(filters);

// 2. Insert companies
for (const company of apolloResults.companies) {
  db.wizard_companies.insertOne({
    campaign_id,
    source: "apollo",
    source_id: company.id,
    source_data: company,
    name: company.name,
    industry: company.industry,
    // ... other fields
    qualification: {
      status: "pending",
      method: null
    },
    hubspot: { sync_status: "not_synced" },
    is_deleted: false,
    created_at: new Date()
  });
  
  // 3. Insert contacts for each company
  for (const contact of company.contacts) {
    db.wizard_contacts.insertOne({
      campaign_id,
      company_id: companyDoc._id,
      source: "apollo",
      source_id: contact.id,
      // ... fields
      qualification: { status: "pending" },
      hubspot: { sync_status: "not_synced" },
      enrollment: { status: "not_enrolled" }
    });
  }
  
  // 4. Update progress
  db.wizard_jobs.updateOne(
    { _id: jobId },
    { $inc: { "progress.current": 1 }, $set: { "progress.percentage": ... } }
  );
}

// 5. Update campaign metrics
db.wizard_campaigns.updateOne(
  { _id: campaign_id },
  {
    $set: {
      "metrics.companies_prospected": totalCompanies,
      updated_at: new Date()
    }
  }
)

// 6. Complete job
db.wizard_jobs.updateOne(
  { _id: jobId },
  {
    $set: {
      status: "completed",
      result: { total_companies_found, total_contacts_found },
      completed_at: new Date()
    }
  }
)
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "job_id": "job_pros_abc123",
    "status": "pending",
    "message": "Prospect fetching job has been queued"
  }
}
```

---

### 4.2 List Prospected Companies

**GET** `/api/v1/wizard/campaigns/{campaign_id}/prospects`

**UI Mapping:** Prospect results list with pagination

**Query Parameters:**
| Param | Type | Default |
|-------|------|---------|
| `cursor` | string | null |
| `limit` | int | 10 |

**Database Query:**
```javascript
db.wizard_companies.aggregate([
  {
    $match: {
      campaign_id: ObjectId(campaign_id),
      is_deleted: false,
      ...(cursor ? { _id: { $lt: ObjectId(cursor) } } : {})
    }
  },
  {
    $lookup: {
      from: "wizard_contacts",
      let: { company_id: "$_id" },
      pipeline: [
        { $match: { $expr: { $eq: ["$company_id", "$$company_id"] }, is_deleted: false } },
        { $count: "count" }
      ],
      as: "contact_stats"
    }
  },
  {
    $addFields: {
      contact_count: { $ifNull: [{ $arrayElemAt: ["$contact_stats.count", 0] }, 0] }
    }
  },
  { $sort: { created_at: -1 } },
  { $limit: limit + 1 }
])
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "companies": [
      {
        "id": "comp_abc123",
        "name": "TechFlow Solutions",
        "industry": "Software & Technology",
        "employee_count": "51-200",
        "revenue": "$5M - $10M",
        "location": "United States",
        "website": "https://techflow.com",
        "linkedin_url": "https://linkedin.com/company/techflow",
        "contact_count": 5,
        "source": "apollo"
      }
    ]
  },
  "pagination": {
    "cursor": "eyJsYXN0X2lkIjoiY29tcF9hYmMxMjMifQ==",
    "has_more": true,
    "total_count": 156
  }
}
```

---

### 4.3 Confirm Prospecting & Proceed

**POST** `/api/v1/wizard/campaigns/{campaign_id}/prospects/confirm`

**UI Mapping:** "Continue to Qualification →" button

**Database Operation:**
```javascript
db.wizard_campaigns.updateOne(
  { _id: ObjectId(campaign_id) },
  {
    $set: {
      status: "company_qualification",
      current_step: 2,
      "step_timings.step_1_duration_seconds": calculateDuration(),
      updated_at: new Date()
    }
  }
)
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "campaign": {
      "id": "camp_xyz789",
      "status": "company_qualification",
      "current_step": 2,
      "metrics": { "companies_prospected": 156 }
    }
  }
}
```

---

## 5. Step 2: Company Qualification APIs

### 5.1 Set Company Qualification Mode

**POST** `/api/v1/wizard/campaigns/{campaign_id}/companies/qualification-mode`

**UI Mapping:** Mode selection cards (Manual/AI)

**Request:**
```json
{ "mode": "ai" }
```

**Database Operation:**
```javascript
db.wizard_campaigns.updateOne(
  { _id: ObjectId(campaign_id) },
  {
    $set: {
      "company_qualification.mode": request.mode,
      "company_qualification.started_at": new Date(),
      updated_at: new Date()
    }
  }
)
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "campaign": {
      "id": "camp_xyz789",
      "company_qualification_mode": "ai"
    }
  }
}
```

---

### 5.2 Run AI Company Qualification

**POST** `/api/v1/wizard/campaigns/{campaign_id}/companies/qualify-ai`

**UI Mapping:** "Run AI Qualification" button

**Request:**
```json
{
  "criteria": {
    "has_engineering_team": true,
    "is_hiring_technical": false,
    "uses_cloud_solutions": true,
    "recent_funding": true,
    "growth_phase": false
  }
}
```

**Database Operations:**
```javascript
// 1. Save criteria to campaign
db.wizard_campaigns.updateOne(
  { _id: ObjectId(campaign_id) },
  {
    $set: {
      "company_qualification.criteria": request.criteria,
      updated_at: new Date()
    }
  }
)

// 2. Create job
db.wizard_jobs.insertOne({
  campaign_id: ObjectId(campaign_id),
  type: "company_qualification_ai",
  status: "pending",
  input: { criteria: request.criteria },
  created_at: new Date()
})
```

**Worker Process:**
```javascript
// 1. Get all pending companies
const companies = db.wizard_companies.find({
  campaign_id,
  is_deleted: false,
  "qualification.status": "pending"
}).toArray();

// 2. For each company, call OpenAI
for (const company of companies) {
  const aiResult = await openai.chat({
    model: "gpt-4",
    messages: [
      { role: "system", content: "You are a B2B sales qualification expert..." },
      { role: "user", content: buildPrompt(company, criteria) }
    ]
  });
  
  const { qualified, confidence, reason } = parseAiResponse(aiResult);
  
  // 3. Update company with AI decision
  db.wizard_companies.updateOne(
    { _id: company._id },
    {
      $set: {
        "qualification.status": qualified ? "qualified" : "rejected",
        "qualification.method": "ai",
        "qualification.ai_decision": qualified,
        "qualification.ai_confidence": confidence,
        "qualification.ai_reason": reason,
        "qualification.ai_qualified_at": new Date(),
        "qualification.final_decision": qualified,
        "qualification.qualified_at": new Date(),
        updated_at: new Date()
      }
    }
  );
  
  // 4. If company rejected, auto-exclude its contacts
  if (!qualified) {
    db.wizard_contacts.updateMany(
      { company_id: company._id, is_deleted: false },
      {
        $set: {
          "qualification.status": "excluded",
          "qualification.method": "auto_excluded",
          "qualification.auto_excluded": true,
          "qualification.auto_excluded_at": new Date(),
          updated_at: new Date()
        }
      }
    );
  }
  
  // 5. Update job progress
  db.wizard_jobs.updateOne(
    { _id: jobId },
    { $inc: { "progress.current": 1 } }
  );
}

// 6. Update campaign metrics
const qualifiedCount = db.wizard_companies.countDocuments({
  campaign_id, "qualification.status": "qualified"
});
const rejectedCount = db.wizard_companies.countDocuments({
  campaign_id, "qualification.status": "rejected"
});

db.wizard_campaigns.updateOne(
  { _id: campaign_id },
  {
    $set: {
      "metrics.companies_qualified": qualifiedCount,
      "metrics.companies_rejected": rejectedCount,
      "metrics.ai_company_qualified": qualifiedCount,
      "metrics.ai_company_rejected": rejectedCount,
      updated_at: new Date()
    }
  }
)
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "job_id": "job_qual_comp_abc123",
    "status": "pending",
    "companies_to_process": 156
  }
}
```

---

### 5.3 Bulk Manual Company Qualification

**POST** `/api/v1/wizard/campaigns/{campaign_id}/companies/qualify-manual`

**UI Mapping:** Checkboxes, Select All, Company card clicks

**Request:**
```json
{
  "qualifications": [
    { "company_id": "comp_abc123", "qualified": true },
    { "company_id": "comp_def456", "qualified": false }
  ]
}
```

**Database Operations:**
```javascript
// Process each qualification
for (const q of request.qualifications) {
  db.wizard_companies.updateOne(
    { _id: ObjectId(q.company_id), campaign_id: ObjectId(campaign_id) },
    {
      $set: {
        "qualification.status": q.qualified ? "qualified" : "rejected",
        "qualification.method": "manual",
        "qualification.final_decision": q.qualified,
        "qualification.qualified_at": new Date(),
        updated_at: new Date()
      }
    }
  );
  
  // If rejected, auto-exclude contacts
  if (!q.qualified) {
    db.wizard_contacts.updateMany(
      { company_id: ObjectId(q.company_id), is_deleted: false },
      {
        $set: {
          "qualification.status": "excluded",
          "qualification.method": "auto_excluded",
          "qualification.auto_excluded": true,
          "qualification.auto_excluded_at": new Date(),
          updated_at: new Date()
        }
      }
    );
  }
}

// Update campaign metrics
const qualifiedCount = db.wizard_companies.countDocuments({
  campaign_id: ObjectId(campaign_id),
  is_deleted: false,
  "qualification.status": "qualified"
});

db.wizard_campaigns.updateOne(
  { _id: ObjectId(campaign_id) },
  {
    $set: {
      "metrics.companies_qualified": qualifiedCount,
      updated_at: new Date()
    }
  }
)
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "processed": 2,
    "qualified": 1,
    "rejected": 1
  }
}
```

---

### 5.4 Override AI Company Qualification

**POST** `/api/v1/wizard/campaigns/{campaign_id}/companies/override`

**UI Mapping:** "Qualify" button (on rejected), "Reject" button (on qualified)

**Request:**
```json
{
  "overrides": [
    {
      "company_id": "comp_abc123",
      "qualified": true,
      "override_reason": "Manual review indicates good fit"
    }
  ]
}
```

**Database Operations:**
```javascript
for (const o of request.overrides) {
  // Get original AI decision
  const company = db.wizard_companies.findOne({ _id: ObjectId(o.company_id) });
  
  db.wizard_companies.updateOne(
    { _id: ObjectId(o.company_id) },
    {
      $set: {
        "qualification.status": o.qualified ? "qualified" : "rejected",
        "qualification.is_overridden": true,
        "qualification.override_decision": o.qualified,
        "qualification.override_reason": o.override_reason,
        "qualification.overridden_at": new Date(),
        "qualification.final_decision": o.qualified,
        updated_at: new Date()
      }
    }
  );
  
  // Handle contact exclusion based on override
  if (!o.qualified) {
    // Reject → exclude contacts
    db.wizard_contacts.updateMany(
      { company_id: ObjectId(o.company_id), is_deleted: false },
      {
        $set: {
          "qualification.status": "excluded",
          "qualification.auto_excluded": true,
          updated_at: new Date()
        }
      }
    );
  } else if (company.qualification.ai_decision === false) {
    // Was rejected by AI, now qualified → un-exclude contacts
    db.wizard_contacts.updateMany(
      { company_id: ObjectId(o.company_id), is_deleted: false },
      {
        $set: {
          "qualification.status": "pending",
          "qualification.auto_excluded": false,
          updated_at: new Date()
        }
      }
    );
  }
}

// Update metrics
db.wizard_campaigns.updateOne(
  { _id: ObjectId(campaign_id) },
  {
    $inc: {
      "metrics.company_overrides_to_qualified": overridesToQualified,
      "metrics.company_overrides_to_rejected": overridesToRejected
    }
  }
)
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "overrides_applied": 1,
    "companies": [
      {
        "company_id": "comp_abc123",
        "original_decision": false,
        "overridden_to": true,
        "ai_reason": "Revenue below minimum requirement",
        "override_reason": "Manual review indicates good fit"
      }
    ]
  }
}
```

---

### 5.5 List Companies

**GET** `/api/v1/wizard/campaigns/{campaign_id}/companies`

**UI Mapping:** Company list (Manual/AI modes), Qualified/Rejected tabs

**Query Parameters:**
| Param | Type | Default |
|-------|------|---------|
| `cursor` | string | null |
| `limit` | int | 10 |
| `status` | string | null |

**Database Query:**
```javascript
db.wizard_companies.find({
  campaign_id: ObjectId(campaign_id),
  is_deleted: false,
  ...(status ? { "qualification.status": status } : {})
})
.sort({ created_at: -1 })
.limit(limit + 1)
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "companies": [
      {
        "id": "comp_abc123",
        "name": "TechFlow Solutions",
        "industry": "Software & Technology",
        "employee_count": "51-200",
        "revenue": "$5M - $10M",
        "location": "United States",
        "linkedin_url": "https://linkedin.com/company/techflow",
        "contact_count": 5,
        "qualification": {
          "status": "qualified",
          "method": "ai",
          "ai_decision": true,
          "ai_confidence": "high",
          "ai_reason": "Strong alignment with target criteria",
          "is_overridden": false
        }
      }
    ]
  },
  "pagination": { /* ... */ }
}
```

---

### 5.6 Confirm Company Qualification & Proceed

**POST** `/api/v1/wizard/campaigns/{campaign_id}/companies/confirm`

**UI Mapping:** "Continue with X Selected →" button

**Database Operations:**
```javascript
// Count qualified companies and their contacts
const qualifiedCompanyIds = db.wizard_companies.find({
  campaign_id: ObjectId(campaign_id),
  is_deleted: false,
  "qualification.status": "qualified"
}).map(c => c._id);

const contactCount = db.wizard_contacts.countDocuments({
  campaign_id: ObjectId(campaign_id),
  company_id: { $in: qualifiedCompanyIds },
  is_deleted: false,
  "qualification.status": { $ne: "excluded" }
});

db.wizard_campaigns.updateOne(
  { _id: ObjectId(campaign_id) },
  {
    $set: {
      status: "contact_qualification",
      current_step: 3,
      "metrics.contacts_extracted": contactCount,
      "company_qualification.completed_at": new Date(),
      "step_timings.step_2_duration_seconds": calculateDuration(),
      updated_at: new Date()
    }
  }
)
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "campaign": {
      "id": "camp_xyz789",
      "status": "contact_qualification",
      "current_step": 3,
      "metrics": {
        "companies_qualified": 62
      }
    },
    "contacts_extracted": 187,
    "message": "187 contacts extracted from 62 qualified companies"
  }
}
```

---

## 6. Step 3: Contact Qualification APIs

### 6.1 Set Contact Qualification Mode

**POST** `/api/v1/wizard/campaigns/{campaign_id}/contacts/qualification-mode`

**UI Mapping:** Mode selection cards

**Request:**
```json
{ "mode": "ai" }
```

*(Similar to company qualification mode)*

---

### 6.2 Run AI Contact Qualification

**POST** `/api/v1/wizard/campaigns/{campaign_id}/contacts/qualify-ai`

**UI Mapping:** "Run AI Qualification" button

**Request:**
```json
{
  "criteria": {
    "decision_maker_role": true,
    "technical_background": false,
    "linkedin_active": true,
    "minimum_tenure": true,
    "same_region": false
  }
}
```

*(Similar worker process to company qualification, using OpenAI)*

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "job_id": "job_qual_cont_abc123",
    "status": "pending",
    "contacts_to_process": 187
  }
}
```

---

### 6.3 Bulk Manual Contact Qualification

**POST** `/api/v1/wizard/campaigns/{campaign_id}/contacts/qualify-manual`

**UI Mapping:** Checkboxes, Select All

**Request:**
```json
{
  "qualifications": [
    { "contact_id": "cont_abc123", "qualified": true },
    { "contact_id": "cont_def456", "qualified": false }
  ]
}
```

**Database Operation:**
```javascript
for (const q of request.qualifications) {
  db.wizard_contacts.updateOne(
    { _id: ObjectId(q.contact_id), campaign_id: ObjectId(campaign_id) },
    {
      $set: {
        "qualification.status": q.qualified ? "qualified" : "rejected",
        "qualification.method": "manual",
        "qualification.final_decision": q.qualified,
        "qualification.qualified_at": new Date(),
        updated_at: new Date()
      }
    }
  );
}
```

**Response (200):**
```json
{
  "success": true,
  "data": { "processed": 2, "qualified": 1, "rejected": 1 }
}
```

---

### 6.4 Override AI Contact Qualification

**POST** `/api/v1/wizard/campaigns/{campaign_id}/contacts/override`

**UI Mapping:** "Qualify"/"Reject" buttons on AI results

*(Similar to company override)*

---

### 6.5 List Contacts

**GET** `/api/v1/wizard/campaigns/{campaign_id}/contacts`

**UI Mapping:** Contact list

**Query Parameters:**
| Param | Type | Default |
|-------|------|---------|
| `cursor` | string | null |
| `limit` | int | 10 |
| `status` | string | null |
| `company_id` | string | null |

**Database Query:**
```javascript
db.wizard_contacts.aggregate([
  {
    $match: {
      campaign_id: ObjectId(campaign_id),
      is_deleted: false,
      "qualification.status": { $ne: "excluded" },
      ...(status ? { "qualification.status": status } : {}),
      ...(company_id ? { company_id: ObjectId(company_id) } : {})
    }
  },
  { $sort: { created_at: -1 } },
  { $limit: limit + 1 }
])
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "contacts": [
      {
        "id": "cont_abc123",
        "company_id": "comp_abc123",
        "company_name": "TechFlow Solutions",
        "first_name": "Sarah",
        "last_name": "Chen",
        "email": "sarah.chen@techflow.com",
        "phone": "+1-555-0101",
        "job_title": "VP of Engineering",
        "linkedin_url": "https://linkedin.com/in/sarahchen",
        "qualification": {
          "status": "qualified",
          "method": "ai",
          "ai_decision": true,
          "ai_confidence": "high",
          "ai_reason": "Decision-maker role with technical background"
        }
      }
    ]
  },
  "pagination": { /* ... */ }
}
```

---

### 6.6 Confirm Contact Qualification & Proceed

**POST** `/api/v1/wizard/campaigns/{campaign_id}/contacts/confirm`

**UI Mapping:** "Continue with X Contacts →" button

**Response (200):**
```json
{
  "success": true,
  "data": {
    "campaign": {
      "id": "camp_xyz789",
      "status": "hubspot_sync",
      "current_step": 4,
      "metrics": { "contacts_qualified": 112 }
    }
  }
}
```

---

## 7. Step 4: HubSpot Sync APIs

### 7.1 List Contacts for Sync

**GET** `/api/v1/wizard/campaigns/{campaign_id}/hubspot/contacts`

**UI Mapping:** Company/contact list for sync selection

**Database Query:**
```javascript
// Group contacts by company
db.wizard_contacts.aggregate([
  {
    $match: {
      campaign_id: ObjectId(campaign_id),
      is_deleted: false,
      "qualification.status": "qualified"
    }
  },
  {
    $lookup: {
      from: "wizard_companies",
      localField: "company_id",
      foreignField: "_id",
      as: "company"
    }
  },
  { $unwind: "$company" },
  {
    $group: {
      _id: "$company_id",
      company: { $first: "$company" },
      contacts: { $push: "$$ROOT" }
    }
  },
  { $sort: { "company.name": 1 } },
  { $limit: limit + 1 }
])
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "companies": [
      {
        "id": "comp_abc123",
        "name": "TechFlow Solutions",
        "industry": "Software & Technology",
        "location": "United States",
        "sync_status": "not_synced",
        "contacts": [
          {
            "id": "cont_abc123",
            "first_name": "Sarah",
            "last_name": "Chen",
            "email": "sarah.chen@techflow.com",
            "job_title": "VP of Engineering",
            "sync_status": "not_synced"
          }
        ]
      }
    ]
  }
}
```

---

### 7.2 Sync Contacts to HubSpot

**POST** `/api/v1/wizard/campaigns/{campaign_id}/hubspot/sync`

**UI Mapping:** "Sync X Companies (Y Contacts) to HubSpot" button

**Request:**
```json
{
  "company_ids": ["comp_abc123", "comp_def456"]
}
```

**Worker Process:**
```javascript
for (const companyId of company_ids) {
  const company = db.wizard_companies.findOne({ _id: ObjectId(companyId) });
  
  // 1. Check if company exists in HubSpot (by name)
  const existingHubspotCompany = await hubspotApi.searchCompanies({ name: company.name });
  
  let hubspotCompanyId;
  if (existingHubspotCompany) {
    // Skip creating company, use existing
    hubspotCompanyId = existingHubspotCompany.id;
    db.wizard_companies.updateOne(
      { _id: ObjectId(companyId) },
      {
        $set: {
          "hubspot.sync_status": "skipped",
          "hubspot.skip_reason": "Company already exists in HubSpot",
          "hubspot.hubspot_company_id": hubspotCompanyId
        }
      }
    );
  } else {
    // Create company in HubSpot
    const newCompany = await hubspotApi.createCompany({
      name: company.name,
      industry: company.industry,
      // ... other fields
    });
    hubspotCompanyId = newCompany.id;
    
    db.wizard_companies.updateOne(
      { _id: ObjectId(companyId) },
      {
        $set: {
          "hubspot.sync_status": "synced",
          "hubspot.hubspot_company_id": hubspotCompanyId,
          "hubspot.synced_at": new Date()
        }
      }
    );
  }
  
  // 2. Sync contacts
  const contacts = db.wizard_contacts.find({
    company_id: ObjectId(companyId),
    is_deleted: false,
    "qualification.status": "qualified"
  });
  
  for (const contact of contacts) {
    // Check if contact exists by email
    const existingContact = await hubspotApi.searchContacts({ email: contact.email });
    
    if (existingContact) {
      // Skip but associate company
      await hubspotApi.associateContactToCompany(existingContact.id, hubspotCompanyId);
      
      db.wizard_contacts.updateOne(
        { _id: contact._id },
        {
          $set: {
            "hubspot.sync_status": "skipped",
            "hubspot.skip_reason": "Contact with same email already exists",
            "hubspot.hubspot_contact_id": existingContact.id
          }
        }
      );
    } else {
      // Create contact
      const newContact = await hubspotApi.createContact({
        email: contact.email,
        firstName: contact.first_name,
        lastName: contact.last_name,
        // ... other fields
      });
      
      await hubspotApi.associateContactToCompany(newContact.id, hubspotCompanyId);
      
      db.wizard_contacts.updateOne(
        { _id: contact._id },
        {
          $set: {
            "hubspot.sync_status": "synced",
            "hubspot.hubspot_contact_id": newContact.id,
            "hubspot.synced_at": new Date()
          }
        }
      );
    }
  }
}

// Update campaign metrics
db.wizard_campaigns.updateOne(
  { _id: campaign_id },
  {
    $set: {
      "metrics.contacts_synced": syncedCount,
      "metrics.contacts_sync_skipped": skippedCount
    }
  }
)
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "job_id": "job_hubspot_abc123",
    "status": "pending",
    "companies_to_sync": 3,
    "contacts_to_sync": 12
  }
}
```

---

### 7.3 Get HubSpot Sync Status

**GET** `/api/v1/wizard/campaigns/{campaign_id}/hubspot/status`

**UI Mapping:** Sync status badges, success banner

**Database Query:**
```javascript
const syncStats = db.wizard_contacts.aggregate([
  { $match: { campaign_id: ObjectId(campaign_id), is_deleted: false } },
  {
    $group: {
      _id: "$hubspot.sync_status",
      count: { $sum: 1 }
    }
  }
]);
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "sync_summary": {
      "total_companies": 62,
      "synced_companies": 45,
      "pending_companies": 17,
      "total_contacts": 112,
      "synced_contacts": 89,
      "skipped_contacts": 5,
      "pending_contacts": 18
    },
    "last_sync_at": "2024-12-27T11:30:00Z"
  }
}
```

---

### 7.4 Confirm HubSpot Sync & Proceed

**POST** `/api/v1/wizard/campaigns/{campaign_id}/hubspot/confirm`

**UI Mapping:** "Continue with X Companies (Y Contacts) →" button

**Response (200):**
```json
{
  "success": true,
  "data": {
    "campaign": {
      "id": "camp_xyz789",
      "status": "personalization",
      "current_step": 5,
      "metrics": { "contacts_synced": 89 }
    }
  }
}
```

---

## 8. Step 5: Personalization APIs

### 8.1 List Contacts for Personalization

**GET** `/api/v1/wizard/campaigns/{campaign_id}/personalization/contacts`

**UI Mapping:** Personalization contact list

**Database Query:**
```javascript
db.wizard_contacts.aggregate([
  {
    $match: {
      campaign_id: ObjectId(campaign_id),
      is_deleted: false,
      "hubspot.sync_status": "synced"
    }
  },
  {
    $lookup: {
      from: "wizard_personalizations",
      localField: "personalization_id",
      foreignField: "_id",
      as: "personalization"
    }
  },
  { $unwind: { path: "$personalization", preserveNullAndEmptyArrays: true } },
  { $sort: { created_at: -1 } },
  { $limit: limit + 1 }
])
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "contacts": [
      {
        "id": "cont_abc123",
        "company_id": "comp_abc123",
        "company_name": "TechFlow Solutions",
        "first_name": "Sarah",
        "last_name": "Chen",
        "job_title": "VP of Engineering",
        "email": "sarah.chen@techflow.com",
        "personalization": {
          "message": {
            "status": "approved",
            "current_version": 2,
            "regeneration_count": 1,
            "max_regenerations": 5,
            "approved_content": "Hi Sarah,\n\nI noticed TechFlow...",
            "generated_content": "Hi Sarah,\n\nI noticed TechFlow...",
            "generated_at": "2024-12-27T11:45:00Z",
            "approved_at": "2024-12-27T11:50:00Z"
          },
          "deck": {
            "status": "approved",
            "current_version": 1,
            "regeneration_count": 0,
            "max_regenerations": 5,
            "approved_url": "https://manus.app/decks/sarah-chen.pdf",
            "generated_url": "https://manus.app/decks/sarah-chen.pdf"
          },
          "is_fully_approved": true
        }
      }
    ]
  }
}
```

---

### 8.2 Generate Personalization (Bulk)

**POST** `/api/v1/wizard/campaigns/{campaign_id}/personalization/generate`

**UI Mapping:** "Generate Personalized Messages for X Contacts" button

**Request:**
```json
{
  "contact_ids": ["cont_abc123", "cont_def456"]
}
```

**Worker Process:**
```javascript
for (const contactId of contact_ids) {
  const contact = db.wizard_contacts.findOne({ _id: ObjectId(contactId) });
  const company = db.wizard_companies.findOne({ _id: contact.company_id });
  
  // 1. Create or get personalization record
  let personalization = db.wizard_personalizations.findOne({ contact_id: ObjectId(contactId) });
  
  if (!personalization) {
    personalization = db.wizard_personalizations.insertOne({
      campaign_id: ObjectId(campaign_id),
      contact_id: ObjectId(contactId),
      company_id: contact.company_id,
      message: {
        status: "generating",
        current_version: 1,
        regeneration_count: 0,
        max_regenerations: 5
      },
      deck: {
        status: "generating",
        current_version: 1,
        regeneration_count: 0,
        max_regenerations: 5
      },
      is_fully_approved: false,
      created_at: new Date()
    });
    
    // Link to contact
    db.wizard_contacts.updateOne(
      { _id: ObjectId(contactId) },
      { $set: { personalization_id: personalization._id } }
    );
  }
  
  // 2. Generate message via OpenAI
  const messageResult = await openai.chat({
    model: "gpt-4",
    messages: [
      { role: "system", content: "You are a B2B sales outreach expert..." },
      {
        role: "user",
        content: `Generate a personalized message for:
          Contact: ${contact.first_name} ${contact.last_name}, ${contact.job_title}
          Company: ${company.name}, ${company.industry}
          ...`
      }
    ]
  });
  
  // 3. Generate deck via Manus
  const deckResult = await manusApi.generateDeck({
    contact: { firstName: contact.first_name, lastName: contact.last_name, jobTitle: contact.job_title },
    company: { name: company.name, industry: company.industry }
  });
  
  // 4. Update personalization
  db.wizard_personalizations.updateOne(
    { _id: personalization._id },
    {
      $set: {
        "message.status": "generated",
        "message.generated_content": messageResult.content,
        "message.generated_at": new Date(),
        "message.generation_model": "gpt-4",
        "deck.status": "generated",
        "deck.generated_url": deckResult.deck_url,
        "deck.generated_at": new Date(),
        updated_at: new Date()
      }
    }
  );
  
  // 5. Create version records
  db.wizard_personalization_versions.insertOne({
    personalization_id: personalization._id,
    contact_id: ObjectId(contactId),
    campaign_id: ObjectId(campaign_id),
    type: "message",
    version: 1,
    content: messageResult.content,
    generated_by: "openai",
    generation_model: "gpt-4",
    action: "generated",
    created_at: new Date()
  });
  
  db.wizard_personalization_versions.insertOne({
    personalization_id: personalization._id,
    contact_id: ObjectId(contactId),
    campaign_id: ObjectId(campaign_id),
    type: "deck",
    version: 1,
    content: deckResult.deck_url,
    generated_by: "manus",
    action: "generated",
    created_at: new Date()
  });
}

// Update campaign metrics
db.wizard_campaigns.updateOne(
  { _id: ObjectId(campaign_id) },
  {
    $inc: {
      "metrics.messages_generated": contact_ids.length,
      "metrics.decks_generated": contact_ids.length
    }
  }
)
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "job_id": "job_pers_abc123",
    "status": "pending",
    "contacts_to_process": 3
  }
}
```

---

### 8.3 Regenerate Message Only (Bulk)

**POST** `/api/v1/wizard/campaigns/{campaign_id}/personalization/regenerate-messages`

**UI Mapping:** "Regenerate" button on rejected messages

**Request:**
```json
{
  "contact_ids": ["cont_abc123"]
}
```

**Validation:**
```javascript
// Check regeneration limit
for (const contactId of contact_ids) {
  const p = db.wizard_personalizations.findOne({ contact_id: ObjectId(contactId) });
  if (p.message.regeneration_count >= 5) {
    return error(429, "REGENERATION_LIMIT_EXCEEDED", "Maximum regeneration limit (5) reached");
  }
}
```

**Database Updates:**
```javascript
// Increment regeneration count
db.wizard_personalizations.updateOne(
  { contact_id: ObjectId(contactId) },
  {
    $set: { "message.status": "generating" },
    $inc: { "message.regeneration_count": 1, "message.current_version": 1 }
  }
)

// ... generate new message via OpenAI ...

// Update metrics
db.wizard_campaigns.updateOne(
  { _id: ObjectId(campaign_id) },
  { $inc: { "metrics.messages_regenerated": 1 } }
)
```

**Response (202) or Error (429):**
```json
{
  "success": false,
  "error": {
    "code": "REGENERATION_LIMIT_EXCEEDED",
    "message": "Maximum regeneration limit (5) reached",
    "details": [{
      "contact_id": "cont_abc123",
      "regeneration_count": 5,
      "message": "Contact admin to request additional regenerations"
    }]
  }
}
```

---

### 8.4 Approve/Reject Messages (Bulk)

**POST** `/api/v1/wizard/campaigns/{campaign_id}/personalization/messages/review`

**UI Mapping:** "Approve"/"Reject" buttons on messages

**Request:**
```json
{
  "reviews": [
    { "contact_id": "cont_abc123", "action": "approve" },
    { "contact_id": "cont_def456", "action": "reject" }
  ]
}
```

**Database Operations:**
```javascript
for (const r of request.reviews) {
  const updateFields = {
    "message.status": r.action === "approve" ? "approved" : "rejected",
    updated_at: new Date()
  };
  
  if (r.action === "approve") {
    const p = db.wizard_personalizations.findOne({ contact_id: ObjectId(r.contact_id) });
    updateFields["message.approved_content"] = p.message.generated_content;
    updateFields["message.approved_at"] = new Date();
    
    // Check if fully approved
    if (p.deck.status === "approved") {
      updateFields.is_fully_approved = true;
      updateFields.fully_approved_at = new Date();
    }
    
    // Track first-try approvals
    if (p.message.regeneration_count === 0) {
      db.wizard_campaigns.updateOne(
        { _id: ObjectId(campaign_id) },
        { $inc: { "metrics.messages_approved_first_try": 1 } }
      );
    }
  }
  
  db.wizard_personalizations.updateOne(
    { contact_id: ObjectId(r.contact_id) },
    { $set: updateFields }
  );
  
  // Create version record for action
  db.wizard_personalization_versions.insertOne({
    personalization_id: p._id,
    contact_id: ObjectId(r.contact_id),
    campaign_id: ObjectId(campaign_id),
    type: "message",
    version: p.message.current_version,
    content: p.message.generated_content,
    action: r.action === "approve" ? "approved" : "rejected",
    created_at: new Date()
  });
}
```

**Response (200):**
```json
{
  "success": true,
  "data": { "processed": 2, "approved": 1, "rejected": 1 }
}
```

---

### 8.5 Update Message Content (Bulk)

**POST** `/api/v1/wizard/campaigns/{campaign_id}/personalization/messages/update`

**UI Mapping:** "Edit Manually" save

**Request:**
```json
{
  "updates": [
    {
      "contact_id": "cont_abc123",
      "content": "Hi Sarah,\n\nCustom message..."
    }
  ]
}
```

**Database Operations:**
```javascript
for (const u of request.updates) {
  db.wizard_personalizations.updateOne(
    { contact_id: ObjectId(u.contact_id) },
    {
      $set: {
        "message.generated_content": u.content,
        "message.status": "generated",
        "message.is_manually_edited": true,
        "message.edited_at": new Date(),
        updated_at: new Date()
      },
      $inc: { "message.current_version": 1 }
    }
  );
  
  db.wizard_personalization_versions.insertOne({
    /* ... */
    type: "message",
    content: u.content,
    generated_by: "manual",
    action: "edited"
  });
}

db.wizard_campaigns.updateOne(
  { _id: ObjectId(campaign_id) },
  { $inc: { "metrics.messages_manually_edited": request.updates.length } }
)
```

---

### 8.6 Approve/Reject Decks (Bulk)

**POST** `/api/v1/wizard/campaigns/{campaign_id}/personalization/decks/review`

**UI Mapping:** "Approve Deck"/"Reject Deck" buttons

*(Similar to message review)*

---

### 8.7 Update Deck URL (Bulk)

**POST** `/api/v1/wizard/campaigns/{campaign_id}/personalization/decks/update`

**UI Mapping:** Custom URL "Submit", "Replace with Default Deck"

**Request:**
```json
{
  "updates": [
    { "contact_id": "cont_abc123", "deck_url": "https://custom.com/deck.pdf" },
    { "contact_id": "cont_def456", "use_default": true }
  ]
}
```

**Database Operations:**
```javascript
const DEFAULT_DECK_URL = "https://default-decks.company.com/standard-deck.pdf";

for (const u of request.updates) {
  const deckUrl = u.use_default ? DEFAULT_DECK_URL : u.deck_url;
  
  db.wizard_personalizations.updateOne(
    { contact_id: ObjectId(u.contact_id) },
    {
      $set: {
        "deck.generated_url": deckUrl,
        "deck.status": "generated",
        "deck.is_default_deck": u.use_default || false,
        "deck.is_custom_url": !u.use_default,
        "deck.custom_url_submitted_at": u.use_default ? null : new Date(),
        updated_at: new Date()
      },
      $inc: { "deck.current_version": 1 }
    }
  );
  
  if (u.use_default) {
    db.wizard_campaigns.updateOne(
      { _id: ObjectId(campaign_id) },
      { $inc: { "metrics.decks_replaced_with_default": 1 } }
    );
  }
}
```

---

### 8.8 Get Personalization Stats

**GET** `/api/v1/wizard/campaigns/{campaign_id}/personalization/stats`

**UI Mapping:** Stats bar at top of Step 5

**Database Query:**
```javascript
const stats = db.wizard_personalizations.aggregate([
  { $match: { campaign_id: ObjectId(campaign_id), is_deleted: false } },
  {
    $group: {
      _id: null,
      total: { $sum: 1 },
      message_pending: { $sum: { $cond: [{ $eq: ["$message.status", "pending"] }, 1, 0] } },
      message_generating: { $sum: { $cond: [{ $eq: ["$message.status", "generating"] }, 1, 0] } },
      message_generated: { $sum: { $cond: [{ $eq: ["$message.status", "generated"] }, 1, 0] } },
      message_approved: { $sum: { $cond: [{ $eq: ["$message.status", "approved"] }, 1, 0] } },
      message_rejected: { $sum: { $cond: [{ $eq: ["$message.status", "rejected"] }, 1, 0] } },
      deck_pending: { $sum: { $cond: [{ $eq: ["$deck.status", "pending"] }, 1, 0] } },
      /* ... similar for deck ... */
      fully_approved: { $sum: { $cond: ["$is_fully_approved", 1, 0] } }
    }
  }
]);
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total_contacts": 89,
    "messages": {
      "pending": 10, "generating": 5, "generated": 30, "approved": 40, "rejected": 4
    },
    "decks": {
      "pending": 10, "generating": 5, "generated": 32, "approved": 38, "rejected": 4
    },
    "fully_approved": 35
  }
}
```

---

### 8.9 Confirm Personalization & Proceed

**POST** `/api/v1/wizard/campaigns/{campaign_id}/personalization/confirm`

**UI Mapping:** "Continue with X Fully Approved →" button

**Database Operations:**
```javascript
const fullyApprovedCount = db.wizard_personalizations.countDocuments({
  campaign_id: ObjectId(campaign_id),
  is_deleted: false,
  is_fully_approved: true
});

db.wizard_campaigns.updateOne(
  { _id: ObjectId(campaign_id) },
  {
    $set: {
      status: "enrollment",
      current_step: 6,
      "metrics.contacts_fully_approved": fullyApprovedCount,
      "personalization.completed_at": new Date(),
      updated_at: new Date()
    }
  }
)
```

---

## 9. Step 6: Enrollment APIs

### 9.1 Get Lemlist Sequences

**GET** `/api/v1/wizard/lemlist/sequences`

**UI Mapping:** Sequence selection list

**Implementation:**
```javascript
// Call Lemlist API
const sequences = await lemlistApi.getSequences();

// Return formatted response
return sequences.map(s => ({
  id: s.id,
  name: s.name,
  description: s.description,
  steps: s.steps.length,
  avg_open_rate: s.analytics.openRate,
  avg_reply_rate: s.analytics.replyRate
}));
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "sequences": [
      {
        "id": "seq_abc123",
        "name": "Enterprise Outreach - Q1 2025",
        "description": "Multi-touch sequence for enterprise prospects",
        "steps": 5,
        "avg_open_rate": 42.5,
        "avg_reply_rate": 8.2
      }
    ]
  }
}
```

---

### 9.2 List Contacts for Enrollment

**GET** `/api/v1/wizard/campaigns/{campaign_id}/enrollment/contacts`

**UI Mapping:** Contact preview grid

**Database Query:**
```javascript
db.wizard_contacts.aggregate([
  {
    $match: {
      campaign_id: ObjectId(campaign_id),
      is_deleted: false,
      personalization_id: { $exists: true }
    }
  },
  {
    $lookup: {
      from: "wizard_personalizations",
      localField: "personalization_id",
      foreignField: "_id",
      as: "personalization"
    }
  },
  { $unwind: "$personalization" },
  { $match: { "personalization.is_fully_approved": true } },
  { $limit: limit + 1 }
])
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "contacts": [
      {
        "id": "cont_abc123",
        "first_name": "Sarah",
        "last_name": "Chen",
        "company_name": "TechFlow Solutions",
        "job_title": "VP of Engineering",
        "email": "sarah.chen@techflow.com",
        "personalized_message": "Hi Sarah,\n\nI noticed TechFlow...",
        "deck_url": "https://manus.app/decks/sarah-chen.pdf"
      }
    ]
  }
}
```

---

### 9.3 Enroll Contacts to Lemlist

**POST** `/api/v1/wizard/campaigns/{campaign_id}/enrollment/enroll`

**UI Mapping:** "Enroll X Contacts to Sequence" button

**Request:**
```json
{
  "sequence_id": "seq_abc123"
}
```

**Worker Process:**
```javascript
// Get all fully approved contacts
const contacts = db.wizard_contacts.aggregate([
  { $match: { campaign_id, is_deleted: false } },
  { $lookup: { from: "wizard_personalizations", ... } },
  { $match: { "personalization.is_fully_approved": true } }
]).toArray();

for (const contact of contacts) {
  // Enroll to Lemlist
  const result = await lemlistApi.enrollLead(sequence_id, {
    email: contact.email,
    firstName: contact.first_name,
    lastName: contact.last_name,
    companyName: contact.company_name,
    jobTitle: contact.job_title,
    // Custom variables for personalization
    personalized_message: contact.personalization.message.approved_content,
    deck_link: contact.personalization.deck.approved_url
  });
  
  // Update contact with enrollment status
  db.wizard_contacts.updateOne(
    { _id: contact._id },
    {
      $set: {
        "enrollment.status": "enrolled",
        "enrollment.lemlist_lead_id": result.leadId,
        "enrollment.enrolled_at": new Date(),
        updated_at: new Date()
      }
    }
  );
}

// Update campaign
db.wizard_campaigns.updateOne(
  { _id: campaign_id },
  {
    $set: {
      "enrollment.sequence_id": sequence_id,
      "enrollment.sequence_name": sequenceName,
      "enrollment.enrolled_at": new Date(),
      "metrics.contacts_enrolled": contacts.length,
      updated_at: new Date()
    }
  }
)
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "job_id": "job_enroll_abc123",
    "status": "pending",
    "contacts_to_enroll": 35,
    "sequence_name": "Enterprise Outreach - Q1 2025"
  }
}
```

---

### 9.4 Confirm Enrollment & Complete

**POST** `/api/v1/wizard/campaigns/{campaign_id}/enrollment/confirm`

**UI Mapping:** Auto-called after successful enrollment

**Database Operation:**
```javascript
db.wizard_campaigns.updateOne(
  { _id: ObjectId(campaign_id) },
  {
    $set: {
      status: "outreach",
      current_step: 7,
      "enrollment.completed_at": new Date(),
      updated_at: new Date()
    }
  }
)
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "campaign": {
      "id": "camp_xyz789",
      "status": "outreach",
      "current_step": 7,
      "metrics": { "contacts_enrolled": 35 }
    },
    "lemlist_campaign_url": "https://app.lemlist.com/campaigns/abc123"
  }
}
```

---

## 10. Job Management APIs

### 10.1 Get Job Status

**GET** `/api/v1/wizard/jobs/{job_id}`

**UI Mapping:** All loading states that poll for completion

**Database Query:**
```javascript
db.wizard_jobs.findOne({ _id: ObjectId(job_id) })
```

**Response (200 - Processing):**
```json
{
  "success": true,
  "data": {
    "job": {
      "id": "job_abc123",
      "type": "prospect_fetch",
      "status": "processing",
      "progress": { "current": 45, "total": 156, "percentage": 28.8 },
      "created_at": "2024-12-27T10:30:00Z",
      "started_at": "2024-12-27T10:30:05Z"
    }
  }
}
```

**Response (200 - Completed):**
```json
{
  "success": true,
  "data": {
    "job": {
      "id": "job_abc123",
      "type": "prospect_fetch",
      "status": "completed",
      "progress": { "current": 156, "total": 156, "percentage": 100 },
      "result": { "total_companies_found": 156, "total_contacts_found": 423 },
      "completed_at": "2024-12-27T10:31:45Z",
      "duration_ms": 100000
    }
  }
}
```

**Response (200 - Failed):**
```json
{
  "success": true,
  "data": {
    "job": {
      "id": "job_abc123",
      "type": "prospect_fetch",
      "status": "failed",
      "error": {
        "code": "EXTERNAL_SERVICE_ERROR",
        "message": "Apollo API rate limit exceeded"
      }
    }
  }
}
```

---

### 10.2 Retry Failed Job

**POST** `/api/v1/wizard/jobs/{job_id}/retry`

**UI Mapping:** "Retry" button on error states

**Database Operations:**
```javascript
const originalJob = db.wizard_jobs.findOne({ _id: ObjectId(job_id) });

if (originalJob.status !== "failed") {
  return error(409, "CONFLICT", "Only failed jobs can be retried");
}

// Create new job
const newJob = db.wizard_jobs.insertOne({
  ...originalJob,
  _id: new ObjectId(),
  status: "pending",
  original_job_id: ObjectId(job_id),
  retry_count: (originalJob.retry_count || 0) + 1,
  error: null,
  result: null,
  progress: { current: 0, total: originalJob.progress.total, percentage: 0 },
  created_at: new Date()
});
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "job": {
      "id": "job_abc123_retry_1",
      "original_job_id": "job_abc123",
      "status": "pending",
      "retry_count": 1
    }
  }
}
```

---

### 10.3 List Jobs for Campaign

**GET** `/api/v1/wizard/campaigns/{campaign_id}/jobs`

**UI Mapping:** Job history (if needed)

**Query Parameters:**
| Param | Type | Default |
|-------|------|---------|
| `cursor` | string | null |
| `limit` | int | 10 |
| `status` | string | null |
| `type` | string | null |

**Database Query:**
```javascript
db.wizard_jobs.find({
  campaign_id: ObjectId(campaign_id),
  ...(status ? { status } : {}),
  ...(type ? { type } : {})
})
.sort({ created_at: -1 })
.limit(limit + 1)
```

---

## 11. API Summary Table

| # | Method | Endpoint | UI Mapping | Async |
|---|--------|----------|------------|-------|
| **Auth** |||||
| 1 | POST | `/auth/login` | Login form | No |
| 2 | GET | `/auth/validate` | App init | No |
| **Campaigns** |||||
| 3 | GET | `/wizard/campaigns` | Campaign list | No |
| 4 | POST | `/wizard/campaigns` | New Campaign | No |
| 5 | GET | `/wizard/campaigns/{id}` | Wizard init | No |
| 6 | PATCH | `/wizard/campaigns/{id}` | Update campaign | No |
| 7 | POST | `/wizard/campaigns/{id}/navigate` | Stepper, Continue | No |
| 8 | DELETE | `/wizard/campaigns/{id}` | Delete | No |
| **Step 1** |||||
| 9 | POST | `/wizard/campaigns/{id}/prospects/fetch` | Find Prospects | Yes |
| 10 | GET | `/wizard/campaigns/{id}/prospects` | Prospect list | No |
| 11 | POST | `/wizard/campaigns/{id}/prospects/confirm` | Continue | No |
| **Step 2** |||||
| 12 | POST | `/wizard/campaigns/{id}/companies/qualification-mode` | Mode cards | No |
| 13 | POST | `/wizard/campaigns/{id}/companies/qualify-ai` | Run AI | Yes |
| 14 | POST | `/wizard/campaigns/{id}/companies/qualify-manual` | Checkboxes | No |
| 15 | POST | `/wizard/campaigns/{id}/companies/override` | Qualify/Reject | No |
| 16 | GET | `/wizard/campaigns/{id}/companies` | Company list | No |
| 17 | POST | `/wizard/campaigns/{id}/companies/confirm` | Continue | No |
| **Step 3** |||||
| 18 | POST | `/wizard/campaigns/{id}/contacts/qualification-mode` | Mode cards | No |
| 19 | POST | `/wizard/campaigns/{id}/contacts/qualify-ai` | Run AI | Yes |
| 20 | POST | `/wizard/campaigns/{id}/contacts/qualify-manual` | Checkboxes | No |
| 21 | POST | `/wizard/campaigns/{id}/contacts/override` | Qualify/Reject | No |
| 22 | GET | `/wizard/campaigns/{id}/contacts` | Contact list | No |
| 23 | POST | `/wizard/campaigns/{id}/contacts/confirm` | Continue | No |
| **Step 4** |||||
| 24 | GET | `/wizard/campaigns/{id}/hubspot/contacts` | Sync list | No |
| 25 | POST | `/wizard/campaigns/{id}/hubspot/sync` | Sync button | Yes |
| 26 | GET | `/wizard/campaigns/{id}/hubspot/status` | Status | No |
| 27 | POST | `/wizard/campaigns/{id}/hubspot/confirm` | Continue | No |
| **Step 5** |||||
| 28 | GET | `/wizard/campaigns/{id}/personalization/contacts` | Contact list | No |
| 29 | POST | `/wizard/campaigns/{id}/personalization/generate` | Generate | Yes |
| 30 | POST | `/wizard/campaigns/{id}/personalization/regenerate-messages` | Regenerate | Yes |
| 31 | POST | `/wizard/campaigns/{id}/personalization/messages/review` | Approve/Reject | No |
| 32 | POST | `/wizard/campaigns/{id}/personalization/messages/update` | Edit save | No |
| 33 | POST | `/wizard/campaigns/{id}/personalization/decks/review` | Approve/Reject | No |
| 34 | POST | `/wizard/campaigns/{id}/personalization/decks/update` | URL update | No |
| 35 | GET | `/wizard/campaigns/{id}/personalization/stats` | Stats bar | No |
| 36 | POST | `/wizard/campaigns/{id}/personalization/confirm` | Continue | No |
| **Step 6** |||||
| 37 | GET | `/wizard/lemlist/sequences` | Sequence list | No |
| 38 | GET | `/wizard/campaigns/{id}/enrollment/contacts` | Contact preview | No |
| 39 | POST | `/wizard/campaigns/{id}/enrollment/enroll` | Enroll button | Yes |
| 40 | POST | `/wizard/campaigns/{id}/enrollment/confirm` | Auto confirm | No |
| **Jobs** |||||
| 41 | GET | `/wizard/jobs/{job_id}` | Loading states | No |
| 42 | POST | `/wizard/jobs/{job_id}/retry` | Retry button | No |
| 43 | GET | `/wizard/campaigns/{id}/jobs` | Job history | No |

**Total: 43 API endpoints**

---

*End of API Specifications Document*

