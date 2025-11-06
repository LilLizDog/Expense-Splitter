const form = document.getElementById('login-form');

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.detail || "Login failed");
            return;
        }

        // Store session info in localStorage
        localStorage.setItem('session', JSON.stringify(data));

        alert(data.message);  
        window.location.href = 'dashboard.html';

    } catch (err) {
        console.error(err);
        alert("Login failed. Please try again.");
    }
});
