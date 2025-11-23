document.addEventListener("DOMContentLoaded", () => {
  loadPayments();
});

// Backend base URL (adjust if needed)
const API_BASE = "/api/payments";

// Fetch all payments
async function loadPayments() {
  try {
    const res = await fetch(`${API_BASE}`, { credentials: "include" });
    if (!res.ok) throw new Error("Failed to fetch payments");

    const payments = await res.json();

    // Split into outstanding (requested) and past (paid)
    const outstanding = payments.filter(p => p.status === "requested" && p.to_user_id === CURRENT_USER_ID);
    const past = payments.filter(p => p.status === "paid" && (p.to_user_id === CURRENT_USER_ID || p.from_user_id === CURRENT_USER_ID));

    renderPayments("outstanding-payments", outstanding, false);
    renderPayments("past-payments", past, true);

  } catch (err) {
    console.error(err);
    document.getElementById("outstanding-payments").innerHTML = "<p>Error loading payments.</p>";
    document.getElementById("past-payments").innerHTML = "<p>Error loading payments.</p>";
  }
}

// Render payments into a container
function renderPayments(containerId, payments, isPast) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";

  if (payments.length === 0) {
    container.innerHTML = "<p>No payments here.</p>";
    return;
  }

  payments.forEach(p => {
    const div = document.createElement("div");
    div.classList.add("payment-item");
    div.style.border = "1px solid #ddd";
    div.style.padding = "10px";
    div.style.marginBottom = "8px";
    div.style.borderRadius = "8px";

    div.innerHTML = `
      <p><strong>Expense:</strong> ${p.expense_name || "N/A"}</p>
      <p><strong>From:</strong> ${p.from_user_id}</p>
      <p><strong>To:</strong> ${p.to_user_id}</p>
      <p><strong>Amount:</strong> $${p.amount.toFixed(2)}</p>
      <p><strong>Requested On:</strong> ${p.created_at ? new Date(p.created_at).toLocaleDateString() : "-"}</p>
      ${isPast ? `<p><strong>Paid On:</strong> ${p.paid_at ? new Date(p.paid_at).toLocaleDateString() : "-"}</p>` : ""}
    `;

    if (!isPast) {
      const btn = document.createElement("button");
      btn.textContent = "Mark as Paid";
      btn.style.marginTop = "6px";
      btn.classList.add("btn", "primary");
      btn.onclick = () => markAsPaid(p.id);
      div.appendChild(btn);
    }

    container.appendChild(div);
  });
}

// Call backend to mark a payment as paid
async function markAsPaid(paymentId) {
  try {
    const res = await fetch(`${API_BASE}/${paymentId}/pay`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ paid_via: "Cash" }), // optional, can be dynamic
      credentials: "include"
    });

    if (!res.ok) throw new Error("Failed to mark as paid");

    // Refresh the lists
    loadPayments();

  } catch (err) {
    console.error(err);
    alert("Could not mark payment as paid. Try again.");
  }
}

// Optional: mock CURRENT_USER_ID if not set by your backend
const CURRENT_USER_ID = window.CURRENT_USER_ID || "user_mock_1";
