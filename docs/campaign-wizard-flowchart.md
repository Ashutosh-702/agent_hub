# AI SDR - Campaign Wizard API Flowchart

## Document Information

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Created | December 28, 2024 |
| Purpose | Visual representation of API interactions |

---

## Table of Contents

1. [High-Level Flow](#1-high-level-flow)
2. [Campaign Lifecycle](#2-campaign-lifecycle)
3. [Step-by-Step API Flows](#3-step-by-step-api-flows)
4. [Async Job Pattern](#4-async-job-pattern)
5. [State Machine](#5-state-machine)
6. [Data Flow Diagrams](#6-data-flow-diagrams)
7. [Integration Flows](#7-integration-flows)

---

## 1. High-Level Flow

### 1.1 Complete Campaign Wizard Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                        CAMPAIGN WIZARD - COMPLETE FLOW                                          │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────┐     ┌──────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
    │  LOGIN   │────▶│  CAMPAIGN LIST   │────▶│   CREATE CAMPAIGN   │────▶│   WIZARD STEP 1     │
    │          │     │                  │     │                     │     │   (Prospecting)     │
    └──────────┘     └──────────────────┘     └─────────────────────┘     └──────────┬──────────┘
                                                                                      │
    ┌─────────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   WIZARD STEP 2     │────▶│   WIZARD STEP 3     │────▶│   WIZARD STEP 4     │
│ (Company Qualify)   │     │ (Contact Qualify)   │     │   (HubSpot Sync)    │
└─────────────────────┘     └─────────────────────┘     └──────────┬──────────┘
                                                                    │
    ┌───────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   WIZARD STEP 5     │────▶│   WIZARD STEP 6     │────▶│   CAMPAIGN          │
│  (Personalization)  │     │    (Enrollment)     │     │   COMPLETE!         │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
```

---

## 2. Campaign Lifecycle

### 2.1 Campaign Status State Machine

```
                                    ┌─────────────────────────────────────────────────────────────┐
                                    │                   CAMPAIGN STATUS STATES                     │
                                    └─────────────────────────────────────────────────────────────┘

                        ┌─────────┐
                        │  draft  │
                        │  (1)    │
                        └────┬────┘
                             │ POST /prospects/fetch
                             ▼
                     ┌──────────────┐
                     │ prospecting  │
                     │     (1)      │
                     └───────┬──────┘
                             │ POST /prospects/confirm
                             ▼
              ┌───────────────────────────┐
              │  company_qualification    │
              │          (2)              │
              └─────────────┬─────────────┘
                            │ POST /companies/confirm
                            ▼
              ┌───────────────────────────┐
              │  contact_qualification    │
              │          (3)              │
              └─────────────┬─────────────┘
                            │ POST /contacts/confirm
                            ▼
                   ┌────────────────┐
                   │  hubspot_sync  │
                   │      (4)       │
                   └───────┬────────┘
                           │ POST /hubspot/confirm
                           ▼
                  ┌─────────────────┐
                  │ personalization │
                  │      (5)        │
                  └────────┬────────┘
                           │ POST /personalization/confirm
                           ▼
                    ┌─────────────┐
                    │ enrollment  │
                    │     (6)     │
                    └──────┬──────┘
                           │ POST /enrollment/enroll + confirm
                           ▼
                     ┌──────────┐
                     │ outreach │
                     │   (7)    │
                     └────┬─────┘
                          │ Lemlist webhooks
                          ▼
                    ┌───────────┐
                    │ completed │
                    │   (8)     │
                    └───────────┘


    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║  BACKWARD NAVIGATION (POST /navigate)                                      ║
    ║                                                                            ║
    ║  Any step can navigate backward with confirm_reset: true                   ║
    ║  This soft-deletes data from subsequent steps and resets metrics           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## 3. Step-by-Step API Flows

### 3.1 Step 1: Prospecting

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                              STEP 1: PROSPECTING FLOW                                      │
└───────────────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────────────────┐
    │                                  FRONTEND                                         │
    └──────────────────────────────────────────────────────────────────────────────────┘
    
    User opens Step 1          User sets filters          User clicks           User clicks
    (Prospecting)              and clicks                 pagination            "Continue"
         │                     "Find Prospects"                │                    │
         │                          │                          │                    │
         ▼                          ▼                          ▼                    ▼
    ┌─────────┐              ┌─────────────┐            ┌─────────────┐       ┌─────────────┐
    │  GET    │              │   POST      │            │    GET      │       │   POST      │
    │campaign │              │  prospects/ │            │  prospects  │       │  prospects/ │
    │ /{id}   │              │   fetch     │            │  ?cursor=   │       │  confirm    │
    └────┬────┘              └──────┬──────┘            └──────┬──────┘       └──────┬──────┘
         │                          │                          │                    │
         │                          │                          │                    │
    ┌────┴──────────────────────────┴──────────────────────────┴────────────────────┴────────┐
    │                                     BACKEND                                             │
    └────┬──────────────────────────┬──────────────────────────┬────────────────────┬────────┘
         │                          │                          │                    │
         ▼                          ▼                          ▼                    ▼
    ┌─────────┐              ┌─────────────┐            ┌─────────────┐       ┌─────────────┐
    │ Return  │              │ Create Job  │            │ Query with  │       │ Update      │
    │ campaign│              │ Save filters│            │ cursor      │       │ status to   │
    │ data    │              │ Return job  │            │ pagination  │       │ step 2      │
    └─────────┘              └──────┬──────┘            └─────────────┘       └─────────────┘
                                    │
                                    │ ASYNC JOB
                                    ▼
                             ┌─────────────┐        ┌─────────────┐
                             │   WORKER    │───────▶│   Apollo    │
                             │  Process    │◀───────│    API      │
                             └──────┬──────┘        └─────────────┘
                                    │
                                    │ Save results
                                    ▼
                             ┌─────────────┐
                             │  MongoDB    │
                             │ companies   │
                             │ + contacts  │
                             └─────────────┘
                             
                                    │
    ┌───────────────────────────────┘
    │
    ▼
    ┌──────────────────────────────────────────────────────────────────────────────────┐
    │                           FRONTEND POLLING                                        │
    └──────────────────────────────────────────────────────────────────────────────────┘
    
    Poll every 2s              Job completed?              Refresh list
         │                          │                          │
         ▼                          ▼                          ▼
    ┌─────────────┐           ┌───────────┐             ┌─────────────┐
    │   GET       │           │ status == │    YES      │    GET      │
    │ /jobs/{id}  │──────────▶│ completed │────────────▶│  prospects  │
    └─────────────┘           │    ?      │             └─────────────┘
                              └───────────┘
```

---

### 3.2 Step 2: Company Qualification

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                         STEP 2: COMPANY QUALIFICATION FLOW                                 │
└───────────────────────────────────────────────────────────────────────────────────────────┘

                              ┌────────────────┐
                              │   User opens   │
                              │    Step 2      │
                              └───────┬────────┘
                                      │
                      ┌───────────────┴───────────────┐
                      │     Select Mode               │
                      │  POST /qualification-mode     │
                      └───────────────┬───────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
            ┌───────────────┐                   ┌───────────────┐
            │    MANUAL     │                   │      AI       │
            │     MODE      │                   │     MODE      │
            └───────┬───────┘                   └───────┬───────┘
                    │                                   │
                    ▼                                   ▼
    ┌─────────────────────────────┐     ┌─────────────────────────────┐
    │  GET /companies?status=all  │     │  Set criteria checkboxes    │
    │  Display all companies      │     │  POST /qualify-ai           │
    │  with checkboxes            │     │  (Async job)                │
    └──────────────┬──────────────┘     └──────────────┬──────────────┘
                   │                                    │
                   ▼                                    ▼
    ┌─────────────────────────────┐     ┌─────────────────────────────┐
    │  User selects companies     │     │  Worker calls OpenAI for    │
    │  POST /qualify-manual       │     │  each company               │
    │  { qualifications: [...] }  │     │  Saves: qualified/rejected  │
    └──────────────┬──────────────┘     └──────────────┬──────────────┘
                   │                                    │
                   │                                    ▼
                   │                    ┌─────────────────────────────┐
                   │                    │  Display AI results with    │
                   │                    │  qualified/rejected tabs    │
                   │                    │  GET /companies?status=X    │
                   │                    └──────────────┬──────────────┘
                   │                                   │
                   │                    ┌──────────────┴──────────────┐
                   │                    │  OPTIONAL: User overrides   │
                   │                    │  POST /override             │
                   │                    │  { overrides: [...] }       │
                   │                    └──────────────┬──────────────┘
                   │                                   │
                   └───────────────┬───────────────────┘
                                   │
                                   ▼
                   ┌─────────────────────────────┐
                   │  User clicks "Continue"     │
                   │  POST /companies/confirm    │
                   │  → status: contact_qual     │
                   │  → current_step: 3          │
                   └─────────────────────────────┘
                   

    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║  SIDE EFFECT: When company is REJECTED                                     ║
    ║  → All contacts under that company are auto-excluded                       ║
    ║  → Their qualification.status = "excluded"                                 ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 3.3 Step 3: Contact Qualification

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                         STEP 3: CONTACT QUALIFICATION FLOW                                 │
└───────────────────────────────────────────────────────────────────────────────────────────┘

    Same pattern as Step 2, but operating on contacts instead of companies:
    
    ┌────────────────────────────────────────────────────────────────────────────────────────┐
    │                                                                                        │
    │   1. POST /contacts/qualification-mode     → Select manual or AI                       │
    │                                                                                        │
    │   2a. MANUAL:                                                                          │
    │       GET /contacts?status=pending         → List contacts (excluding auto-excluded)   │
    │       POST /contacts/qualify-manual        → Bulk qualify/reject                       │
    │                                                                                        │
    │   2b. AI:                                                                              │
    │       POST /contacts/qualify-ai            → Async job (OpenAI)                        │
    │       GET /jobs/{id}                       → Poll for completion                       │
    │       GET /contacts?status=qualified       → View results                              │
    │       POST /contacts/override              → Optional overrides                        │
    │                                                                                        │
    │   3. POST /contacts/confirm                → Proceed to Step 4                         │
    │                                                                                        │
    └────────────────────────────────────────────────────────────────────────────────────────┘

    Note: Contacts from REJECTED companies are automatically excluded and not shown
```

---

### 3.4 Step 4: HubSpot Sync

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                              STEP 4: HUBSPOT SYNC FLOW                                     │
└───────────────────────────────────────────────────────────────────────────────────────────┘

    ┌────────────────┐          ┌────────────────┐          ┌────────────────┐
    │  User opens    │─────────▶│ GET /hubspot/  │─────────▶│ Display        │
    │    Step 4      │          │   contacts     │          │ company list   │
    └────────────────┘          └────────────────┘          │ with contacts  │
                                                            └───────┬────────┘
                                                                    │
                                                                    ▼
                                                            ┌────────────────┐
                                                            │ User selects   │
                                                            │ companies to   │
                                                            │ sync           │
                                                            └───────┬────────┘
                                                                    │
                                                                    ▼
                                                            ┌────────────────┐
                                                            │ POST /hubspot/ │
                                                            │     sync       │
                                                            │ (Async Job)    │
                                                            └───────┬────────┘
                                                                    │
                              ┌─────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────────────────────────┐
    │                                 WORKER PROCESS                                       │
    └─────────────────────────────────────────────────────────────────────────────────────┘
    
    For each company:
    ┌──────────────────────┐        ┌──────────────────────┐
    │ Search HubSpot for   │  YES   │ Use existing ID      │
    │ company by name      │───────▶│ company.hubspot.     │
    │ Exists?              │        │ sync_status=skipped  │
    └──────────┬───────────┘        └──────────────────────┘
               │ NO
               ▼
    ┌──────────────────────┐
    │ Create new company   │
    │ in HubSpot           │
    │ sync_status=synced   │
    └──────────┬───────────┘
               │
               ▼
    For each contact:
    ┌──────────────────────┐        ┌──────────────────────┐
    │ Search HubSpot for   │  YES   │ Associate contact to │
    │ contact by EMAIL     │───────▶│ company, skip create │
    │ Exists?              │        │ sync_status=skipped  │
    └──────────┬───────────┘        └──────────────────────┘
               │ NO
               ▼
    ┌──────────────────────┐
    │ Create new contact   │
    │ Associate to company │
    │ sync_status=synced   │
    └──────────────────────┘
    
    
    ┌─────────────────────────────────────────────────────────────────────────────────────┐
    │                                 FRONTEND CONTINUES                                   │
    └─────────────────────────────────────────────────────────────────────────────────────┘

                              ┌────────────────┐
    Poll for completion       │ GET /hubspot/  │
    ─────────────────────────▶│    status      │
                              └───────┬────────┘
                                      │
                                      ▼
                              ┌────────────────┐          ┌────────────────┐
                              │ Display sync   │─────────▶│ POST /hubspot/ │
                              │ results        │  Click   │   confirm      │
                              │ ✓ Synced: 45   │ Continue │ → Step 5       │
                              │ ⊘ Skipped: 5   │          └────────────────┘
                              └────────────────┘
```

---

### 3.5 Step 5: Personalization

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                            STEP 5: PERSONALIZATION FLOW                                    │
└───────────────────────────────────────────────────────────────────────────────────────────┘

    ┌────────────────┐
    │  User opens    │
    │    Step 5      │
    └───────┬────────┘
            │
            ▼
    ┌────────────────────────┐          ┌────────────────────────┐
    │ GET /personalization/  │          │ GET /personalization/  │
    │      contacts          │──────────│        stats           │
    └───────────┬────────────┘          └────────────┬───────────┘
                │                                     │
                └──────────────┬──────────────────────┘
                               │
                               ▼
                       ┌───────────────┐
                       │ Display stats │
                       │ + contact list│
                       └───────┬───────┘
                               │
            ┌──────────────────┴──────────────────┐
            │                                     │
            ▼                                     ▼
    ┌───────────────────┐               ┌───────────────────┐
    │  PENDING CONTACTS │               │ GENERATED CONTACTS│
    │  (Need generation)│               │ (Need review)     │
    └─────────┬─────────┘               └─────────┬─────────┘
              │                                   │
              ▼                                   │
    ┌───────────────────────────────┐             │
    │ POST /personalization/generate│             │
    │ { contact_ids: [...] }        │             │
    │ (Async Job)                   │             │
    └─────────────┬─────────────────┘             │
                  │                               │
                  ▼                               │
    ┌─────────────────────────────────────────────┼──────────────────────────────────────┐
    │                      WORKER PROCESS         │                                       │
    └─────────────────────────────────────────────┼──────────────────────────────────────┘
                                                  │
    For each contact:                             │
    ┌──────────────────────┐                      │
    │ Generate message via │──────┐               │
    │      OpenAI          │      │               │
    └──────────────────────┘      │               │
                                  ▼               │
    ┌──────────────────────┐  ┌───────────────────┼─────┐
    │ Generate deck via    │  │ Save to           │     │
    │      Manus           │──│ wizard_           │     │
    └──────────────────────┘  │ personalizations  │     │
                              │ + version history │     │
                              └───────────────────┼─────┘
                                                  │
    ┌─────────────────────────────────────────────┼──────────────────────────────────────┐
    │                      REVIEW FLOW            │                                       │
    └─────────────────────────────────────────────┼──────────────────────────────────────┘
                                                  │
                               ┌──────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  For each generated  │
                    │  message + deck:     │
                    └──────────┬───────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
    ┌──────────┐        ┌──────────────┐       ┌──────────┐
    │ APPROVE  │        │   REJECT &   │       │  EDIT    │
    │          │        │  REGENERATE  │       │ MANUALLY │
    └────┬─────┘        └──────┬───────┘       └────┬─────┘
         │                     │                    │
         ▼                     ▼                    ▼
    ┌──────────────┐   ┌──────────────────┐   ┌──────────────┐
    │POST /messages│   │POST /regenerate- │   │POST /messages│
    │  /review     │   │    messages      │   │   /update    │
    │{action:      │   │ Check: count < 5 │   │ Save manual  │
    │ "approve"}   │   │ (Async Job)      │   │ version      │
    └──────────────┘   └──────────────────┘   └──────────────┘
    
    
    ┌─────────────────────────────────────────────────────────────────────────────────────┐
    │                            FULLY APPROVED CHECK                                      │
    └─────────────────────────────────────────────────────────────────────────────────────┘
    
    Contact is FULLY APPROVED when:
    ┌─────────────────────────────────────────────────────────────────────────────────────┐
    │  message.status == "approved"  AND  deck.status == "approved"                        │
    │  → is_fully_approved = true                                                          │
    │  → Eligible for enrollment                                                           │
    └─────────────────────────────────────────────────────────────────────────────────────┘
    
                               ┌────────────────────┐
                               │ User clicks        │
                               │ "Continue with X"  │
                               │ POST /confirm      │
                               └────────────────────┘
```

---

### 3.6 Step 6: Enrollment

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                              STEP 6: ENROLLMENT FLOW                                       │
└───────────────────────────────────────────────────────────────────────────────────────────┘

    ┌────────────────┐
    │  User opens    │
    │    Step 6      │
    └───────┬────────┘
            │
            ├──────────────────────┐
            │                      │
            ▼                      ▼
    ┌────────────────┐     ┌───────────────────┐
    │ GET /lemlist/  │     │ GET /enrollment/  │
    │   sequences    │     │    contacts       │
    │ (From Lemlist) │     │ (Fully approved)  │
    └───────┬────────┘     └─────────┬─────────┘
            │                        │
            └──────────┬─────────────┘
                       │
                       ▼
               ┌───────────────┐
               │ Display:      │
               │ - Sequences   │
               │ - Contacts    │
               │   preview     │
               └───────┬───────┘
                       │
                       ▼
               ┌───────────────┐
               │ User selects  │
               │ sequence and  │
               │ clicks Enroll │
               └───────┬───────┘
                       │
                       ▼
               ┌───────────────────────┐
               │ POST /enrollment/     │
               │       enroll          │
               │ { sequence_id: "..." }│
               │ (Async Job)           │
               └───────────┬───────────┘
                           │
                           ▼
    ┌─────────────────────────────────────────────────────────────────────────────────────┐
    │                              WORKER PROCESS                                          │
    └─────────────────────────────────────────────────────────────────────────────────────┘
    
    For each fully approved contact:
    ┌──────────────────────────────┐
    │ Call Lemlist API:            │
    │ lemlist.enrollLead({         │
    │   email,                     │
    │   firstName, lastName,       │
    │   companyName,               │
    │   personalized_message,  ◀───┼─── From wizard_personalizations.message.approved_content
    │   deck_link              ◀───┼─── From wizard_personalizations.deck.approved_url
    │ })                           │
    └──────────────────────────────┘
                    │
                    ▼
    ┌──────────────────────────────┐
    │ Update wizard_contacts:      │
    │ enrollment.status = enrolled │
    │ enrollment.lemlist_lead_id   │
    └──────────────────────────────┘
    
    
    ┌─────────────────────────────────────────────────────────────────────────────────────┐
    │                              COMPLETION                                              │
    └─────────────────────────────────────────────────────────────────────────────────────┘
    
                       ┌───────────────────────┐
                       │ Job completes         │
                       │ POST /enrollment/     │
                       │      confirm          │
                       │ (auto-called)         │
                       └───────────┬───────────┘
                                   │
                                   ▼
                       ┌───────────────────────┐
                       │ Campaign status =     │
                       │ "outreach"            │
                       └───────────┬───────────┘
                                   │
                                   ▼
                       ┌───────────────────────┐
                       │ CAMPAIGN COMPLETE     │
                       │ Show success screen   │
                       │ Link to Lemlist       │
                       └───────────────────────┘
```

---

## 4. Async Job Pattern

### 4.1 Job Lifecycle

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                               ASYNC JOB PATTERN                                            │
└───────────────────────────────────────────────────────────────────────────────────────────┘

    FRONTEND                                      BACKEND
    ─────────                                     ───────
    
    ┌─────────────────┐                          ┌─────────────────┐
    │ User initiates  │                          │                 │
    │ action (e.g.,   │──── POST /action ────────▶│ Validate input │
    │ find prospects) │                          │                 │
    └─────────────────┘                          └────────┬────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │ Create Job:     │
                                                 │ status: pending │
                                                 │ progress: 0/N   │
                                                 └────────┬────────┘
                                                          │
    ┌─────────────────┐                                   │
    │ Receive:        │◀────── 202 Accepted ──────────────┤
    │ { job_id: ... } │                                   │
    └────────┬────────┘                                   │
             │                                            │
             │                                   ┌────────┴────────┐
             │                                   │ BACKGROUND      │
             │                                   │ WORKER          │
             │                                   │ Picks up job    │
             │                                   └────────┬────────┘
             │                                            │
             │                                   ┌────────┴────────┐
             │                                   │ status:         │
             │                                   │  processing     │
             ▼                                   │ progress: X/N   │
    ┌─────────────────┐                          └─────────────────┘
    │ POLLING LOOP    │                                   │
    │ Every 2 seconds │                                   │
    └────────┬────────┘                                   │
             │                                            │
             ▼                                            │
    ┌─────────────────┐                          ┌────────┴────────┐
    │ GET /jobs/{id}  │─────────────────────────▶│ Return current  │
    │                 │◀─────────────────────────│ job status      │
    └────────┬────────┘                          └─────────────────┘
             │
             ├──── status == "processing" ──▶ Continue polling
             │
             ├──── status == "completed" ───▶ Stop polling, refresh data
             │
             └──── status == "failed" ──────▶ Show error, offer retry
             
             
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║  JOB TYPES:                                                                ║
    ║  • prospect_fetch         → Apollo API                                     ║
    ║  • company_qualification_ai → OpenAI                                       ║
    ║  • contact_qualification_ai → OpenAI                                       ║
    ║  • hubspot_sync           → HubSpot API                                    ║
    ║  • personalization_generate → OpenAI + Manus                               ║
    ║  • personalization_regenerate_messages → OpenAI                            ║
    ║  • lemlist_enrollment     → Lemlist API                                    ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 4.2 Job Error Handling & Retry

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                               JOB ERROR & RETRY FLOW                                       │
└───────────────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐
    │ Job fails       │
    │ (External API   │
    │  error, timeout)│
    └────────┬────────┘
             │
             ▼
    ┌─────────────────────────────────────────┐
    │ Save error to job:                      │
    │ {                                       │
    │   status: "failed",                     │
    │   error: {                              │
    │     code: "EXTERNAL_SERVICE_ERROR",     │
    │     message: "Apollo rate limit",       │
    │     details: [...]                      │
    │   }                                     │
    │ }                                       │
    └─────────────────────────────────────────┘
             │
             ▼
    ┌─────────────────┐       ┌─────────────────┐
    │ Frontend shows  │       │ User clicks     │
    │ error message   │──────▶│ "Retry"         │
    │ + Retry button  │       │                 │
    └─────────────────┘       └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │ POST /jobs/{id} │
                              │     /retry      │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────────────────────┐
                              │ Create new job:                 │
                              │ {                               │
                              │   status: "pending",            │
                              │   original_job_id: old_id,      │
                              │   retry_count: 1                │
                              │ }                               │
                              └─────────────────────────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │ Normal job      │
                              │ processing      │
                              │ begins again    │
                              └─────────────────┘
```

---

## 5. State Machine

### 5.1 Contact State Flow

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                             CONTACT LIFECYCLE STATE MACHINE                                │
└───────────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌──────────────────────┐
                                    │     Step 1:          │
                                    │  Created from Apollo │
                                    └──────────┬───────────┘
                                               │
                                               ▼
    ┌────────────────────────────────────────────────────────────────────────────────┐
    │                         qualification.status                                    │
    │                                                                                │
    │   ┌─────────┐      Company         ┌──────────┐                               │
    │   │ pending │──── rejected? ──────▶│ excluded │ (Contact auto-excluded)       │
    │   └────┬────┘                      └──────────┘                               │
    │        │                                                                       │
    │        │ Qualify (AI or Manual)                                                │
    │        │                                                                       │
    │   ┌────┴────────────────┐                                                      │
    │   │                     │                                                      │
    │   ▼                     ▼                                                      │
    │ ┌───────────┐      ┌──────────┐                                               │
    │ │ qualified │      │ rejected │                                               │
    │ └─────┬─────┘      └──────────┘                                               │
    │       │                                                                        │
    └───────┼────────────────────────────────────────────────────────────────────────┘
            │
            │ Step 4: HubSpot Sync
            ▼
    ┌────────────────────────────────────────────────────────────────────────────────┐
    │                          hubspot.sync_status                                    │
    │                                                                                │
    │   ┌────────────┐     ┌─────────┐     ┌────────┐                                │
    │   │ not_synced │────▶│ syncing │────▶│ synced │                                │
    │   └────────────┘     └────┬────┘     └────────┘                                │
    │                           │                                                    │
    │                           │ Email exists                                       │
    │                           ▼ in HubSpot                                         │
    │                      ┌─────────┐                                               │
    │                      │ skipped │                                               │
    │                      └─────────┘                                               │
    │                                                                                │
    └───────┬────────────────────────────────────────────────────────────────────────┘
            │
            │ Step 5: Personalization
            ▼
    ┌────────────────────────────────────────────────────────────────────────────────┐
    │                      personalization.is_fully_approved                          │
    │                                                                                │
    │   Message                                 Deck                                  │
    │   ┌─────────┐  ┌────────────┐  ┌──────────┐    ┌─────────┐  ┌──────────┐       │
    │   │ pending │─▶│ generating │─▶│ generated│    │ pending │─▶│ generated│       │
    │   └─────────┘  └────────────┘  └────┬─────┘    └─────────┘  └────┬─────┘       │
    │                                     │                            │              │
    │                          ┌──────────┴──────────┐      ┌──────────┴──────────┐  │
    │                          │                     │      │                     │  │
    │                          ▼                     ▼      ▼                     ▼  │
    │                     ┌──────────┐          ┌──────────┐                ┌──────────┐
    │                     │ approved │          │ rejected │                │ approved │
    │                     └────┬─────┘          └──────────┘                └────┬─────┘
    │                          │                                                 │  │
    │                          └────────────────┬────────────────────────────────┘  │
    │                                           │                                    │
    │                                           ▼                                    │
    │                               ┌──────────────────────┐                         │
    │                               │ is_fully_approved =  │                         │
    │                               │        TRUE          │                         │
    │                               └──────────────────────┘                         │
    │                                                                                │
    └───────┬────────────────────────────────────────────────────────────────────────┘
            │
            │ Step 6: Enrollment
            ▼
    ┌────────────────────────────────────────────────────────────────────────────────┐
    │                          enrollment.status                                      │
    │                                                                                │
    │   ┌──────────────┐     ┌───────────┐     ┌──────────┐                          │
    │   │ not_enrolled │────▶│ enrolling │────▶│ enrolled │                          │
    │   └──────────────┘     └───────────┘     └──────────┘                          │
    │                                                                                │
    └────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Data Flow Diagrams

### 6.1 Data Transformation Pipeline

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                           DATA TRANSFORMATION PIPELINE                                     │
└───────────────────────────────────────────────────────────────────────────────────────────┘

    ┌───────────────┐
    │  Apollo API   │
    │  (External)   │
    └───────┬───────┘
            │
            │ Raw company + contact data
            ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                        STEP 1: INGESTION                         │
    │                                                                  │
    │   wizard_companies:                                              │
    │   - source_data (raw)                                            │
    │   - Normalized fields (name, industry, revenue...)               │
    │   - qualification.status = pending                               │
    │                                                                  │
    │   wizard_contacts:                                               │
    │   - source_data (raw)                                            │
    │   - Normalized fields (email, name, job_title...)                │
    │   - company_id reference                                         │
    │   - qualification.status = pending                               │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘
            │
            ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                   STEP 2-3: QUALIFICATION                        │
    │                                                                  │
    │   OpenAI evaluates companies/contacts                            │
    │                                                                  │
    │   wizard_companies:                                              │
    │   - qualification.ai_decision                                    │
    │   - qualification.ai_reason                                      │
    │   - qualification.status = qualified | rejected                  │
    │                                                                  │
    │   wizard_contacts:                                               │
    │   - qualification.ai_decision                                    │
    │   - qualification.status = qualified | rejected | excluded       │
    │                                                                  │
    │   FILTER: Only qualified contacts proceed                        │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘
            │
            ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                     STEP 4: HUBSPOT SYNC                         │
    │                                                                  │
    │   HubSpot API creates/updates records                            │
    │                                                                  │
    │   wizard_companies:                                              │
    │   - hubspot.hubspot_company_id                                   │
    │   - hubspot.sync_status = synced | skipped                       │
    │                                                                  │
    │   wizard_contacts:                                               │
    │   - hubspot.hubspot_contact_id                                   │
    │   - hubspot.sync_status = synced | skipped                       │
    │                                                                  │
    │   FILTER: Only synced contacts proceed                           │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘
            │
            ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                   STEP 5: PERSONALIZATION                        │
    │                                                                  │
    │   OpenAI + Manus generate content                                │
    │                                                                  │
    │   wizard_personalizations:                                       │
    │   - message.generated_content → message.approved_content         │
    │   - deck.generated_url → deck.approved_url                       │
    │   - is_fully_approved = true (when both approved)                │
    │                                                                  │
    │   wizard_personalization_versions:                               │
    │   - Version history for each regeneration/edit                   │
    │                                                                  │
    │   FILTER: Only fully_approved contacts proceed                   │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘
            │
            ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                     STEP 6: ENROLLMENT                           │
    │                                                                  │
    │   Lemlist API enrolls contacts with personalization              │
    │                                                                  │
    │   wizard_contacts:                                               │
    │   - enrollment.lemlist_lead_id                                   │
    │   - enrollment.status = enrolled                                 │
    │                                                                  │
    │   Payload to Lemlist:                                            │
    │   {                                                              │
    │     email, firstName, lastName, companyName,                     │
    │     personalized_message: approved_content,                      │
    │     deck_link: approved_url                                      │
    │   }                                                              │
    │                                                                  │
    └─────────────────────────────────────────────────────────────────┘
            │
            ▼
    ┌───────────────┐
    │   Lemlist     │
    │   (External)  │
    │   Outreach    │
    └───────────────┘
```

---

### 6.2 Metrics Aggregation

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                            METRICS AGGREGATION FLOW                                        │
└───────────────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────────────────┐
    │                        ATOMIC INCREMENTS ON EACH ACTION                              │
    └─────────────────────────────────────────────────────────────────────────────────────┘
    
    Action                                    Metric Updated
    ──────                                    ──────────────
    Company added (Step 1)     ─────────────▶ $inc { metrics.companies_prospected: 1 }
    
    Company AI qualified       ─────────────▶ $inc { metrics.ai_company_qualified: 1 }
    Company AI rejected        ─────────────▶ $inc { metrics.ai_company_rejected: 1 }
    
    Company override to qual   ─────────────▶ $inc { metrics.company_overrides_to_qualified: 1 }
    Company override to rej    ─────────────▶ $inc { metrics.company_overrides_to_rejected: 1 }
    
    Contact synced             ─────────────▶ $inc { metrics.contacts_synced: 1 }
    Contact skipped            ─────────────▶ $inc { metrics.contacts_sync_skipped: 1 }
    
    Message generated          ─────────────▶ $inc { metrics.messages_generated: 1 }
    Message approved (1st try) ─────────────▶ $inc { metrics.messages_approved_first_try: 1 }
    Message regenerated        ─────────────▶ $inc { metrics.messages_regenerated: 1 }
    Message manually edited    ─────────────▶ $inc { metrics.messages_manually_edited: 1 }
    
    Contact enrolled           ─────────────▶ $inc { metrics.contacts_enrolled: 1 }
    
    
    ┌─────────────────────────────────────────────────────────────────────────────────────┐
    │                        COUNTS ON STEP CONFIRMATION                                   │
    └─────────────────────────────────────────────────────────────────────────────────────┘
    
    On /companies/confirm:
    ┌──────────────────────────────────────────────────────────────────────────────────┐
    │ const qualified = db.wizard_companies.countDocuments({                            │
    │   campaign_id, is_deleted: false, "qualification.status": "qualified"             │
    │ });                                                                               │
    │                                                                                   │
    │ db.wizard_campaigns.updateOne(                                                    │
    │   { _id: campaign_id },                                                           │
    │   { $set: { "metrics.companies_qualified": qualified } }                          │
    │ );                                                                                │
    └──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Integration Flows

### 7.1 Third-Party Integration Architecture

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                        THIRD-PARTY INTEGRATION ARCHITECTURE                                │
└───────────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌──────────────────┐
                                    │     FRONTEND     │
                                    │     (React)      │
                                    └────────┬─────────┘
                                             │
                                             │ All API calls
                                             ▼
                                    ┌──────────────────┐
                                    │     BACKEND      │
                                    │    (Python)      │
                                    └────────┬─────────┘
                                             │
                                             │ Third-party calls
                                             │ (Server-to-server)
              ┌──────────────────────────────┼──────────────────────────────┐
              │                              │                              │
              ▼                              ▼                              ▼
    ┌─────────────────┐           ┌─────────────────┐           ┌─────────────────┐
    │                 │           │                 │           │                 │
    │   Apollo API    │           │   OpenAI API    │           │   Manus API     │
    │                 │           │                 │           │                 │
    │ • Prospect      │           │ • Qualify       │           │ • Generate      │
    │   search        │           │   companies     │           │   decks         │
    │ • Company data  │           │ • Qualify       │           │                 │
    │ • Contact data  │           │   contacts      │           │                 │
    │                 │           │ • Generate      │           │                 │
    │                 │           │   messages      │           │                 │
    │                 │           │                 │           │                 │
    └─────────────────┘           └─────────────────┘           └─────────────────┘
              │
              │
              ├──────────────────────────────┬──────────────────────────────┐
              │                              │                              │
              ▼                              ▼                              ▼
    ┌─────────────────┐           ┌─────────────────┐           ┌─────────────────┐
    │                 │           │                 │           │                 │
    │  HubSpot API    │           │  Lemlist API    │           │   MongoDB       │
    │                 │           │                 │           │   (Internal)    │
    │ • Create        │           │ • Get sequences │           │                 │
    │   companies     │           │ • Enroll leads  │           │ • wizard_*      │
    │ • Create        │           │ • Personalized  │           │   collections   │
    │   contacts      │           │   variables     │           │                 │
    │ • Associate     │           │                 │           │                 │
    │                 │           │                 │           │                 │
    └─────────────────┘           └─────────────────┘           └─────────────────┘
    
    
    ╔═══════════════════════════════════════════════════════════════════════════════════════╗
    ║  CREDENTIALS:                                                                          ║
    ║  All API credentials are stored server-side (hardcoded for now, env vars later)        ║
    ║                                                                                        ║
    ║  Apollo:     APOLLO_API_KEY                                                            ║
    ║  OpenAI:     OPENAI_API_KEY                                                            ║
    ║  Manus:      MANUS_API_KEY                                                             ║
    ║  HubSpot:    HUBSPOT_ACCESS_TOKEN                                                      ║
    ║  Lemlist:    LEMLIST_API_KEY                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════════════════╝
```

---

### 7.2 OpenAI Integration Details

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                              OPENAI INTEGRATION FLOW                                       │
└───────────────────────────────────────────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────────────────────────────────────┐
    │                          COMPANY QUALIFICATION PROMPT                               │
    └────────────────────────────────────────────────────────────────────────────────────┘
    
    SYSTEM:
    ┌────────────────────────────────────────────────────────────────────────────────────┐
    │ You are a B2B sales qualification expert. Evaluate companies based on the given    │
    │ criteria and return a JSON response with your decision.                            │
    └────────────────────────────────────────────────────────────────────────────────────┘
    
    USER:
    ┌────────────────────────────────────────────────────────────────────────────────────┐
    │ Evaluate this company:                                                             │
    │ Name: {company.name}                                                               │
    │ Industry: {company.industry}                                                       │
    │ Employee Count: {company.employee_count}                                           │
    │ Revenue: {company.revenue}                                                         │
    │ Location: {company.location}                                                       │
    │                                                                                    │
    │ Criteria to check:                                                                 │
    │ - Has engineering team: {criteria.has_engineering_team}                            │
    │ - Is hiring technical roles: {criteria.is_hiring_technical}                        │
    │ - Uses cloud solutions: {criteria.uses_cloud_solutions}                            │
    │ - Recent funding: {criteria.recent_funding}                                        │
    │ - Growth phase: {criteria.growth_phase}                                            │
    │                                                                                    │
    │ Return JSON: { "qualified": true/false, "confidence": "high/medium/low",           │
    │                "reason": "explanation" }                                           │
    └────────────────────────────────────────────────────────────────────────────────────┘
    
    
    ┌────────────────────────────────────────────────────────────────────────────────────┐
    │                          MESSAGE PERSONALIZATION PROMPT                             │
    └────────────────────────────────────────────────────────────────────────────────────┘
    
    SYSTEM:
    ┌────────────────────────────────────────────────────────────────────────────────────┐
    │ You are a B2B sales outreach expert. Write personalized, compelling cold emails    │
    │ that are professional yet conversational. Keep them under 150 words.               │
    └────────────────────────────────────────────────────────────────────────────────────┘
    
    USER:
    ┌────────────────────────────────────────────────────────────────────────────────────┐
    │ Write a personalized outreach message for:                                         │
    │                                                                                    │
    │ Contact:                                                                           │
    │ - Name: {contact.first_name} {contact.last_name}                                   │
    │ - Title: {contact.job_title}                                                       │
    │                                                                                    │
    │ Company:                                                                           │
    │ - Name: {company.name}                                                             │
    │ - Industry: {company.industry}                                                     │
    │ - Size: {company.employee_count}                                                   │
    │                                                                                    │
    │ Product we're selling: {campaign.product_name}                                     │
    │                                                                                    │
    │ Make it personalized based on their role and company.                              │
    └────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 7.3 HubSpot Sync Details

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                              HUBSPOT SYNC FLOW DETAILS                                     │
└───────────────────────────────────────────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────────────────────────────────────┐
    │                            COMPANY CREATE/LOOKUP                                    │
    └────────────────────────────────────────────────────────────────────────────────────┘
    
    1. Search for existing company by name:
       POST https://api.hubapi.com/crm/v3/objects/companies/search
       Body: { "filterGroups": [{ "filters": [{ "propertyName": "name",
                                                "operator": "EQ",
                                                "value": "{company_name}" }] }] }
    
    2. If not found, create:
       POST https://api.hubapi.com/crm/v3/objects/companies
       Body: {
         "properties": {
           "name": "{company_name}",
           "industry": "{industry}",
           "numberofemployees": "{employee_count}",
           "annualrevenue": "{revenue}",
           "website": "{website}"
         }
       }
    
    
    ┌────────────────────────────────────────────────────────────────────────────────────┐
    │                            CONTACT CREATE/LOOKUP                                    │
    └────────────────────────────────────────────────────────────────────────────────────┘
    
    1. Search for existing contact by EMAIL:
       POST https://api.hubapi.com/crm/v3/objects/contacts/search
       Body: { "filterGroups": [{ "filters": [{ "propertyName": "email",
                                                "operator": "EQ",
                                                "value": "{email}" }] }] }
    
    2. If found, skip create but associate:
       → hubspot.sync_status = "skipped"
       → Still associate to company (step 3)
    
    3. If not found, create:
       POST https://api.hubapi.com/crm/v3/objects/contacts
       Body: {
         "properties": {
           "email": "{email}",
           "firstname": "{first_name}",
           "lastname": "{last_name}",
           "jobtitle": "{job_title}",
           "phone": "{phone}"
         }
       }
    
    4. Associate contact to company:
       PUT https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}/associations/companies/{company_id}/{association_type}
```

---

### 7.4 Lemlist Enrollment Details

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                              LEMLIST ENROLLMENT DETAILS                                    │
└───────────────────────────────────────────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────────────────────────────────────┐
    │                              GET SEQUENCES                                          │
    └────────────────────────────────────────────────────────────────────────────────────┘
    
    GET https://api.lemlist.com/api/campaigns
    
    Response:
    [
      {
        "_id": "seq_abc123",
        "name": "Enterprise Outreach - Q1 2025",
        "sequence": [
          { "type": "email", "subject": "..." },
          { "type": "email", "subject": "..." }
        ]
      }
    ]
    
    
    ┌────────────────────────────────────────────────────────────────────────────────────┐
    │                              ENROLL LEAD                                            │
    └────────────────────────────────────────────────────────────────────────────────────┘
    
    POST https://api.lemlist.com/api/campaigns/{sequence_id}/leads/{email}
    
    Body:
    {
      "firstName": "{first_name}",
      "lastName": "{last_name}",
      "companyName": "{company_name}",
      
      // Custom variables for email templates
      "personalized_message": "{approved_message_content}",
      "deck_link": "{approved_deck_url}"
    }
    
    
    ┌────────────────────────────────────────────────────────────────────────────────────┐
    │                    EMAIL TEMPLATE VARIABLES IN LEMLIST                              │
    └────────────────────────────────────────────────────────────────────────────────────┘
    
    Lemlist email templates can use:
    
    {{firstName}}              → "Sarah"
    {{lastName}}               → "Chen"
    {{companyName}}            → "TechFlow Solutions"
    {{personalized_message}}   → AI-generated personalized message
    {{deck_link}}              → Manus-generated deck URL
    
    Example template:
    ┌────────────────────────────────────────────────────────────────────────────────────┐
    │ Hi {{firstName}},                                                                  │
    │                                                                                    │
    │ {{personalized_message}}                                                           │
    │                                                                                    │
    │ I've also prepared a quick overview deck for you: {{deck_link}}                    │
    │                                                                                    │
    │ Would you have 15 minutes this week for a quick call?                              │
    │                                                                                    │
    │ Best,                                                                              │
    │ [Sender Name]                                                                      │
    └────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

This document provides visual representations of:

1. **High-Level Flow**: End-to-end campaign wizard journey
2. **Campaign Lifecycle**: Status state machine with all transitions
3. **Step-by-Step Flows**: Detailed API interaction diagrams for each wizard step
4. **Async Job Pattern**: How background jobs work with polling
5. **State Machine**: Contact lifecycle through all states
6. **Data Flow**: How data transforms through the pipeline
7. **Integrations**: Third-party service integration architecture

---

*End of Campaign Wizard Flowchart Document*

