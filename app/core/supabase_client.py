import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load .env from the project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))

# Get environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Validate
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
