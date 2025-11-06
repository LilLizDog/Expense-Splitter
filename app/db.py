# app/db.py
from supabase import create_client, Client
import os

# Load Supabase credentials from environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase credentials not set. Please set SUPABASE_URL and SUPABASE_KEY in your environment.")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
