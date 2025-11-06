// payments.js
import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm";

/**
 * CONFIG
 * - Works with Supabase if URL/KEY set.
 * - Falls back to mock data if not configured or if queries fail.
 */
const supabaseUrl = window.ENV_SUPABASE_URL || "https://YOUR_SUPABASE_URL";
const supabaseKey = window.ENV_SUPABASE_KEY || "YOUR_SUPABASE_ANON_KEY";
const supabase = createClient(supabaseUrl, supabaseKey);

// If you have auth wired up, we’ll try to use the real user; otherwise use a mock user id.
let CURRENT_USER_ID = null;

// DOM
const requestedList = document.getElementById("requested-list");
const pastList = document.getElementById("past-list");
const requestedEmpty = document.getElementById("requested-empty");
const pastEmpty = document.getElementById("past-empty");
const searchEl = document.getElementById("search");
const groupFilterEl = document.getElementById("group-filter");

// In-memory state
let groupsById = new Map();
let expensesById = new Map();
let allPayments = []; // unified list
let filteredPayments = [];

// ---- Helpers ----

function isMockMode() {
  return !supabaseUrl || supabaseUrl.includes("YOUR_SUPABASE_URL") || supabaseKey.includes("YOUR_SUPABASE_ANON_KEY");
}

function formatMoney(n) {
  const v = Number(n || 0);
  return `$${v.toFixed(2)}`;
}

function fmtDate(s) {
  if (!s) return "";
  const d = new Date(s);
  return d.toLocaleDateString();
}

function render() {
  const q = (searchEl.value || "").trim().toLowerCase();
  const gFilter = groupFilterEl.value || "";

  const match = (p) => {
    const g = groupsById.get(p.group_id)?.name || "";
    const e = expensesById.get(p.expense_id)?.name || p.expense_name || "";
    const hay = `${g} ${e}`.toLowerCase();
    if (gFilter && String(p.group_id) !== gFilter) return false;
    if (q && !hay.includes(q)) return false;
    return true;
  };

  const requested = filteredPayments.filter(p => p.status === "requested" && p.to_user_id === CURRENT_USER_ID && match(p));
  const past = filteredPayments.filter(p => p.status === "paid" && p.from_user_id === CURRENT_USER_ID && match(p));

  requestedList.innerHTML = "";
  pastList.innerHTML = "";

  if (requested.length === 0) {
    requestedEmpty.style.display = "block";
  } else {
    requestedEmpty.style.display = "none";
    requested.forEach(p => requestedList.appendChild(renderPaymentRow(p, true)));
  }

  if (past.length === 0) {
    pastEmpty.style.display = "block";
  } else {
    pastEmpty.style.display = "none";
    past.forEach(p => pastList.appendChild(renderPaymentRow(p, false)));
  }
}

function renderPaymentRow(p, showPayButton) {
  const li = document.createElement("li");
  li.className = "payment";

  const group = groupsById.get(p.group_id);
  const expense = expensesById.get(p.expense_id);

  const title = document.createElement("div");
  title.innerHTML = `
    <div class="who">${expense?.name || p.expense_name || "Expense"} · <span class="chip">${group?.name || "Group"}</span></div>
    <div class="meta">Requested on ${fmtDate(p.created_at)} ${p.paid_at ? `· Paid on ${fmtDate(p.paid_at)}` : ""}</div>
  `;

  const right = document.createElement("div");
  right.style.display = "flex";
  right.style.alignItems = "center";
  right.style.gap = "8px";

  const amt = document.createElement("div");
  amt.className = "amt " + (p.status === "requested" ? "negative" : "positive");
  amt.textContent = formatMoney(p.amount);
  right.appendChild(amt);

  if (showPayButton) {
    const btn = document.createElement("button");
    btn.className = "btn primary";
    btn.textContent = "Mark Paid";
    btn.addEventListener("click", async () => {
      await markPaid(p);
    });
    right.appendChild(btn);
  } else {
    const badge = document.createElement("div");
    badge.className = "chip";
    badge.textContent = "Paid";
    right.appendChild(badge);
  }

  li.appendChild(title);
  li.appendChild(right);
  return li;
}

async function markPaid(p) {
  // Update instantly in UI (optimistic), then try Supabase
  const index = allPayments.findIndex(x => x.id === p.id);
  if (index >= 0) {
    allPayments[index] = { ...allPayments[index], status: "paid", paid_at: new Date().toISOString() };
    filteredPayments = [...allPayments];
    render();
  }

  // If we actually have Supabase configured, persist it
  if (!isMockMode()) {
    const { error } = await supabase.from("payments").update({
      status: "paid",
      paid_at: new Date().toISOString()
    }).eq("id", p.id);
    if (error) {
      console.error("Failed to update payment:", error);
      // Rollback optimistic change on error
      if (index >= 0) {
        allPayments[index] = { ...allPayments[index], status: "requested", paid_at: null };
        filteredPayments = [...allPayments];
        render();
        alert("Couldn’t mark as paid. Try again.");
      }
    }
  }
}

// ---- Data Loading ----

async function getCurrentUserId() {
  if (isMockMode()) return "user_mock_1";

  try {
    const { data: { user }, error } = await supabase.auth.getUser();
    if (error || !user) return "user_mock_1";
    // You might store your app’s user id in user.id or user.user_metadata
    return user.id || "user_mock_1";
  } catch {
    return "user_mock_1";
  }
}

async function loadGroupsAndExpenses() {
  // Try real data; on any failure, fill from mock
  if (!isMockMode()) {
    try {
      const [{ data: groups, error: gErr }, { data: expenses, error: eErr }] = await Promise.all([
        supabase.from("groups").select("id, name"),
        supabase.from("expenses").select("id, name, group_id")
      ]);

      if (!gErr && groups) {
        groupsById = new Map(groups.map(g => [String(g.id), g]));
        // populate group filter
        groupFilterEl.innerHTML = `<option value="">All groups</option>` + groups.map(g => `<option value="${g.id}">${g.name}</option>`).join("");
      }

      if (!eErr && expenses) {
        expensesById = new Map(expenses.map(e => [String(e.id), e]));
      } else {
        // minimal fallback: empty map; row rendering will use p.expense_name
        expensesById = new Map();
      }
      return;
    } catch (err) {
      console.warn("Groups/Expenses fetch failed; using mock", err);
    }
  }

  // Mock fallback
  const mockGroups = [
    { id: "g1", name: "Roomies" },
    { id: "g2", name: "Brunch Crew" }
  ];
  const mockExpenses = [
    { id: "e1", name: "Groceries", group_id: "g1" },
    { id: "e2", name: "Internet", group_id: "g1" },
    { id: "e3", name: "Pancakes", group_id: "g2" }
  ];
  groupsById = new Map(mockGroups.map(g => [g.id, g]));
  expensesById = new Map(mockExpenses.map(e => [e.id, e]));
  groupFilterEl.innerHTML = `<option value="">All groups</option>` + mockGroups.map(g => `<option value="${g.id}">${g.name}</option>`).join("");
}

async function loadPayments() {
  // Try real payments table first
  if (!isMockMode()) {
    try {
      // Expecting a table "payments" with columns:
      // id, group_id, expense_id, from_user_id, to_user_id, amount, status ('requested'|'paid'), created_at, paid_at
      const { data, error } = await supabase
        .from("payments")
        .select("id, group_id, expense_id, from_user_id, to_user_id, amount, status, created_at, paid_at")
        .order("created_at", { ascending: false });

      if (!error && Array.isArray(data)) {
        allPayments = data.map(row => ({
          ...row,
          group_id: String(row.group_id),
          expense_id: String(row.expense_id)
        }));
        filteredPayments = [...allPayments];
        return;
      }
    } catch (err) {
      console.warn("Payments fetch failed; using mock", err);
    }
  }

  // Mock payments derived from expenses/groups
  const now = new Date().toISOString();
  allPayments = [
    {
      id: "p1",
      group_id: "g1",
      expense_id: "e1",
      expense_name: "Groceries",
      from_user_id: CURRENT_USER_ID,       // you are the payer for past payments
      to_user_id: "friend_2",
      amount: 24.50,
      status: "paid",
      created_at: now,
      paid_at: now
    },
    {
      id: "p2",
      group_id: "g1",
      expense_id: "e2",
      expense_name: "Internet",
      from_user_id: "friend_2",
      to_user_id: CURRENT_USER_ID,         // you owe this (requested)
      amount: 30.00,
      status: "requested",
      created_at: now,
      paid_at: null
    },
    {
      id: "p3",
      group_id: "g2",
      expense_id: "e3",
      expense_name: "Pancakes",
      from_user_id: "friend_5",
      to_user_id: CURRENT_USER_ID,         // you owe this (requested)
      amount: 12.75,
      status: "requested",
      created_at: now,
      paid_at: null
    }
  ];
  filteredPayments = [...allPayments];
}

// ---- Init ----

async function init() {
  CURRENT_USER_ID = await getCurrentUserId();
  await loadGroupsAndExpenses();
  await loadPayments();
  render();
}

searchEl?.addEventListener("input", () => {
  filteredPayments = [...allPayments];
  render();
});
groupFilterEl?.addEventListener("change", () => {
  filteredPayments = [...allPayments];
  render();
});

init();
