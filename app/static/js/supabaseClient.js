// Supabase client; session in sessionStorage so it ends when the tab closes
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// Public anon key is intended for client use
const SUPABASE_URL = "https://ntivhddzzdldypdlcoqy.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im50aXZoZGR6emRsZHlwZGxjb3F5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk2MTA4MTgsImV4cCI6MjA3NTE4NjgxOH0.2uyS6DAhbKJi2iXotnKjWygGvO6XQ1YqGWDRsjgErcw";

// Singleton supabase client on window
window.sb = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    storage: window.sessionStorage,
    persistSession: true,
    autoRefreshToken: true,
    storageKey: "sb-es-auth"
  }
});