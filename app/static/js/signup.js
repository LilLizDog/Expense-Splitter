const form = document.getElementById('signup-form');

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const dob = document.getElementById('dob').value;

    try {
        const response = await fetch('/auth/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password, dob })
        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.detail || "Signup failed");
            return;
        }

        alert(data.message);  
        window.location.href = 'login.html';

    } catch (err) {
        console.error(err);
        alert("Signup failed. Please try again.");
    }
});
