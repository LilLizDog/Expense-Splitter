document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("generate-summary-btn");
    const box = document.getElementById("trip-summary-output");
    const output = document.getElementById("trip-summary-text");

    btn.addEventListener("click", async () => {
        const desc = document.getElementById("trip-description").value.trim();

        if (!desc) {
            output.textContent = "Please enter a trip description.";
            output.style.color = "red";
            box.style.display = "block";
            return;
        }

        if (desc.length > 1000) {
            output.textContent = "Description too long (max 1000 characters).";
            output.style.color = "red";
            box.style.display = "block";
            return;
        }

        btn.disabled = true;
        btn.textContent = "Generating…";
        output.textContent = "";
        box.style.display = "block";

        try {
            const response = await fetch("/trip-summary/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ description: desc }),
            });

            if (!response.ok) {
                const err = await response.json();
                output.textContent = err.detail || "Error generating summary.";
                output.style.color = "red";
                return;
            }

            const data = await response.json();
            output.textContent = data.summary;
            output.style.color = "black";

        } catch (err) {
            output.textContent = `Error: ${err}`;
            output.style.color = "red";
        } finally {
            btn.disabled = false;
            btn.textContent = "Generate Summary";
        }
    });
});
