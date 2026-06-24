from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.server.models.transcribe import (
    TranscriptChunk,
    TranscriptChunkRequest,
    TranscriptionSessionState,
)


class TranscriptCompositionService:
    """
    Utility service for transcript normalization and composition.

    Responsibilities:
    - normalize raw transcript text
    - dedupe consecutive repeated final chunks
    - compose final_text / parsed_text for UI
    - append incoming chunks with lightweight deduplication
    """

    @staticmethod
    def normalize_text(text: str | None) -> str:
        return " ".join((text or "").split()).strip()

    @staticmethod
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def append_chunk(
        session: TranscriptionSessionState,
        payload: TranscriptChunkRequest,
    ) -> bool:
        """
        Append a chunk to the session unless it is a consecutive duplicate.

        Returns:
            True if a new chunk was appended.
            False if the chunk was treated as a duplicate and skipped.
        """
        normalized_text = TranscriptCompositionService.normalize_text(
            payload.text
        )
        last_chunk = session.chunks[-1] if session.chunks else None

        if (
            last_chunk is not None
            and last_chunk.is_final == payload.is_final
            and TranscriptCompositionService.normalize_text(last_chunk.text)
            == normalized_text
        ):
            session.latest_text = normalized_text
            session.latest_is_final = payload.is_final
            session.updated_at = TranscriptCompositionService.utc_now_iso()
            return False

        chunk = TranscriptChunk(
            chunk_id=str(uuid4()),
            text=payload.text,
            is_final=payload.is_final,
            created_at=TranscriptCompositionService.utc_now_iso(),
        )

        session.chunks.append(chunk)
        session.latest_text = payload.text
        session.latest_is_final = payload.is_final
        session.updated_at = TranscriptCompositionService.utc_now_iso()

        return True

    @staticmethod
    def compose_parsed_text(
        session: TranscriptionSessionState,
    ) -> tuple[str, str]:
        """
        Build:
        - final_text: all finalized utterances joined together, deduped
        - parsed_text: final_text + current interim if the current one is not final
        """
        final_parts: list[str] = []
        previous_final: str | None = None

        for chunk in session.chunks:
            if not chunk.is_final:
                continue

            normalized = TranscriptCompositionService.normalize_text(
                chunk.text
            )
            if not normalized:
                continue

            if normalized == previous_final:
                continue

            final_parts.append(normalized)
            previous_final = normalized

        final_text = " ".join(final_parts).strip()

        latest_text = TranscriptCompositionService.normalize_text(
            session.latest_text
        )

        if (
            latest_text
            and not session.latest_is_final
            and latest_text != final_text
            and latest_text not in final_text
        ):
            parsed_text = " ".join(
                part for part in [final_text, latest_text] if part
            ).strip()
        else:
            parsed_text = final_text

        return final_text, parsed_text