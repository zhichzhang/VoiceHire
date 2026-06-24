# app/server/interview/experience_selectors.py

from app.server.models.candidate import (
    CandidateProfile,
)


class ExperienceSelector:
    """
    Selects the most appropriate experience
    for the experience phase.
    """

    async def select(
        self,
        profile: CandidateProfile,
    ):

        if profile.highlighted_experiences:
            return profile.highlighted_experiences[0]

        return None