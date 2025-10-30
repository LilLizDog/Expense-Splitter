import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm'

const supabaseUrl = 'https://ntivhddzzdldypdlcoqy.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im50aXZoZGR6emRsZHlwZGxjb3F5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk2MTA4MTgsImV4cCI6MjA3NTE4NjgxOH0.2uyS6DAhbKJi2iXotnKjWygGvO6XQ1YqGWDRsjgErcw'

const supabase = createClient(supabaseUrl, supabaseAnonKey)
const form = document.getElementById('login-form')

form.addEventListener('submit', async (e) => {
  e.preventDefault()

  const email = document.getElementById('email').value
  const password = document.getElementById('password').value

  const { data, error } = await supabase.auth.signInWithPassword({ email, password })

  if (error) {
    alert(error.message)
  } else {
    localStorage.setItem('session', JSON.stringify(data.session))
    alert('Login successful!')
    window.location.href = 'home.html'
  }
})
