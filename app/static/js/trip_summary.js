document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("generateSummaryBtn");
    const box = document.getElementById("tripSummaryBox");

    btn.addEventListener("click", async () => {
        const desc = document.getElementById("tripDesc").value.trim();

        if (!desc) {
            box.innerHTML = "<p style='color:red;'>Please enter a trip description.</p>";
            return;
        }

        box.innerHTML = "Generating summary…";

        try {
            const response = await fetch("/trip-summary/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(desc),
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
        }
    });
});
