from supabase import create_client, Client
from .config import settings

# Prefer the service role key if available, fallback to anon key
_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
supabase: Client = create_client(settings.SUPABASE_URL, _key)
