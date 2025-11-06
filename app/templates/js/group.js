import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm";

const supabaseUrl = "https://YOUR_SUPABASE_URL";
const supabaseKey = "YOUR_SUPABASE_ANON_KEY";
const supabase = createClient(supabaseUrl, supabaseKey);

const expensesList = document.getElementById("expenses-list");
const createForm = document.getElementById("create-expense-form");
const groupNameEl = document.getElementById("group-name");
const groupDescEl = document.getElementById("group-description");

// Example: Get group_id from URL query
const urlParams = new URLSearchParams(window.location.search);
const groupId = urlParams.get("id");

async function loadGroup() {
  const { data, error } = await supabase.from("groups").select("*").eq("id", groupId).single();
  if (data) {
    groupNameEl.textContent = data.name;
    groupDescEl.textContent = data.description;
  }
}

async function loadExpenses() {
  const { data, error } = await supabase.from("expenses").select("*").eq("group_id", groupId);
  expensesList.innerHTML = "";
  data.forEach(exp => {
    const li = document.createElement("li");
    li.textContent = `${exp.name}: $${exp.amount}`;
    expensesList.appendChild(li);
  });
}

createForm.addEventListener("submit", async e => {
  e.preventDefault();
  const name = document.getElementById("expense-name").value;
  const amount = parseFloat(document.getElementById("expense-amount").value);

  const { data, error } = await supabase.from("expenses").insert([{ group_id: groupId, name, amount }]);
  if (!error) {
    loadExpenses();
    createForm.reset();
  }
});

loadGroup();
loadExpenses();
