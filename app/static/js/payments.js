// payments.js

const requestedList = document.getElementById("requested-list");
const pastList = document.getElementById("past-list");
const requestedEmpty = document.getElementById("requested-empty");
const pastEmpty = document.getElementById("past-empty");
const searchEl = document.getElementById("search");

let CURRENT_USER_ID = null;
let allPayments = [];

async function getCurrentUserId() {
  try {
    const resp = await fetch("/api/payments");
    const data = await resp.json();
    if (data.length) {
      CURRENT_USER_ID = data[0].to_user_id; // fallback if mock
    } else {
      CURRENT_USER_ID = "user_mock_1";
    }
  } catch {
    CURRENT_USER_ID = "user_mock_1";
  }
  return CURRENT_USER_ID;
}

function formatMoney(n) {
  return `$${Number(n || 0).toFixed(2)}`;
}

function fmtDate(s) {
  if (!s) return "";
  return new Date(s).toLocaleDateString();
}

async function loadPayments() {
  const resp = await fetch("/api/payments");
  const data = await resp.json();
  allPayments = data;
  render();
}

function render() {
  const q = (searchEl.value || "").toLowerCase();

  const requested = allPayments.filter(p =>
    p.status === "requested" &&
    p.to_user_id === CURRENT_USER_ID &&
    (`${p.expense_name || ""}`.toLowerCase().includes(q))
  );

  const past = allPayments.filter(p =>
    p.status === "paid" &&
    (p.from_user_id === CURRENT_USER_ID || p.to_user_id === CURRENT_USER_ID) &&
    (`${p.expense_name || ""}`.toLowerCase().includes(q))
  );

  requestedList.innerHTML = "";
  pastList.innerHTML = "";

  if (requested.length === 0) requestedEmpty.style.display = "block";
  else {
    requestedEmpty.style.display = "none";
    requested.forEach(p => requestedList.appendChild(renderPaymentRow(p, true)));
  }

  if (past.length === 0) pastEmpty.style.display = "block";
  else {
    pastEmpty.style.display = "none";
    past.forEach(p => pastList.appendChild(renderPaymentRow(p, false)));
  }
}

function renderPaymentRow(p, allowPay) {
  const li = document.createElement("li");
  li.className = "payment";

  const title = document.createElement("div");
  title.innerHTML = `<div class="who">${p.expense_name || "Expense"}</div>
                     <div class="meta">Requested on ${fmtDate(p.created_at)}${p.paid_at ? ` · Paid on ${fmtDate(p.paid_at)}` : ""}</div>`;

  const right = document.createElement("div");
  right.style.display = "flex";
  right.style.alignItems = "center";
  right.style.gap = "8px";

  const amt = document.createElement("div");
  amt.className = "amt " + (p.status === "requested" ? "negative" : "positive");
  amt.textContent = formatMoney(p.amount);
  right.appendChild(amt);

  if (allowPay) {
    const btn = document.createElement("button");
    btn.className = "btn primary";
    btn.textContent = "Mark as Paid";
    btn.addEventListener("click", async () => {
      await markPaid(p.id);
    });
    right.appendChild(btn);
  }

  li.appendChild(title);
  li.appendChild(right);
  return li;
}

async function markPaid(paymentId) {
  const resp = await fetch(`/api/payments/${paymentId}/pay`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ paid_via: "Cash" }),
  });
  if (resp.ok) {
    await loadPayments();
  } else {
    alert("Failed to mark payment as paid");
  }
}

searchEl.addEventListener("input", render);

(async () => {
  await getCurrentUserId();
  await loadPayments();
})();
