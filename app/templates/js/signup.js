import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm'

const supabaseUrl = 'https://ntivhddzzdldypdlcoqy.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im50aXZoZGR6emRsZHlwZGxjb3F5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk2MTA4MTgsImV4cCI6MjA3NTE4NjgxOH0.2uyS6DAhbKJi2iXotnKjWygGvO6XQ1YqGWDRsjgErcw'

const supabase = createClient(supabaseUrl, supabaseAnonKey)
const form = document.getElementById('signup-form')

form.addEventListener('submit', async (e) => {
  e.preventDefault()

  const name = document.getElementById('name').value
  const email = document.getElementById('email').value
  const password = document.getElementById('password').value
  const dob = document.getElementById('dob').value

  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: { name, dob }
    }
  })

  if (error) {
    alert(error.message)
  } else {
    alert('Signup successful! Redirecting to login page...')
    window.location.href = 'login.html'
  }
})
