# VoiceHire

An AI-powered voice interview platform that conducts structured technical interviews, dynamically generates follow-up questions, evaluates candidate responses, and produces detailed hiring reports.

VoiceHire combines real-time speech transcription, resume-aware interview generation, dynamic LLM orchestration, session recovery, and automated candidate evaluation into a single end-to-end interview workflow.



## Demo Video

Watch the complete demo here:

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

This prevents invalid or unrelated content from entering the interview workflow.



## Resume Reuse

VoiceHire supports resume persistence.

If a candidate has already uploaded a resume and does not want to update it:

* The resume field may be left empty
* Existing resume data will be reused
* Interview initialization proceeds immediately

This significantly improves the experience for repeated interview sessions.



## Dynamic Question Generation

Unlike traditional scripted interviews, VoiceHire generates questions dynamically.

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

VoiceHire depends on three external services.

* Gemini API
* Supabase
* LiveKit Cloud



## 1. Gemini API

Website: https://ai.google.dev/

Create an API key and add:

```env
GEMINI_API_KEY=
```



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

Open:

```text
Supabase Dashboard
→ SQL Editor
→ New Query
→ Paste voicehire-schema.sql
→ Run
```



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



# Backend Environment Variables

Create:

```text
app/server/.env.dev
```

Example:

```env
APP_ENV=dev

GEMINI_API_KEY=

SUPABASE_URL=
SUPABASE_KEY=

LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=

LIVEKIT_TRANSCRIBER_AGENT_NAME=voicehire-transcriber
```

# Frontend Environment Variables

Create:

```text
app/web/.env.development
```

Example:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```



# Installation

## Backend

```bash
cd app/server

pip install -r requirements.txt
```

## Frontend

```bash
cd app/web

npm install
```



# Running Locally

Three processes must be started.



## Start Backend

From project root:

```bash
python -m uvicorn app.server.main:app --reload
```



## Start LiveKit STT Worker

Open another terminal:

```bash
python -m app.server.workers.livekit_stt_worker start
```



## Start Frontend

```bash
cd app/web

npm run dev
```



# Access Application

Frontend:

```text
http://localhost:5173
```

Backend:

```text
http://localhost:8000
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



## Codebase Cleanup

Current priorities focus on functionality.

Areas still being improved:

* Refactoring
* Documentation
* Testing coverage
* Component organization



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



# Future Roadmap

* OpenAI support
* Claude support
* PDF resume support
* DOCX resume support
* Interview template customization
* Recruiter dashboard
* Candidate history tracking
* Multi-language interviews
* Better analytics
* Docker deployment
* CI/CD pipelines
* Production deployment



# License

This project is provided for educational, research, portfolio, and demonstration purposes only.

Commercial use, redistribution, sublicensing, and production deployment are not currently permitted without explicit permission from the author.

Copyright (c) 2026 Zhicheng Zhang. All rights reserved.