import { supabase } from './supabaseClient.js';

const createForm = document.getElementById("create-group-form");
const groupsList = document.getElementById("groups-list");

async function getUser() {
  const { data } = await supabase.auth.getUser();
  return data.user;
}

async function fetchGroups() {
  const user = await getUser();
  if (!user) {
    groupsList.innerHTML = '<div class="muted">You must log in.</div>';
    return;
  }

  const { data, error } = await supabase
    .from("groups")
    .select("*")
    .contains("members", [user.id])
    .order("created_at", { ascending: false });

  if (error) {
    groupsList.innerHTML = "Error loading groups";
    console.error(error);
    return;
  }

  if (!data.length) {
    groupsList.innerHTML = '<div class="muted">You are not part of any groups.</div>';
    return;
  }

  groupsList.innerHTML = "";
  data.forEach(group => {
    const div = document.createElement("div");
    div.classList.add("tx");
    div.innerHTML = `
      <div class="left">
        <a href="/group.html?group_id=${group.id}" class="name">${group.name}</a>
        <div class="meta">${group.description || ""}</div>
        <div class="meta">Created: ${new Date(group.created_at).toLocaleDateString()}</div>
      </div>
      <button class="btn add-member" data-id="${group.id}">Add Member</button>
    `;
    groupsList.appendChild(div);
  });

  document.querySelectorAll('.add-member').forEach(btn => {
    btn.addEventListener('click', async () => {
      const email = prompt("Enter email of member to add:");
      if (!email) return;
      const { data: user } = await supabase.from('users').select('id').eq('email', email).single();
      if (!user) return alert("User not found");

      const { data: group } = await supabase.from('groups').select('members').eq('id', btn.dataset.id).single();
      const updated = [...new Set([...group.members, user.id])];
      await supabase.from('groups').update({ members: updated }).eq('id', btn.dataset.id);
      alert("Member added!");
    });
  });
}

createForm.addEventListener("submit", async e => {
  e.preventDefault();
  const name = document.getElementById("group-name").value.trim();
  const desc = document.getElementById("group-desc").value.trim();
  const emails = document.getElementById("group-members").value.split(',').map(e => e.trim()).filter(Boolean);

  const user = await getUser();
  const members = [user.id];

  for (const email of emails) {
    const { data } = await supabase.from('users').select('id').eq('email', email).single();
    if (data) members.push(data.id);
  }

  const { error } = await supabase.from('groups').insert([{ name, description: desc, members, created_at: new Date().toISOString() }]);
  if (error) return alert("Error creating group");
  createForm.reset();
  fetchGroups();
});

fetchGroups();
