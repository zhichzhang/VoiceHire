# VoiceHire

An AI-powered voice interview platform that conducts structured technical interviews, dynamically generates follow-up questions, evaluates candidate responses, and produces detailed hiring reports.

VoiceHire combines resume-aware interview generation, real-time speech transcription, dynamic LLM orchestration, session recovery, and automated candidate evaluation into a unified end-to-end technical interviewing platform.


## Demo Video

Watch the complete demo:

[Demo Video](https://drive.google.com/file/d/13cW2mWJeB89b1Tsfnue-y3bC9dznQat1/view?usp=sharing)

The demo walks through:

- Resume submission
- Resume validation
- Interview initialization
- Dynamic question generation
- Voice-based interview interaction
- Session recovery workflow
- Final evaluation report generation



# Features

## Real-Time AI Interviewing

VoiceHire conducts fully automated voice interviews using LiveKit, speech-to-text, and LLM orchestration.

Instead of following a predefined script, the interview dynamically adapts to each candidate's resume, previous answers, and information coverage throughout the session.

## Resume-Aware Interviewing

Candidates provide:

* Name
* Email
* Resume (TXT)

The system analyzes the resume and generates personalized interview questions based on:

* Technical skills
* Work experience
* Projects
* Technology stack
* Educational background



## Resume Validation

Before an interview begins, VoiceHire performs resume preflight validation.

Validation includes:

* Resume structure verification
* Email consistency checks
* Resume section detection
* Core content verification

This prevents malformed or unrelated resumes from entering the interview workflow.



## Resume Reuse

VoiceHire supports resume persistence.

If a candidate has previously uploaded a resume and does not want to update it:

* The resume field may be left empty
* Existing resume data will be reused
* Interview initialization proceeds immediately

This significantly improves the experience for repeated interview sessions.



## Dynamic Question Generation

Unlike traditional rule-based or scripted interviews, VoiceHire generates questions dynamically.

Questions are generated using:

* Candidate resume
* Previous answers
* Interview history
* Current interview phase
* Missing coverage areas

This allows the interview to adapt naturally to each candidate.



## Voice-Based Interview Experience

Candidates answer interview questions using voice.

VoiceHire uses:

* LiveKit
* WebRTC
* Speech-to-Text workers

to convert spoken responses into transcripts that can be processed by the backend.



## Multi-Phase Interview Workflow

### Intro Phase

Focuses on:

* Personal introduction
* Education
* Career goals
* Professional background



### Experience Phase

Focuses on:

* Projects
* Work experience
* Technical decisions
* Challenges
* Outcomes
* Business impact



## Intelligent Follow-Up Questions

After each answer:

1. Voice is transcribed
2. Transcript is analyzed
3. Structured evidence is extracted
4. Coverage is updated
5. Interview progress is evaluated
6. The next question is generated

The system determines whether to:

* Continue the current topic
* Explore missing information
* Advance to the next phase
* Complete the interview



## Coverage-Based Interview Control

VoiceHire tracks information coverage throughout the interview.

Examples include:

* What was built?
* Why was it built?
* How was it implemented?
* What challenges occurred?
* What was the outcome?

The interview continues until either:

### Coverage Requirement Satisfied

Enough evidence has been collected for evaluation.

### Maximum Turn Limit Reached

The configured questioning limit has been reached.



## Session Recovery

VoiceHire supports interruption recovery.

If a candidate:

* Refreshes the browser
* Closes the page
* Loses internet connection

the interview state is preserved.

Recovery can be performed through:

* Session ID
* Browser cookie

Candidates can continue from the exact point where the interview stopped.



## Automated Evaluation

After interview completion, VoiceHire generates a structured evaluation report.

The report includes:

### Technical Assessment

Evaluation of:

* Technical depth
* Communication
* Problem solving
* Project ownership

### Strengths

Key positive observations.

### Weaknesses

Areas requiring improvement.

### Recommendations

Actionable suggestions for future growth.

### Hiring Recommendation

Structured signal for hiring decisions.



## Configurable LLM Provider

The architecture is provider-agnostic.

Current implementation:

* Gemini 2.5 Flash

Future support may include:

* OpenAI
* Claude
* Local models
* Other providers

without requiring workflow redesign.


# Standard Interview Lifecycle

A typical interview follows the workflow below.

```text
Candidate Starts Interview
          │
          ▼
Resume Validation
          │
          ▼
Resume Analysis
          │
          ▼
Session Initialization
          │
          ▼
Generate Question
          │
          ▼
Question Readout
          │
          ▼
Candidate Answers
          │
          ▼
Speech Transcription
          │
          ▼
Backend Processing
          │
          ▼
Coverage Evaluation
          │
 ┌────────┴─────────┐
 │                  │
 ▼                  ▼
Coverage Met?    Turn Limit Reached?
 │                  │
 └──────No──────────┘
          │
          ▼
Generate Follow-Up Question
          │
          ▼
Continue Interview
          │
          ▼
Phase Completed
          │
          ▼
Next Phase
          │
          ▼
Final Evaluation
          │
          ▼
Evaluation Report
```



# System Architecture

```text
┌─────────────────────┐
│     React Frontend  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│      LiveKit        │
│ Voice Communication │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    STT Worker       │
│ Speech Recognition  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│      FastAPI        │
│ Workflow Services   │
└───────┬───────┬─────┘
        │       │
        ▼       ▼

┌─────────────┐ ┌─────────────┐
│   Gemini    │ │  Supabase   │
│     LLM     │ │ PostgreSQL  │
└─────────────┘ └─────────────┘
```



# Tech Stack

## Frontend

* React
* TypeScript
* Vite
* Zustand
* LiveKit Client

## Backend

* FastAPI
* Python 3.11+
* Pydantic

## AI

* Gemini 2.5 Flash

## Infrastructure

* Supabase
* PostgreSQL
* LiveKit Cloud



# Project Structure

```text
VoiceHire
│
├── app
│   ├── server
│   ├── web
│
├── packages
│   └── shared
│       └── voicehire-schema.sql
│
└── tests
```  

# Environment Setup

VoiceHire depends on three external services:

- Gemini API
- Supabase
- LiveKit Cloud

## 1. Gemini API

Website: https://ai.google.dev/

Create an API key:

```env
GEMINI_API_KEY=
```

---

## 2. Supabase

Website: https://supabase.com/

Create a project and obtain:

```env
SUPABASE_URL=
SUPABASE_KEY=
```

Initialize the database using:

```text
packages/shared/voicehire-schema.sql
```

---

## 3. LiveKit Cloud

Website: https://cloud.livekit.io/

Create a project and obtain:

```env
LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
```

Example:

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
```

# Running Locally (Development)

VoiceHire supports native local development without Docker.

## Backend

Configure:

```text
app/server/.env.dev
```

Example:

```env
APP_ENV=dev

SUPABASE_URL=
SUPABASE_KEY=

GEMINI_API_KEY=

LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=

LIVEKIT_TRANSCRIBER_AGENT_NAME=voicehire-transcriber

DATABASE_URL=
```

If you switch between local development and Docker deployment,
remember to switch the imported settings module accordingly. 

```python
from app.server.core.config import settings
```

Install dependencies:

```bash
cd app/server
pip install -r requirements.txt
```

Start the backend:

```bash
python -m uvicorn app.server.main:app --reload
```

---

## LiveKit STT Worker

Open another terminal and start the worker:

```bash
python -m app.server.workers.livekit_stt_worker start
```

> **Important**
>
> The LiveKit worker must be started using the `start` subcommand.

---

## Frontend

Configure:

```text
app/web/.env.development
```

Example:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Install dependencies:

```bash
cd app/web
npm install
```

Start the frontend:

```bash
npm run dev
```

The application will be available at:

```text
Frontend:
http://localhost:5173

Backend:
http://localhost:8000
```

---

# Production Deployment (Docker)

Production deployment is designed for cloud servers (e.g. AWS EC2) using Docker Compose.

## Backend

Configure:

```text
app/server/.env.prod
```

Example:

```env
APP_ENV=production

SUPABASE_URL=
SUPABASE_KEY=

GEMINI_API_KEY=

LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=

LIVEKIT_TRANSCRIBER_AGENT_NAME=voicehire-transcriber

VOICEHIRE_API_BASE_URL=http://backend:8000

DATABASE_URL=
```

For Docker deployment, ensure the backend imports:

```python
from app.server.core.config_docker import settings
```

---

## Frontend

Configure:

```text
app/web/.env.production
```

Example:

```env
VITE_API_BASE_URL=/api
```

---

## Build and Start

Build and start all services:

```bash
docker compose build
docker compose up -d
```

Check running services:

```bash
docker compose ps
```

---

# HTTPS Support

VoiceHire provides two Nginx configurations:

```text
app/web/nginx.http.conf
app/web/nginx.https.conf
```

> **Important**
>
> Both files use:
>
> ```nginx
> server_name voicehire.zhichzhang.dev;
> ```
>
> Replace `voicehire.zhichzhang.dev` with **your own domain** before deployment.

### First Deployment

Use the HTTP configuration:

```bash
cp app/web/nginx.http.conf app/web/nginx.conf
```

Build and start the application:

```bash
docker compose build
docker compose up -d
```

Issue a Let's Encrypt certificate:

```bash
docker compose run --rm certbot certonly \
  --webroot \
  -w /var/www/certbot \
  -d <your-domain> \
  --email <your-email> \
  --agree-tos \
  --no-eff-email
```

The HTTP configuration is only required for the initial certificate issuance.
Subsequent deployments can continue using `nginx.https.conf`. After the certificate has been generated successfully, switch to the HTTPS configuration:

```bash
cp app/web/nginx.https.conf app/web/nginx.conf
docker compose up -d --force-recreate web
```

The application will then be available over HTTPS.

---

# Useful Docker Commands

Build images:

```bash
docker compose build
```

Start services:

```bash
docker compose up -d
```

View logs:

```bash
docker compose logs backend --tail=50
docker compose logs worker --tail=50
docker compose logs web --tail=50
```

Check running containers:

```bash
docker compose ps
```

Renew the Let's Encrypt certificate:

```bash
docker compose run --rm certbot renew --webroot -w /var/www/certbot
```


# First-Time Test

1. Open the web application
2. Enter name and email
3. Paste a TXT resume
4. Start interview
5. Allow microphone access
6. Answer generated questions
7. Complete interview
8. View evaluation report



# Current Limitations

## High Token Consumption

Current implementation performs LLM calls for:

* Resume analysis
* Information extraction
* Question generation
* Turn assessment
* Final evaluation

As a result:

* Token usage can be significant
* Long interviews may increase cost
* Latency may increase

Prompt optimization is ongoing.



## Resume Format Support

Currently supported:

```text
TXT
```

Planned:

```text
PDF
DOCX
```

## Frontend Issues

Known issues include:

* Minor UI bugs
* Responsive layout improvements
* Visual polish opportunities

## Potential Edge Cases

Because VoiceHire combines:

* Real-time voice communication
* Speech transcription
* Dynamic LLM orchestration
* Session recovery
* Automated evaluation

there may still be untested edge cases involving:

* Network interruptions
* Long interview sessions
* Large resumes
* Unexpected LLM outputs
* Recovery during in-flight processing 

# License

This project is licensed under the PolyForm Noncommercial License 1.0.0.

See the [LICENSE](LICENSE) file for details.