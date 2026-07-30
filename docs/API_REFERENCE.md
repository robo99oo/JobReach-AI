# JobReach AI API Reference

## Base URL

```text
http://127.0.0.1:8000
```

Interactive Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

## Health Check

### `GET /`

Checks whether the application is running.

#### Example Response

```json
{
  "application": "JobReach AI",
  "version": "1.0.0",
  "status": "running"
}
```

---

## Master Profile APIs

### `POST /master-profile`

Creates the approved candidate profile used during email generation.

#### Example Request

```json
{
  "full_name": "Kshiti Tyagi",
  "email": "candidate@example.com",
  "phone": "9999999999",
  "location": "Meerut, India",
  "preferred_roles": "Generative AI Engineer, AI Engineer",
  "skills": "Python, FastAPI, LangChain, RAG, FAISS, MongoDB",
  "projects": "Agentic HR OS, OCR Aadhaar Verification, FIFA Nexus AI",
  "resume_text": "Approved resume content",
  "portfolio_url": "https://example.com",
  "github_url": "https://github.com/robo99oo",
  "is_approved": true
}
```

#### Success Response

```json
{
  "id": 1,
  "full_name": "Kshiti Tyagi",
  "is_approved": true
}
```

#### Possible Errors

```text
422 Unprocessable Entity
```

Returned when required fields are missing or invalid.

---

### `GET /master-profile`

Returns the current approved Master Profile.

#### Success Response

```json
{
  "id": 1,
  "full_name": "Kshiti Tyagi",
  "preferred_roles": "Generative AI Engineer, AI Engineer",
  "is_approved": true
}
```

#### Possible Errors

```text
404 Not Found
```

Returned when no approved Master Profile exists.

---

## Campaign APIs

### `POST /campaigns`

Creates a new outreach campaign.

Three follow-up steps are created automatically.

#### Example Request Without JD

```json
{
  "company_name": "Amazon",
  "contact_name": "Hiring Manager",
  "contact_title": "Engineering Manager",
  "recipient_email": "manager@example.com",
  "mode": "WITHOUT_JD",
  "job_description": null,
  "target_role": "Generative AI Engineer"
}
```

#### Example Request With JD

```json
{
  "company_name": "Microsoft",
  "contact_name": "Recruiter",
  "contact_title": "Technical Recruiter",
  "recipient_email": "recruiter@example.com",
  "mode": "WITH_JD",
  "job_description": "The role requires Python, FastAPI, RAG, and LLM experience.",
  "target_role": "AI Engineer"
}
```

#### Success Response

```json
{
  "id": 1,
  "company_name": "Amazon",
  "recipient_email": "manager@example.com",
  "status": "PENDING_GEN"
}
```

#### Possible Errors

```text
409 Conflict
```

Returned when the recipient email already exists.

```text
422 Unprocessable Entity
```

Returned when request validation fails.

---

### `GET /campaigns`

Returns all campaigns.

#### Example Response

```json
[
  {
    "id": 1,
    "company_name": "Amazon",
    "recipient_email": "manager@example.com",
    "status": "PENDING_GEN"
  },
  {
    "id": 2,
    "company_name": "Microsoft",
    "recipient_email": "recruiter@example.com",
    "status": "DRAFT_READY"
  }
]
```

---

### `GET /campaigns/{campaign_id}`

Returns one campaign by ID.

#### Example Request

```text
GET /campaigns/1
```

#### Example Response

```json
{
  "id": 1,
  "company_name": "Amazon",
  "contact_name": "Hiring Manager",
  "recipient_email": "manager@example.com",
  "mode": "WITHOUT_JD",
  "target_role": "Generative AI Engineer",
  "status": "PENDING_GEN",
  "email_subject": null,
  "email_body": null,
  "gmail_thread_id": null,
  "stop_reason": null
}
```

#### Possible Errors

```text
404 Not Found
```

Returned when the campaign does not exist.

---

### `POST /campaigns/{campaign_id}/generate`

Generates an outreach email using the approved Master Profile and Ollama.

The campaign must be in one of these states:

```text
PENDING_GEN
DEAD_LETTER
```

#### Example Request

```text
POST /campaigns/1/generate
```

No request body is required.

#### Successful Response

```json
{
  "id": 1,
  "status": "DRAFT_READY",
  "email_subject": "Exploring Generative AI Engineer Opportunities",
  "email_body": "Dear Hiring Manager, I am reaching out...",
  "stop_reason": null
}
```

#### Validation Failure Response

```json
{
  "id": 1,
  "status": "DEAD_LETTER",
  "email_subject": null,
  "email_body": null,
  "stop_reason": "Generated email failed validation."
}
```

#### Possible Errors

```text
404 Not Found
```

Campaign does not exist.

```text
409 Conflict
```

Campaign is not in an allowed generation state.

```text
422 Unprocessable Entity
```

No approved Master Profile exists or generation validation fails.

```text
503 Service Unavailable
```

Ollama is unavailable or the configured model cannot be reached.

---

### `GET /campaigns/{campaign_id}/follow-ups`

Returns the three follow-up steps created for a campaign.

#### Example Response

```json
[
  {
    "step_number": 1,
    "due_at": "2026-08-02T10:00:00",
    "requires_approval": true,
    "status": "PENDING"
  },
  {
    "step_number": 2,
    "due_at": "2026-08-06T10:00:00",
    "requires_approval": true,
    "status": "PENDING"
  },
  {
    "step_number": 3,
    "due_at": "2026-08-11T10:00:00",
    "requires_approval": true,
    "status": "PENDING"
  }
]
```

#### Possible Errors

```text
404 Not Found
```

Returned when the campaign does not exist.

---

## Campaign Modes

### `WITH_JD`

Used when a job description is supplied.

The model may reference only information explicitly present in the supplied job description.

### `WITHOUT_JD`

Used for exploratory outreach.

The generated email must not claim that:

- A job opening exists
- A vacancy was posted
- The company is hiring
- The company has a specific initiative
- The recipient owns a specific responsibility

---

## Campaign Statuses

```text
PENDING_GEN
DRAFT_READY
DEAD_LETTER
SENT
REPLIED
BOUNCED
STOPPED
```

Some statuses are planned for later phases and may not yet be active.

---

## Follow-Up Statuses

```text
PENDING
SENT
CANCELLED
```

---

## Error Response Format

FastAPI validation errors generally follow this structure:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": [
        "body",
        "full_name"
      ],
      "msg": "Field required"
    }
  ]
}
```

Application-level errors may follow this structure:

```json
{
  "detail": "Campaign not found."
}
```

---

## Planned Gmail APIs

These endpoints are part of the upcoming development phase.

### Create Gmail Draft

```text
POST /campaigns/{campaign_id}/gmail-draft
```

### Send Approved Draft

```text
POST /campaigns/{campaign_id}/send
```

### Check Reply Status

```text
GET /campaigns/{campaign_id}/reply-status
```

### Cancel Pending Follow-Ups

```text
POST /campaigns/{campaign_id}/cancel-follow-ups
```