// FILE: group.js
import { supabase } from './supabaseClient.js';

document.addEventListener("DOMContentLoaded", async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const groupId = urlParams.get("group_id");

  if (!groupId) {
    alert("No group selected.");
    window.location.href = "/groups.html";
    return;
  }

  const groupNameEl = document.getElementById("group-name");
  const groupDescEl = document.getElementById("group-desc");
  const groupDateEl = document.getElementById("group-date");
  const membersListEl = document.getElementById("members-list"); // Add this div in HTML
  const txListEl = document.getElementById("tx-list");
  const addMemberBtn = document.getElementById("add-member-btn");
  const addExpenseBtn = document.querySelector('a[href^="/add_expense.html"]');

  // ---------------------------
  // Load Group Info
  // ---------------------------
  async function loadGroup() {
    const { data, error } = await supabase
      .from("groups")
      .select("*")
      .eq("id", groupId)
      .single();

    if (error || !data) {
      alert("Failed to load group info");
      console.error(error);
      return;
    }

    groupNameEl.textContent = data.name;
    groupDescEl.textContent = data.description || "";
    groupDateEl.textContent = new Date(data.created_at).toLocaleDateString();
  }

  // ---------------------------
  // Load Members
  // ---------------------------
  async function loadMembers() {
    const { data: group, error: groupError } = await supabase
      .from("groups")
      .select("members")
      .eq("id", groupId)
      .single();

    if (groupError || !group) {
      console.error(groupError);
      membersListEl.innerHTML = "<div class='muted'>Failed to load members.</div>";
      return;
    }

    const memberIds = group.members || [];
    if (memberIds.length === 0) {
      membersListEl.innerHTML = "<div class='muted'>No members yet.</div>";
      return;
    }

    const { data: users, error: usersError } = await supabase
      .from("users")
      .select("id, name, email")
      .in("id", memberIds);

    if (usersError) {
      console.error(usersError);
      membersListEl.innerHTML = "<div class='muted'>Failed to load members.</div>";
      return;
    }

    membersListEl.innerHTML = "";
    users.forEach(u => {
      const p = document.createElement("p");
      p.textContent = u.name || u.email;
      membersListEl.appendChild(p);
    });
  }

  // ---------------------------
  // Load Expenses
  // ---------------------------
  async function loadExpenses() {
    const { data: expenses, error } = await supabase
      .from("transactions")
      .select("*")
      .eq("group_id", groupId)
      .order("created_at", { ascending: false })
      .limit(10);

    if (error) {
      console.error(error);
      txListEl.innerHTML = "<div class='muted'>Failed to load transactions.</div>";
      return;
    }

    if (!expenses || expenses.length === 0) {
      txListEl.innerHTML = "<div class='muted'>No transactions yet.</div>";
      return;
    }

    txListEl.innerHTML = "";
    expenses.forEach(t => {
      const div = document.createElement("div");
      div.className = "tx";
      const signClass = t.amount >= 0 ? "positive" : "negative";
      div.innerHTML = `
        <div class="left">
          <div class="name">${t.name}</div>
          <div class="meta">${new Date(t.created_at).toLocaleDateString()}</div>
          <div class="meta">Paid by: ${t.paid_by}</div>
        </div>
        <div class="amt ${signClass}">${t.amount >= 0 ? "+" : "-"}$${Math.abs(t.amount).toFixed(2)}</div>
      `;
      txListEl.appendChild(div);
    });
  }

  // ---------------------------
  // Add Expense button
  // ---------------------------
  addExpenseBtn.addEventListener("click", e => {
    e.preventDefault();
    window.location.href = `/add_expense.html?group_id=${groupId}`;
  });

  // ---------------------------
  // Add Member button
  // ---------------------------
  addMemberBtn.addEventListener("click", async () => {
    const memberEmail = prompt("Enter member email to add:");
    if (!memberEmail) return;

    const { data: userData, error: userError } = await supabase
      .from("users")
      .select("id")
      .eq("email", memberEmail)
      .single();

    if (!userData || userError) {
      alert("User not found");
      return;
    }

    const { data: group, error: groupError } = await supabase
      .from("groups")
      .select("members")
      .eq("id", groupId)
      .single();

    if (groupError) {
      alert("Failed to fetch group");
      return;
    }

    const updatedMembers = Array.from(new Set([...(group.members || []), userData.id]));

    const { error: updateError } = await supabase
      .from("groups")
      .update({ members: updatedMembers })
      .eq("id", groupId);

    if (updateError) {
      alert("Failed to add member");
    } else {
      alert("Member added!");
      loadMembers(); // refresh member list
    }
  });

  // ---------------------------
  // Initial load
  // ---------------------------
  await loadGroup();
  await loadMembers();
  await loadExpenses();
});
