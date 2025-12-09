// /static/js/dashboard.js
// import { supabase } from "/static/js/supabaseClient.js";

const mockPayload = {
  user_name: "Preet (mock)",
  wallet: { owed: 25.5, owing: 27.85 },
  groups: [
    { id: "1", name: "Roommates" },
    { id: "2", name: "CS3300 Team" },
  ],
  recent_transactions: [
    {
      name: "Pizza Night",
      amount: 18.25,
      sign: "-",
      date: "2025-10-29",
      group_name: "Roommates",
    },
    {
      name: "Uber to AWM",
      amount: 9.6,
      sign: "-",
      date: "2025-10-28",
      group_name: "AWM",
    },
  ],
};

function formatMoney(n) {
  return "$" + (Number(n) || 0).toFixed(2);
}

export async function initDashboard(config) {
  const {
    mockMode,
    dashboardUrl,
    elements: {
      welcomeHeading,
      walletOwed,
      walletOwing,
      walletEmpty,
      recentContainer,
      recentEmpty,
      groupsContainer,
      groupsEmpty,
    },
  } = config;

  let data;

  if (mockMode) {
    data = mockPayload;
  } else {
    const res = await fetch(dashboardUrl, { credentials: "include" });
    if (!res.ok) {
      console.error("Failed to load dashboard data", res.status);
      data = mockPayload;
    } else {
      data = await res.json();
    }
  }

  // Welcome
  if (welcomeHeading) {
    const name = data && data.user_name ? data.user_name : "Friend";
    welcomeHeading.textContent = `Welcome ${name}!`;
  }

  // Wallet
  const owed = data.wallet?.owed || 0;
  const owing = data.wallet?.owing || 0;

  if (walletOwed) walletOwed.textContent = formatMoney(owed);
  if (walletOwing) walletOwing.textContent = formatMoney(owing);

  if (walletEmpty) {
    const hasAnyBalance = owed !== 0 || owing !== 0;
    walletEmpty.style.display = hasAnyBalance ? "none" : "block";
  }

  // Recent transactions
  recentContainer.innerHTML = "";
  const txs = data.recent_transactions || [];
  if (txs.length === 0) {
    if (recentEmpty) recentEmpty.style.display = "block";
  } else {
    if (recentEmpty) recentEmpty.style.display = "none";
    txs.forEach((tx) => {
      const wrapper = document.createElement("div");
      wrapper.className = "tx";

      const left = document.createElement("div");
      left.className = "left";

      const name = document.createElement("div");
      name.className = "name";
      name.textContent = tx.name;

      const meta = document.createElement("div");
      meta.className = "meta";
      meta.textContent = `${tx.date} • ${tx.group_name || ""}`;

      left.appendChild(name);
      left.appendChild(meta);

      const amt = document.createElement("div");
      const sign = tx.sign === "+" ? "positive" : "negative";
      amt.className = `amt ${sign}`;
      const numeric = Number(tx.amount) || 0;
      const prefix = tx.sign === "+" ? "+" : "-";
      amt.textContent = `${prefix}${formatMoney(Math.abs(numeric))}`;

      wrapper.appendChild(left);
      wrapper.appendChild(amt);
      recentContainer.appendChild(wrapper);
    });
  }

  // Groups
  groupsContainer.innerHTML = "";
  const groups = data.groups || [];
  if (groups.length === 0) {
    if (groupsEmpty) groupsEmpty.style.display = "block";
  } else {
    if (groupsEmpty) groupsEmpty.style.display = "none";
    groups.forEach((g) => {
      const li = document.createElement("li");
      const link = document.createElement("a");

      // Go to group page using query param
      link.href = `/group?group_id=${encodeURIComponent(g.id)}`;
      link.textContent = g.name;

      li.appendChild(link);
      groupsContainer.appendChild(li);
    });
  }
}
