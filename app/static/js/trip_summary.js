document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("generateSummaryBtn");
    const box = document.getElementById("tripSummaryBox");

    btn.addEventListener("click", async () => {
        const desc = document.getElementById("tripDesc").value.trim();

        if (!desc) {
            box.innerHTML = "<p style='color:red;'>Please enter a trip description.</p>";
            return;
        }

        if (desc.length > 1000) {
            box.innerHTML = "<p style='color:red;'>Description too long (max 1000 characters).</p>";
            return;
        }

        // Disable button while generating
        btn.disabled = true;
        btn.textContent = "Generating…";
        box.innerHTML = "";

        try {
            const response = await fetch("/trip-summary/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ description: desc }),
            });

            if (!response.ok) {
                const err = await response.json();
                box.innerHTML = `<p style="color:red;">${err.detail}</p>`;
                return;
            }

            const data = await response.json();
            box.innerHTML = `<p>${data.summary}</p>`;

        } catch (err) {
            box.innerHTML = `<p style="color:red;">Error: ${err}</p>`;
        } finally {
            btn.disabled = false;
            btn.textContent = "Generate Summary";
        }
    });
});
