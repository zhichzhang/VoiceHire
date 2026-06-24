from app.server.interview.sessions.session_initializer import (
    SessionInitializer,
)
from app.server.models.candidate import CandidateProfile
from app.server.models.resume import CandidateResume


SEED_RESUME = {
    "education": [
        {
            "school": "University of Southern California",
            "degree": "Master of Science in Computer Science",
            "expected_graduation": "2027-05",
        }
    ],
    "experience": [
        {
            "company": "Prox Shopping",
            "title": "Software Engineering Intern",
            "start_date": "2026-01",
            "end_date": "2026-03",
            "highlights": [
                "Built deterministic email attribution system",
            ],
        }
    ],
    "skills": {
        "languages": [
            "Python",
            "TypeScript",
        ],
        "backend": [
            "FastAPI",
            "PostgreSQL",
        ],
    },
}


def test_build_resume_context():
    resume = (
        SessionInitializer._build_resume_context(
            SEED_RESUME
        )
    )

    assert isinstance(
        resume,
        CandidateResume,
    )

    assert (
        resume.education[0].institution
        == "University of Southern California"
    )

    assert (
        resume.experiences[0].organization
        == "Prox Shopping"
    )

    assert (
        resume.experiences[0].name
        == "Software Engineering Intern"
    )

    assert "Python" in resume.skills
    assert "FastAPI" in resume.skills


def test_build_initial_profile():
    resume = (
        SessionInitializer._build_resume_context(
            SEED_RESUME
        )
    )

    profile = (
        SessionInitializer._build_initial_profile(
            resume
        )
    )

    assert isinstance(
        profile,
        CandidateProfile,
    )

    assert (
        profile.most_recent_role
        == "Software Engineering Intern at Prox Shopping"
    )

    assert profile.education is not None

    assert (
        profile.education.institution
        == "University of Southern California"
    )

    assert (
        len(profile.domain_keywords)
        > 0
    )

    assert (
        len(profile.highlighted_experiences)
        == 1
    )


def test_profile_contains_bootstrap_context():
    resume = (
        SessionInitializer._build_resume_context(
            SEED_RESUME
        )
    )

    profile = (
        SessionInitializer._build_initial_profile(
            resume
        )
    )

    assert any(
        "Bootstrapped"
        in item
        for item in profile.other_context
    )

    assert any(
        "education entries"
        in item
        for item in profile.other_context
    )

    assert any(
        "experience entries"
        in item
        for item in profile.other_context
    )