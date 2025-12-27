# AI SDR - Database Design Document

## Document Information

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Created | December 28, 2024 |
| Database | MongoDB |
| Purpose | Campaign Wizard Database Schema |

---

## Table of Contents

1. [Overview](#1-overview)
2. [Collections Summary](#2-collections-summary)
3. [Collection Schemas](#3-collection-schemas)
4. [Indexes](#4-indexes)
5. [Relationships](#5-relationships)
6. [Metrics & Analytics Design](#6-metrics--analytics-design)
7. [Query Patterns](#7-query-patterns)

---

## 1. Overview

### 1.1 Design Principles

1. **Separation from Existing Collections**: All wizard-related data is stored in new collections prefixed with `wizard_`
2. **Soft Delete**: All collections support soft delete via `is_deleted` and `deleted_at` fields
3. **Metrics-Ready**: Schema designed to support analytics and reporting
4. **Future Extensibility**: Prepared for Option B (historical snapshots) with timestamp fields on all state changes
5. **Single User**: Currently designed for single-user system (no tenant_id)

### 1.2 Data Volume Estimates

| Entity | Monthly Volume | Annual Volume |
|--------|---------------|---------------|
| Campaigns | ~50 | ~600 |
| Companies | ~1,000 | ~12,000 |
| Contacts | ~5,000 | ~60,000 |
| Personalization Records | ~5,000 | ~60,000 |
| Jobs | ~200 | ~2,400 |

### 1.3 Naming Conventions

- Collection names: `wizard_<entity>` (lowercase, underscore)
- Field names: `snake_case`
- ObjectId references: `<entity>_id`
- Timestamps: `<action>_at` (e.g., `created_at`, `qualified_at`)
- Boolean flags: `is_<condition>` (e.g., `is_deleted`, `is_overridden`)

---

## 2. Collections Summary

| Collection | Purpose | Estimated Size |
|------------|---------|----------------|
| `wizard_campaigns` | Campaign metadata, state, filters, criteria | ~50/month |
| `wizard_companies` | Companies associated with campaigns | ~1,000/month |
| `wizard_contacts` | Contacts associated with campaigns | ~5,000/month |
| `wizard_personalizations` | Generated/approved messages and decks | ~5,000/month |
| `wizard_personalization_versions` | Version history for messages/decks | ~10,000/month |
| `wizard_jobs` | Async job tracking | ~200/month |
| `wizard_job_logs` | Detailed job execution logs | ~1,000/month |

---

## 3. Collection Schemas

### 3.1 `wizard_campaigns`

Stores campaign metadata, current state, filters, and qualification criteria.

```javascript
{
  // Primary Key
  _id: ObjectId,
  
  // ===== BASIC INFO =====
  name: String,                          // Campaign name
  status: String,                        // Enum: see Status Values below
  current_step: Number,                  // 1-8
  
  // ===== OWNERSHIP =====
  ownership: {
    user_id: String,                     // User who created the campaign
    user_email: String,                  // User email
    product_name: String,                // Target product
    hubspot_email: String,               // HubSpot owner email
    business_team: String                // Business team name
  },
  
  // ===== STEP 1: PROSPECTING FILTERS =====
  filters: {
    industries: [String],                // Selected industries
    regions: [String],                   // Selected regions
    employee_counts: [String],           // Employee count ranges
    revenue_min: Number,                 // Minimum revenue (USD)
    revenue_max: Number,                 // Maximum revenue (USD)
    apollo_query_params: Object          // Raw Apollo API params (for reference)
  },
  
  // ===== STEP 2: COMPANY QUALIFICATION =====
  company_qualification: {
    mode: String,                        // 'manual' | 'ai' | null
    criteria: {
      has_engineering_team: Boolean,
      is_hiring_technical: Boolean,
      uses_cloud_solutions: Boolean,
      recent_funding: Boolean,
      growth_phase: Boolean
    },
    started_at: Date,                    // When qualification started
    completed_at: Date                   // When qualification completed
  },
  
  // ===== STEP 3: CONTACT QUALIFICATION =====
  contact_qualification: {
    mode: String,                        // 'manual' | 'ai' | null
    criteria: {
      decision_maker_role: Boolean,
      technical_background: Boolean,
      linkedin_active: Boolean,
      minimum_tenure: Boolean,
      same_region: Boolean
    },
    started_at: Date,
    completed_at: Date
  },
  
  // ===== STEP 4: HUBSPOT SYNC =====
  hubspot_sync: {
    started_at: Date,
    completed_at: Date,
    last_sync_at: Date
  },
  
  // ===== STEP 5: PERSONALIZATION =====
  personalization: {
    started_at: Date,
    completed_at: Date
  },
  
  // ===== STEP 6: ENROLLMENT =====
  enrollment: {
    sequence_id: String,                 // Lemlist sequence ID
    sequence_name: String,               // Lemlist sequence name
    started_at: Date,
    completed_at: Date,
    enrolled_at: Date
  },
  
  // ===== METRICS (Denormalized for Performance) =====
  metrics: {
    companies_prospected: Number,        // Step 1 result
    companies_qualified: Number,         // Step 2 result
    companies_rejected: Number,          // Step 2 result
    contacts_extracted: Number,          // After Step 2
    contacts_qualified: Number,          // Step 3 result
    contacts_rejected: Number,           // Step 3 result
    contacts_synced: Number,             // Step 4 result
    contacts_sync_skipped: Number,       // Step 4 result
    contacts_personalized: Number,       // Step 5 result
    contacts_fully_approved: Number,     // Step 5 result
    contacts_enrolled: Number,           // Step 6 result
    
    // AI Qualification Metrics
    ai_company_qualified: Number,
    ai_company_rejected: Number,
    company_overrides_to_qualified: Number,
    company_overrides_to_rejected: Number,
    ai_contact_qualified: Number,
    ai_contact_rejected: Number,
    contact_overrides_to_qualified: Number,
    contact_overrides_to_rejected: Number,
    
    // Personalization Metrics
    messages_generated: Number,
    messages_approved_first_try: Number,
    messages_regenerated: Number,
    messages_manually_edited: Number,
    decks_generated: Number,
    decks_approved_first_try: Number,
    decks_replaced_with_default: Number
  },
  
  // ===== TIMING METRICS =====
  step_timings: {
    step_1_duration_seconds: Number,
    step_2_duration_seconds: Number,
    step_3_duration_seconds: Number,
    step_4_duration_seconds: Number,
    step_5_duration_seconds: Number,
    step_6_duration_seconds: Number
  },
  
  // ===== SOFT DELETE =====
  is_deleted: Boolean,                   // Default: false
  deleted_at: Date,                      // Set when soft deleted
  
  // ===== TIMESTAMPS =====
  created_at: Date,
  updated_at: Date,
  completed_at: Date                     // When status becomes 'completed'
}
```

**Status Values:**
- `draft` - Initial state, just created
- `prospecting` - Step 1 in progress
- `company_qualification` - Step 2 in progress
- `contact_qualification` - Step 3 in progress
- `hubspot_sync` - Step 4 in progress
- `personalization` - Step 5 in progress
- `enrollment` - Step 6 in progress
- `outreach` - Enrolled to Lemlist, waiting for completion
- `completed` - All sequences executed

---

### 3.2 `wizard_companies`

Stores companies associated with campaigns.

```javascript
{
  // Primary Key
  _id: ObjectId,
  
  // ===== REFERENCES =====
  campaign_id: ObjectId,                 // Reference to wizard_campaigns
  
  // ===== SOURCE DATA =====
  source: String,                        // 'apollo'
  source_id: String,                     // Apollo company ID
  source_data: Object,                   // Raw Apollo response (for reference)
  
  // ===== COMPANY INFO =====
  name: String,
  industry: String,
  employee_count: String,                // Range string: "51-200"
  revenue: String,                       // Range string: "$5M - $10M"
  revenue_min: Number,                   // Numeric for filtering
  revenue_max: Number,                   // Numeric for filtering
  location: String,
  country: String,
  website: String,
  linkedin_url: String,
  
  // ===== CONTACT STATS =====
  contact_count: Number,                 // Number of contacts found
  
  // ===== QUALIFICATION =====
  qualification: {
    status: String,                      // 'pending' | 'qualified' | 'rejected'
    method: String,                      // 'manual' | 'ai'
    
    // AI Decision (preserved even after override)
    ai_decision: Boolean,                // null if manual, true/false if AI
    ai_confidence: String,               // 'high' | 'medium' | 'low'
    ai_reason: String,                   // AI explanation
    ai_qualified_at: Date,               // When AI made decision
    
    // Override Info
    is_overridden: Boolean,              // Default: false
    override_decision: Boolean,          // The overridden decision
    override_reason: String,             // User-provided reason
    overridden_at: Date,                 // When override happened
    
    // Final Decision
    final_decision: Boolean,             // Computed: override ?? ai_decision
    qualified_at: Date                   // When final qualification happened
  },
  
  // ===== HUBSPOT SYNC =====
  hubspot: {
    sync_status: String,                 // 'not_synced' | 'syncing' | 'synced' | 'skipped' | 'failed'
    hubspot_company_id: String,          // HubSpot company record ID
    synced_at: Date,
    skip_reason: String,                 // If skipped, why
    error_message: String                // If failed, error details
  },
  
  // ===== SOFT DELETE =====
  is_deleted: Boolean,
  deleted_at: Date,
  
  // ===== TIMESTAMPS =====
  created_at: Date,
  updated_at: Date
}
```

---

### 3.3 `wizard_contacts`

Stores contacts associated with campaigns.

```javascript
{
  // Primary Key
  _id: ObjectId,
  
  // ===== REFERENCES =====
  campaign_id: ObjectId,                 // Reference to wizard_campaigns
  company_id: ObjectId,                  // Reference to wizard_companies
  
  // ===== SOURCE DATA =====
  source: String,                        // 'apollo'
  source_id: String,                     // Apollo contact ID
  source_data: Object,                   // Raw Apollo response
  
  // ===== CONTACT INFO =====
  first_name: String,
  last_name: String,
  full_name: String,                     // Computed: first_name + last_name
  email: String,
  phone: String,
  job_title: String,
  seniority: String,                     // 'C-Level' | 'VP' | 'Director' | 'Manager' | 'IC'
  department: String,
  linkedin_url: String,
  
  // ===== COMPANY INFO (Denormalized) =====
  company_name: String,                  // Denormalized for display
  
  // ===== QUALIFICATION =====
  qualification: {
    status: String,                      // 'pending' | 'qualified' | 'rejected' | 'excluded'
    method: String,                      // 'manual' | 'ai' | 'auto_excluded'
    
    // Auto-exclusion (if company rejected)
    auto_excluded: Boolean,              // True if company was rejected
    auto_excluded_at: Date,
    
    // AI Decision
    ai_decision: Boolean,
    ai_confidence: String,
    ai_reason: String,
    ai_qualified_at: Date,
    
    // Override Info
    is_overridden: Boolean,
    override_decision: Boolean,
    override_reason: String,
    overridden_at: Date,
    
    // Final Decision
    final_decision: Boolean,
    qualified_at: Date
  },
  
  // ===== HUBSPOT SYNC =====
  hubspot: {
    sync_status: String,                 // 'not_synced' | 'syncing' | 'synced' | 'skipped' | 'failed'
    hubspot_contact_id: String,          // HubSpot contact record ID
    synced_at: Date,
    skip_reason: String,                 // e.g., "Contact with same email exists"
    error_message: String
  },
  
  // ===== PERSONALIZATION REFERENCE =====
  personalization_id: ObjectId,          // Reference to wizard_personalizations
  
  // ===== ENROLLMENT =====
  enrollment: {
    status: String,                      // 'not_enrolled' | 'enrolling' | 'enrolled' | 'failed'
    lemlist_lead_id: String,             // Lemlist lead ID
    enrolled_at: Date,
    error_message: String
  },
  
  // ===== OUTREACH TRACKING (From Lemlist Webhooks) =====
  outreach: {
    emails_sent: Number,
    emails_opened: Number,
    emails_clicked: Number,
    emails_replied: Number,
    last_activity_at: Date,
    status: String                       // 'pending' | 'in_progress' | 'completed' | 'replied'
  },
  
  // ===== SOFT DELETE =====
  is_deleted: Boolean,
  deleted_at: Date,
  
  // ===== TIMESTAMPS =====
  created_at: Date,
  updated_at: Date
}
```

---

### 3.4 `wizard_personalizations`

Stores generated and approved personalization content.

```javascript
{
  // Primary Key
  _id: ObjectId,
  
  // ===== REFERENCES =====
  campaign_id: ObjectId,
  contact_id: ObjectId,
  company_id: ObjectId,
  
  // ===== MESSAGE PERSONALIZATION =====
  message: {
    status: String,                      // 'pending' | 'generating' | 'generated' | 'approved' | 'rejected'
    
    // Version Tracking
    current_version: Number,             // Current version number
    regeneration_count: Number,          // Times regenerated (max 5)
    max_regenerations: Number,           // Always 5
    
    // Generated Content
    generated_content: String,           // Latest AI-generated message
    generated_at: Date,
    generation_model: String,            // 'gpt-4' | 'gpt-3.5-turbo' etc.
    generation_prompt_hash: String,      // Hash of prompt used (for debugging)
    
    // Approved Content
    approved_content: String,            // Final approved message
    approved_at: Date,
    
    // Editing
    is_manually_edited: Boolean,         // True if user edited the message
    edited_at: Date
  },
  
  // ===== DECK PERSONALIZATION =====
  deck: {
    status: String,                      // 'pending' | 'generating' | 'generated' | 'approved' | 'rejected'
    
    // Version Tracking
    current_version: Number,
    regeneration_count: Number,
    max_regenerations: Number,           // Always 5
    
    // Generated Content
    generated_url: String,               // Manus-generated deck URL
    generated_at: Date,
    
    // Approved Content
    approved_url: String,                // Final approved deck URL
    approved_at: Date,
    
    // Manual Override
    is_default_deck: Boolean,            // True if using default deck
    is_custom_url: Boolean,              // True if user provided custom URL
    custom_url_submitted_at: Date
  },
  
  // ===== COMBINED STATUS =====
  is_fully_approved: Boolean,            // True if both message AND deck are approved
  fully_approved_at: Date,
  
  // ===== SOFT DELETE =====
  is_deleted: Boolean,
  deleted_at: Date,
  
  // ===== TIMESTAMPS =====
  created_at: Date,
  updated_at: Date
}
```

---

### 3.5 `wizard_personalization_versions`

Stores version history for messages and decks (for Option B future support).

```javascript
{
  // Primary Key
  _id: ObjectId,
  
  // ===== REFERENCES =====
  personalization_id: ObjectId,
  contact_id: ObjectId,
  campaign_id: ObjectId,
  
  // ===== VERSION INFO =====
  type: String,                          // 'message' | 'deck'
  version: Number,                       // Version number (1, 2, 3...)
  
  // ===== CONTENT =====
  content: String,                       // Message text or deck URL
  
  // ===== GENERATION METADATA =====
  generated_by: String,                  // 'openai' | 'manus' | 'manual'
  generation_model: String,              // Model used (if AI)
  generation_prompt: String,             // Prompt used (optional, for debugging)
  generation_params: Object,             // Any additional params
  
  // ===== ACTION =====
  action: String,                        // 'generated' | 'regenerated' | 'edited' | 'approved' | 'rejected'
  action_reason: String,                 // Why this action was taken
  
  // ===== TIMESTAMPS =====
  created_at: Date
}
```

---

### 3.6 `wizard_jobs`

Stores async job tracking information.

```javascript
{
  // Primary Key
  _id: ObjectId,
  
  // ===== REFERENCES =====
  campaign_id: ObjectId,
  
  // ===== JOB INFO =====
  type: String,                          // See Job Types below
  status: String,                        // 'pending' | 'processing' | 'completed' | 'failed'
  
  // ===== PROGRESS =====
  progress: {
    current: Number,                     // Items processed
    total: Number,                       // Total items
    percentage: Number                   // Computed percentage
  },
  
  // ===== INPUT =====
  input: Object,                         // Job-specific input data
  
  // ===== OUTPUT =====
  result: Object,                        // Job-specific result data
  
  // ===== ERROR =====
  error: {
    code: String,
    message: String,
    details: [Object],
    stack_trace: String                  // For debugging
  },
  
  // ===== RETRY =====
  retry_count: Number,                   // Number of retries attempted
  max_retries: Number,                   // Maximum retries allowed
  original_job_id: ObjectId,             // If this is a retry, reference to original
  
  // ===== EXTERNAL REFERENCES =====
  external_job_ids: {
    apollo_job_id: String,
    openai_batch_id: String,
    manus_job_id: String,
    hubspot_batch_id: String,
    lemlist_campaign_id: String
  },
  
  // ===== TIMING =====
  created_at: Date,
  started_at: Date,
  completed_at: Date,
  duration_ms: Number                    // Computed: completed_at - started_at
}
```

**Job Types:**
- `prospect_fetch` - Fetch prospects from Apollo
- `company_qualification_ai` - AI qualify companies
- `contact_qualification_ai` - AI qualify contacts
- `hubspot_sync` - Sync to HubSpot
- `personalization_generate` - Generate messages and decks
- `personalization_regenerate_messages` - Regenerate messages only
- `lemlist_enrollment` - Enroll to Lemlist sequence

---

### 3.7 `wizard_job_logs`

Stores detailed job execution logs for debugging and metrics.

```javascript
{
  // Primary Key
  _id: ObjectId,
  
  // ===== REFERENCES =====
  job_id: ObjectId,
  campaign_id: ObjectId,
  
  // ===== LOG INFO =====
  level: String,                         // 'debug' | 'info' | 'warn' | 'error'
  message: String,
  
  // ===== CONTEXT =====
  context: {
    entity_type: String,                 // 'company' | 'contact' | 'personalization'
    entity_id: ObjectId,
    step: String,                        // Which step in the job
    external_api: String,                // Which external API was called
    request: Object,                     // Request payload (sanitized)
    response: Object                     // Response payload (sanitized)
  },
  
  // ===== TIMING =====
  duration_ms: Number,
  
  // ===== TIMESTAMP =====
  created_at: Date
}
```

---

## 4. Indexes

### 4.1 `wizard_campaigns` Indexes

```javascript
// Primary queries
{ _id: 1 }                                           // Default
{ "ownership.user_id": 1, created_at: -1 }           // List campaigns for user
{ status: 1, created_at: -1 }                        // Filter by status
{ is_deleted: 1, created_at: -1 }                    // Exclude deleted

// Metrics queries
{ status: 1, "metrics.contacts_enrolled": 1 }        // Completed campaigns with enrollments
{ created_at: 1 }                                    // Time-based analytics

// Compound for common listing
{ 
  is_deleted: 1, 
  "ownership.user_id": 1, 
  created_at: -1 
}
```

### 4.2 `wizard_companies` Indexes

```javascript
// Primary queries
{ _id: 1 }
{ campaign_id: 1, created_at: -1 }                   // List companies for campaign
{ campaign_id: 1, "qualification.status": 1 }        // Filter by qualification
{ campaign_id: 1, "hubspot.sync_status": 1 }         // Filter by sync status

// Deduplication
{ source: 1, source_id: 1 }                          // Unique per source

// Soft delete
{ campaign_id: 1, is_deleted: 1 }

// Metrics
{ campaign_id: 1, "qualification.method": 1 }        // AI vs manual breakdown
{ campaign_id: 1, "qualification.is_overridden": 1 } // Override tracking
```

### 4.3 `wizard_contacts` Indexes

```javascript
// Primary queries
{ _id: 1 }
{ campaign_id: 1, created_at: -1 }
{ campaign_id: 1, company_id: 1 }                    // Contacts by company
{ campaign_id: 1, "qualification.status": 1 }
{ campaign_id: 1, "hubspot.sync_status": 1 }
{ campaign_id: 1, "enrollment.status": 1 }

// Email lookup (for HubSpot deduplication)
{ email: 1 }

// Personalization join
{ personalization_id: 1 }

// Soft delete
{ campaign_id: 1, is_deleted: 1 }

// Compound for common listing with filters
{
  campaign_id: 1,
  is_deleted: 1,
  "qualification.status": 1,
  created_at: -1
}
```

### 4.4 `wizard_personalizations` Indexes

```javascript
// Primary queries
{ _id: 1 }
{ contact_id: 1 }                                    // One-to-one with contact
{ campaign_id: 1, is_fully_approved: 1 }             // Approved for enrollment
{ campaign_id: 1, "message.status": 1 }
{ campaign_id: 1, "deck.status": 1 }

// Metrics
{ campaign_id: 1, "message.regeneration_count": 1 }
{ campaign_id: 1, "message.is_manually_edited": 1 }
```

### 4.5 `wizard_personalization_versions` Indexes

```javascript
// Primary queries
{ personalization_id: 1, type: 1, version: -1 }     // Get versions for personalization
{ contact_id: 1, type: 1, created_at: -1 }          // History by contact

// Metrics
{ campaign_id: 1, type: 1, action: 1 }              // Action breakdown
```

### 4.6 `wizard_jobs` Indexes

```javascript
// Primary queries
{ _id: 1 }
{ campaign_id: 1, created_at: -1 }                   // Jobs by campaign
{ status: 1, created_at: 1 }                         // Pending jobs (for worker)
{ type: 1, status: 1 }                               // Jobs by type and status

// Retry tracking
{ original_job_id: 1 }

// Metrics
{ type: 1, status: 1, created_at: 1 }               // Job success rates over time
{ type: 1, duration_ms: 1 }                          // Performance analysis
```

### 4.7 `wizard_job_logs` Indexes

```javascript
// Primary queries
{ job_id: 1, created_at: 1 }                         // Logs for job
{ campaign_id: 1, level: 1, created_at: -1 }         // Error logs by campaign

// TTL Index (optional - auto-delete old logs)
{ created_at: 1 }, { expireAfterSeconds: 2592000 }   // 30 days
```

---

## 5. Relationships

```
                                    ┌─────────────────────────┐
                                    │   wizard_campaigns      │
                                    │   (_id)                 │
                                    └───────────┬─────────────┘
                                                │
                    ┌───────────────────────────┼───────────────────────────┐
                    │                           │                           │
                    ▼                           ▼                           ▼
        ┌───────────────────┐       ┌───────────────────┐       ┌───────────────────┐
        │ wizard_companies  │       │   wizard_jobs     │       │ wizard_job_logs   │
        │ (campaign_id)     │       │ (campaign_id)     │       │ (campaign_id,     │
        └─────────┬─────────┘       └───────────────────┘       │  job_id)          │
                  │                                             └───────────────────┘
                  │
                  ▼
        ┌───────────────────┐
        │ wizard_contacts   │
        │ (campaign_id,     │
        │  company_id)      │
        └─────────┬─────────┘
                  │
                  ▼
        ┌─────────────────────────┐       ┌─────────────────────────────┐
        │ wizard_personalizations │◄──────│ wizard_personalization_     │
        │ (campaign_id,           │       │ versions                    │
        │  contact_id,            │       │ (personalization_id,        │
        │  company_id)            │       │  contact_id, campaign_id)   │
        └─────────────────────────┘       └─────────────────────────────┘
```

### Relationship Types

| Parent | Child | Type | On Delete |
|--------|-------|------|-----------|
| wizard_campaigns | wizard_companies | 1:N | Cascade soft delete |
| wizard_campaigns | wizard_contacts | 1:N | Cascade soft delete |
| wizard_campaigns | wizard_jobs | 1:N | Keep for audit |
| wizard_companies | wizard_contacts | 1:N | Cascade soft delete |
| wizard_contacts | wizard_personalizations | 1:1 | Cascade soft delete |
| wizard_personalizations | wizard_personalization_versions | 1:N | Cascade delete |
| wizard_jobs | wizard_job_logs | 1:N | Cascade delete |

---

## 6. Metrics & Analytics Design

### 6.1 Pre-Computed Metrics (In Documents)

To avoid expensive aggregations, key metrics are pre-computed and stored directly:

**In `wizard_campaigns`:**
```javascript
metrics: {
  // Counts at each step
  companies_prospected: Number,
  companies_qualified: Number,
  // ... etc
  
  // AI vs Manual breakdown
  ai_company_qualified: Number,
  ai_company_rejected: Number,
  company_overrides_to_qualified: Number,
  // ... etc
  
  // Personalization metrics
  messages_approved_first_try: Number,
  messages_regenerated: Number,
  // ... etc
}
```

**Update Strategy:**
- Update `metrics` atomically when underlying data changes
- Use `$inc` for counters to avoid race conditions

### 6.2 Time-Based Metrics

For time-series analytics, use the timestamps in documents:

```javascript
// Example: Calculate average time in each step
db.wizard_campaigns.aggregate([
  { $match: { status: "completed" } },
  { $project: {
    step_1_duration: { $subtract: ["$company_qualification.started_at", "$created_at"] },
    step_2_duration: { $subtract: ["$contact_qualification.started_at", "$company_qualification.started_at"] },
    // ... etc
  }},
  { $group: {
    _id: null,
    avg_step_1: { $avg: "$step_1_duration" },
    avg_step_2: { $avg: "$step_2_duration" }
  }}
]);
```

### 6.3 Conversion Funnel Metrics

```javascript
// Funnel: Prospected → Qualified → Synced → Personalized → Enrolled
db.wizard_campaigns.aggregate([
  { $match: { is_deleted: false } },
  { $group: {
    _id: null,
    total_prospected: { $sum: "$metrics.companies_prospected" },
    total_qualified: { $sum: "$metrics.companies_qualified" },
    total_synced: { $sum: "$metrics.contacts_synced" },
    total_personalized: { $sum: "$metrics.contacts_fully_approved" },
    total_enrolled: { $sum: "$metrics.contacts_enrolled" }
  }},
  { $project: {
    prospected_to_qualified_rate: { 
      $multiply: [{ $divide: ["$total_qualified", "$total_prospected"] }, 100] 
    },
    // ... etc
  }}
]);
```

### 6.4 AI Accuracy Metrics

```javascript
// Calculate AI accuracy based on overrides
db.wizard_companies.aggregate([
  { $match: { "qualification.method": "ai" } },
  { $group: {
    _id: null,
    total_ai_decisions: { $sum: 1 },
    total_overridden: { $sum: { $cond: ["$qualification.is_overridden", 1, 0] } }
  }},
  { $project: {
    ai_accuracy: { 
      $multiply: [
        { $subtract: [1, { $divide: ["$total_overridden", "$total_ai_decisions"] }] },
        100
      ]
    }
  }}
]);
```

### 6.5 Recommended Metrics Views

For the custom reporting service, create these aggregation pipelines:

| Metric | Collection | Aggregation Type |
|--------|------------|------------------|
| Campaign Completion Rate | wizard_campaigns | Group by month, count by status |
| Average Time to Complete | wizard_campaigns | Group by month, avg of step_timings |
| Company Qualification Rate | wizard_companies | Group by campaign, count by status |
| AI Override Rate | wizard_companies | Group by campaign, count overrides |
| HubSpot Sync Success Rate | wizard_contacts | Group by campaign, count by sync_status |
| Message Approval Rate | wizard_personalizations | Group by campaign, count by message.status |
| Regeneration Distribution | wizard_personalizations | Group by regeneration_count |
| Job Success Rate | wizard_jobs | Group by type, count by status |
| Average Job Duration | wizard_jobs | Group by type, avg of duration_ms |

---

## 7. Query Patterns

### 7.1 Campaign List with Pagination (Cursor-Based)

```javascript
// First page
db.wizard_campaigns.find({
  is_deleted: false,
  "ownership.user_id": "user_001"
})
.sort({ created_at: -1 })
.limit(11)  // Fetch 1 extra to determine has_more

// Next page (using cursor = last _id from previous page)
db.wizard_campaigns.find({
  is_deleted: false,
  "ownership.user_id": "user_001",
  _id: { $lt: ObjectId("cursor_value") }
})
.sort({ created_at: -1 })
.limit(11)
```

### 7.2 Companies by Campaign with Status Filter

```javascript
db.wizard_companies.find({
  campaign_id: ObjectId("camp_id"),
  is_deleted: false,
  "qualification.status": "qualified"
})
.sort({ created_at: -1 })
.limit(11)
```

### 7.3 Contacts with Personalization Status

```javascript
db.wizard_contacts.aggregate([
  { $match: { 
    campaign_id: ObjectId("camp_id"),
    is_deleted: false,
    "hubspot.sync_status": "synced"
  }},
  { $lookup: {
    from: "wizard_personalizations",
    localField: "personalization_id",
    foreignField: "_id",
    as: "personalization"
  }},
  { $unwind: { path: "$personalization", preserveNullAndEmptyArrays: true } },
  { $sort: { created_at: -1 } },
  { $limit: 11 }
])
```

### 7.4 Update Metrics on Qualification

```javascript
// When a company is qualified
db.wizard_campaigns.updateOne(
  { _id: ObjectId("camp_id") },
  { 
    $inc: { 
      "metrics.companies_qualified": 1,
      "metrics.ai_company_qualified": 1  // if AI
    },
    $set: { updated_at: new Date() }
  }
)
```

### 7.5 Bulk Override Companies

```javascript
// Update multiple companies
db.wizard_companies.updateMany(
  { 
    _id: { $in: [ObjectId("id1"), ObjectId("id2")] },
    campaign_id: ObjectId("camp_id")
  },
  {
    $set: {
      "qualification.is_overridden": true,
      "qualification.override_decision": true,
      "qualification.overridden_at": new Date(),
      "qualification.status": "qualified",
      "qualification.final_decision": true,
      updated_at: new Date()
    }
  }
)
```

### 7.6 Soft Delete Campaign (Cascade)

```javascript
// 1. Soft delete campaign
db.wizard_campaigns.updateOne(
  { _id: ObjectId("camp_id") },
  { $set: { is_deleted: true, deleted_at: new Date() } }
)

// 2. Soft delete companies
db.wizard_companies.updateMany(
  { campaign_id: ObjectId("camp_id") },
  { $set: { is_deleted: true, deleted_at: new Date() } }
)

// 3. Soft delete contacts
db.wizard_contacts.updateMany(
  { campaign_id: ObjectId("camp_id") },
  { $set: { is_deleted: true, deleted_at: new Date() } }
)

// 4. Soft delete personalizations
db.wizard_personalizations.updateMany(
  { campaign_id: ObjectId("camp_id") },
  { $set: { is_deleted: true, deleted_at: new Date() } }
)
```

---

## Appendix A: Default Values

```javascript
// Default values for new documents

// wizard_campaigns
{
  status: "draft",
  current_step: 1,
  metrics: {
    companies_prospected: 0,
    companies_qualified: 0,
    companies_rejected: 0,
    contacts_extracted: 0,
    contacts_qualified: 0,
    contacts_rejected: 0,
    contacts_synced: 0,
    contacts_sync_skipped: 0,
    contacts_personalized: 0,
    contacts_fully_approved: 0,
    contacts_enrolled: 0,
    ai_company_qualified: 0,
    ai_company_rejected: 0,
    company_overrides_to_qualified: 0,
    company_overrides_to_rejected: 0,
    ai_contact_qualified: 0,
    ai_contact_rejected: 0,
    contact_overrides_to_qualified: 0,
    contact_overrides_to_rejected: 0,
    messages_generated: 0,
    messages_approved_first_try: 0,
    messages_regenerated: 0,
    messages_manually_edited: 0,
    decks_generated: 0,
    decks_approved_first_try: 0,
    decks_replaced_with_default: 0
  },
  is_deleted: false
}

// wizard_companies.qualification
{
  status: "pending",
  method: null,
  ai_decision: null,
  is_overridden: false,
  final_decision: null
}

// wizard_contacts.qualification
{
  status: "pending",
  method: null,
  auto_excluded: false,
  ai_decision: null,
  is_overridden: false,
  final_decision: null
}

// wizard_personalizations.message / .deck
{
  status: "pending",
  current_version: 0,
  regeneration_count: 0,
  max_regenerations: 5
}
```

---

## Appendix B: Enum Values

```javascript
// Campaign Status
const CAMPAIGN_STATUS = [
  "draft",
  "prospecting", 
  "company_qualification",
  "contact_qualification",
  "hubspot_sync",
  "personalization",
  "enrollment",
  "outreach",
  "completed"
];

// Qualification Status
const QUALIFICATION_STATUS = [
  "pending",
  "qualified",
  "rejected",
  "excluded"  // For auto-excluded contacts
];

// Qualification Method
const QUALIFICATION_METHOD = [
  "manual",
  "ai",
  "auto_excluded"
];

// Sync Status
const SYNC_STATUS = [
  "not_synced",
  "syncing",
  "synced",
  "skipped",
  "failed"
];

// Personalization Status
const PERSONALIZATION_STATUS = [
  "pending",
  "generating",
  "generated",
  "approved",
  "rejected"
];

// Enrollment Status
const ENROLLMENT_STATUS = [
  "not_enrolled",
  "enrolling",
  "enrolled",
  "failed"
];

// Job Status
const JOB_STATUS = [
  "pending",
  "processing",
  "completed",
  "failed"
];

// Job Types
const JOB_TYPES = [
  "prospect_fetch",
  "company_qualification_ai",
  "contact_qualification_ai",
  "hubspot_sync",
  "personalization_generate",
  "personalization_regenerate_messages",
  "lemlist_enrollment"
];

// AI Confidence
const AI_CONFIDENCE = [
  "high",
  "medium",
  "low"
];

// Log Level
const LOG_LEVEL = [
  "debug",
  "info",
  "warn",
  "error"
];
```

---

*End of Database Design Document*

