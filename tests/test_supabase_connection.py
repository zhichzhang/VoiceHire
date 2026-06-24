from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import sys as _sys
from supabase import create_client
import supabase
from app.server.core.logger import logger

logger.debug(f"sys.executable = {_sys.executable}")
logger.debug(f"supabase.__file__ = {supabase.__file__}")
logger.debug(f"supabase.__version__ = {supabase.__version__}")

SUPABASE_URL = "https://kcrfndojrgzcelubeyok.supabase.co"
SUPABASE_KEY = "sb_publishable_kNc6taDdgc5u3dzASaoSlQ_mXlsotNa"

print("Creating client...")

client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)

print("Client created.")

print("Testing connection...")

response = (
    client
    .table("candidates")
    .select("*")
    .limit(1)
    .execute()
)

print("SUCCESS")
print(response.data)
print(repr(SUPABASE_KEY))
print(len(SUPABASE_KEY))
print(hash(SUPABASE_KEY))