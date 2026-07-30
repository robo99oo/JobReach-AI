# JobReach AI

JobReach AI is an AI-powered outbound email automation platform built with FastAPI, SQLAlchemy, SQLite, and Ollama. It generates personalized outreach emails using an LLM while validating the output to reduce unsupported claims.

---

## Features

- AI-powered email generation using Ollama
- Campaign management
- Master Profile management
- Automatic follow-up creation
- Prompt grounding
- Email validation
- FastAPI REST APIs
- SQLite database
- Swagger API documentation

---

## Architecture

```text
Campaign Request
       ↓
Approved Master Profile
       ↓
Prompt Builder
       ↓
Ollama LLM
       ↓
Email Validator
       ↓
SQLite Database
       ↓
Status: DRAFT_READY
```
---

## Tech Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic

### AI
- Ollama
- Llama 3.2 (3B)
- Prompt Engineering

### Tools
- Git
- GitHub
- Swagger UI
- HTTPX
- Pytest


## Current Features

- ✅ Master Profile Management
- ✅ Campaign Management
- ✅ AI Email Generation
- ✅ Prompt Grounding
- ✅ Email Validation
- ✅ Automatic Follow-up Creation
- ✅ SQLite Persistence
- ✅ REST APIs
- ✅ Swagger Documentation