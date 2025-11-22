# app/core/supabase_client.py
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load .env for local development
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))

_supabase: Client = None

def get_supabase() -> Client:
    """Return the Supabase client, creating it if necessary."""
    global _supabase
    if _supabase is None:
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError(
                "Missing SUPABASE_URL or SUPABASE_KEY in environment"
            )
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase
