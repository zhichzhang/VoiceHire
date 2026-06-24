from __future__ import annotations

import json

from app.server.core.supabase_client import supabase_client

CANDIDATE_ID = "e6c1d9e0-1111-4444-8888-aaaaaaaaaaaa"
EMAIL = "zzhang32@usc.edu"
NAME = "Zhicheng Zhang"

# 如果你的 candidate_resumes.resume_json 是 json/jsonb，保留 False。
# 如果你的欄位還是 text，改成 True。
STORE_RESUME_AS_TEXT = False

resume_json = {
    "name": "Zhicheng Zhang",
    "location": "Los Angeles, CA",
    "education": [
        {
            "school": "University of Southern California",
            "degree": "Master of Science in Computer Science",
            "gpa": "3.683/4.0",
            "expected_graduation": "2027-05",
        },
        {
            "school": "China University of Mining and Technology",
            "degree": "Bachelor of Engineering in Electronic Information Science and Technology",
            "gpa": "88/100",
            "honors": ["Top 5%"],
            "graduation_date": "2021-06",
        },
    ],
    "experience": [
        {
            "company": "Prox Shopping",
            "title": "Software Engineering Intern",
            "location": "Santa Monica, CA",
            "start_date": "2026-01",
            "end_date": "2026-03",
            "highlights": [
                "Engineered a ChatGPT Vision-powered ingestion pipeline to extract schema-validated structured data from semi-structured inputs.",
                "Developed an ingestion-time product resolution service with deterministic, failure-isolated resolution logic.",
                "Designed a deterministic email attribution system backed by PostgreSQL and FastAPI.",
                "Architected first-party open and click tracking APIs with Redis-backed caching.",
                "Built a typed observability framework with asynchronous multi-transport telemetry.",
            ],
        },
        {
            "company": "Fogsight",
            "title": "Software Engineering Intern",
            "location": "Shenzhen, China",
            "start_date": "2025-05",
            "end_date": "2025-08",
            "highlights": [
                "Launched a production-ready online AI animation platform powered by LLMs.",
                "Packaged the application into a containerized service with Docker.",
                "Designed a normalized IndexedDB schema for persistent client-side conversation storage.",
            ],
        },
    ],
    "projects": [
        {
            "name": "AI Bistro Ordering",
            "technologies": [
                "TypeScript",
                "Node.js",
                "Express.js",
                "PostgreSQL",
                "Prisma",
                "GCP",
                "Gemini API",
            ],
            "highlights": [
                "Architected a multi-stage AI ordering orchestration pipeline.",
                "Designed a semantic cart state management system.",
                "Built a typed service-repository backend architecture.",
            ],
        },
        {
            "name": "DealFlow",
            "technologies": [
                "TypeScript",
                "Node.js",
                "PostgreSQL",
                "Apache Kafka",
                "Redis",
                "AWS",
                "Docker",
            ],
            "highlights": [
                "Architected an event-driven ingestion and email delivery pipeline.",
                "Designed a Redis-backed deduplication layer.",
                "Improved overall system throughput by 40%.",
            ],
        },
    ],
    "publication": [
        {
            "title": "Generation method of class integration test order based on deep reinforcement learning",
            "year": 2023,
        }
    ],
    "skills": {
        "languages": ["Python", "TypeScript", "Java", "C++"],
        "backend": ["Node.js", "Express.js", "FastAPI", "Prisma"],
        "data_and_messaging": ["PostgreSQL", "MongoDB", "MySQL", "Kafka", "Redis"],
        "ai_systems": ["Agent Systems", "RAG", "Function Calling"],
        "machine_learning": ["PyTorch", "Sklearn", "Pandas", "NumPy", "DRL"],
        "observability": ["Prometheus", "Grafana", "Telemetry Systems"],
        "infrastructure": ["GCP", "AWS", "Docker", "Kubernetes"],
        "testing": ["Pytest", "Vitest", "Supertest", "Postman"],
    },
}


def main() -> None:
    candidate_result = (
        supabase_client.table("candidates")
        .upsert(
            {
                "id": CANDIDATE_ID,
                "email": EMAIL,
                "name": NAME,
            },
            on_conflict="email",
        )
        .execute()
    )

    resume_payload = (
        json.dumps(resume_json, ensure_ascii=False)
        if STORE_RESUME_AS_TEXT
        else resume_json
    )

    resume_result = (
        supabase_client.table("candidate_resumes")
        .upsert(
            {
                "candidate_id": CANDIDATE_ID,
                "resume_json": resume_payload,
            },
            on_conflict="candidate_id",
        )
        .execute()
    )

    print("Candidate upserted:", candidate_result.data)
    print("Resume upserted:", resume_result.data)
    print("Candidate ID:", CANDIDATE_ID)


if __name__ == "__main__":
    main()