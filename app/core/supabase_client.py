import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Optional

# Load .env from the project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))

# Get environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Create Supabase client if possible; if not, warn and set to None so test imports don't fail
if not SUPABASE_URL or not SUPABASE_KEY:
    logging.warning(
        "Missing SUPABASE_URL or SUPABASE_KEY in .env; supabase client will be disabled."
    )
    supabase: Optional[Client] = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
