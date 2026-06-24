# app/server/core/supabase_client.py

from functools import lru_cache
from traceback import format_exc

from supabase import Client, create_client

from app.server.core.config import settings
from app.server.core.logger import logger


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    logger.info(
        "Creating Supabase client"
    )

    try:
        client = create_client(
            settings.supabase_url,
            settings.supabase_key,
        )

        logger.success(
            "Supabase client created"
        )

        return client

    except Exception as exc:
        logger.error(
            f"Failed to create Supabase client: "
            f"{type(exc).__name__}: {exc}"
        )

        logger.error(
            format_exc()
        )

        raise


class _SupabaseClientProxy:
    def __getattr__(self, name: str):
        return getattr(
            get_supabase_client(),
            name,
        )


supabase_client = _SupabaseClientProxy()