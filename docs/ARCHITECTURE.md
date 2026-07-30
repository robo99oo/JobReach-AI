# JobReach AI Architecture

## System Overview

JobReach AI is a FastAPI-based outbound email automation platform that generates grounded, personalized outreach emails using a local LLM through Ollama.

The system separates campaign management, AI generation, validation, persistence, and future Gmail integration into independent components.

## High-Level Architecture

```text
User / Swagger UI
        ↓
FastAPI Routes
        ↓
Campaign Service
        ↓
Approved Master Profile
        ↓
Prompt Builder
        ↓
Ollama LLM
        ↓
Email Parser
        ↓
Deterministic Validator
        ↓
SQLAlchemy Models
        ↓
SQLite Database
```

## Email Generation Workflow

```text
Campaign created
        ↓
Status: PENDING_GEN
        ↓
Approved Master Profile loaded
        ↓
Grounded prompt generated
        ↓
Prompt sent to Ollama
        ↓
Subject and body parsed
        ↓
Validation checks executed
        ↓
Valid draft
        ↓
Status: DRAFT_READY
```

If validation fails:

```text
Generated email
        ↓
Validation failure
        ↓
Failure reason stored
        ↓
Status: DEAD_LETTER
```

## Core Components

### FastAPI Routes

The API layer receives requests and returns structured responses.

Main responsibilities:

- Create and retrieve campaigns
- Create and retrieve the Master Profile
- Generate AI email drafts
- Retrieve follow-up steps
- Validate campaign state before processing

### Master Profile

The Master Profile acts as the approved source of truth for candidate information.

It may contain:

- Candidate name
- Resume text
- Skills
- Projects
- Portfolio URL
- GitHub URL
- Preferred roles
- Availability

Only an approved Master Profile can be used during generation.

### Campaign

A Campaign represents one outreach target.

It stores:

- Company information
- Contact information
- Recipient email
- Target role
- Campaign mode
- Optional job description
- Generated subject
- Generated body
- Gmail thread ID
- Campaign status
- Stop reason

The recipient email is unique to prevent duplicate processing.

### Prompt Builder

The Prompt Builder combines:

- Approved profile data
- Resume content
- Campaign data
- Target role
- Optional job description
- Safety and grounding rules

It instructs the model not to invent:

- Vacancies
- Company initiatives
- Candidate achievements
- Technologies
- Metrics
- Responsibilities

### Ollama Service

The Ollama service sends prompts to a locally running model.

Current model:

```text
llama3.2:3b
```

Current endpoint:

```text
http://localhost:11434/api/generate
```

### Email Parser

The generated output is expected in this format:

```text
Subject:
Generated subject

Body:
Generated email body
```

The parser separates the subject and body before validation.

### Deterministic Validator

The validator protects the workflow from unsafe or unusable output.

Current checks include:

- Subject must exist
- Body must exist
- Word count must be between 90 and 160 words
- Unsupported numbers must not appear
- Required output structure must be present

### Follow-Up Engine

Every campaign automatically receives three follow-up steps.

Default schedule:

```text
Step 1: 3 days
Step 2: 7 days
Step 3: 12 days
```

Each step can store:

- Due date
- Subject
- Body
- Approval requirement
- Status
- Sent timestamp
- Cancellation reason

### Database Layer

SQLAlchemy provides the ORM layer.

Current database:

```text
SQLite
```

Main tables:

```text
MasterProfile
Campaign
FollowUpStep
TelemetryEvent
```

## Campaign State Flow

```text
PENDING_GEN
     ↓
DRAFT_READY
     ↓
Future: GMAIL_DRAFT_CREATED
     ↓
Future: SENT
     ↓
Future: REPLIED / BOUNCED / STOPPED
```

Failure flow:

```text
PENDING_GEN
     ↓
DEAD_LETTER
```

## Future Gmail Architecture

```text
DRAFT_READY
     ↓
Google OAuth
     ↓
Gmail Draft Created
     ↓
Manual Approval
     ↓
Email Sent
     ↓
Gmail Thread ID Stored
     ↓
Reply Monitoring
     ↓
Pending Follow-Ups Cancelled
```

## Safety Boundaries

The system must not:

- Scrape or blast large recipient lists
- Invent jobs, initiatives, or responsibilities
- Invent candidate experience or metrics
- Continue follow-ups after a reply
- Continue after rejection or bounce
- Treat an open-tracking event as proof of human reading

## Planned Production Improvements

- PostgreSQL support
- Alembic database migrations
- Redis-backed background jobs
- Gmail OAuth integration
- Reply detection
- Bounce detection
- Structured logging
- Retry policies
- Rate limiting
- Authentication
- Analytics dashboard
- Docker deployment