// FILE: groups.js
import { supabase } from './supabaseClient.js';

const groupsList = document.getElementById('groups-list');
const createForm = document.getElementById('create-group-form');

// ----------------------------
// Fetch and display groups
// ----------------------------
async function fetchGroups() {
  const currentUser = supabase.auth.user();
  if (!currentUser) return;

  const { data: groups, error } = await supabase
    .from('groups')
    .select('*')
    .contains('members', [currentUser.id])
    .order('created_at', { ascending: false });

  if (error) {
    groupsList.innerHTML = 'Error loading groups';
    console.error(error);
    return;
  }

  if (!groups || groups.length === 0) {
    groupsList.innerHTML = '<div class="muted">You are not part of any groups.</div>';
    return;
  }

  groupsList.innerHTML = '';
  groups.forEach(group => {
    const div = document.createElement('div');
    div.classList.add('tx');
    div.innerHTML = `
      <div class="left">
        <a href="group.html?group_id=${group.id}" class="name">${group.name}</a>
        <div class="meta">${group.description || ''}</div>
        <div class="meta">Created: ${new Date(group.created_at).toLocaleDateString()}</div>
      </div>
      <button class="btn add-member" data-id="${group.id}">Add Member</button>
    `;
    groupsList.appendChild(div);
  });

  // Attach Add Member handlers
  document.querySelectorAll('.add-member').forEach(btn => {
    btn.addEventListener('click', async () => {
      const memberEmail = prompt('Enter member email to add:');
      if (!memberEmail) return;

      // Fetch the user ID from email
      const { data: userData, error: userError } = await supabase
        .from('users')
        .select('id')
        .eq('email', memberEmail)
        .single();

      if (!userData || userError) {
        alert('User not found');
        return;
      }

      const groupId = btn.dataset.id;

      // Get current members
      const { data: group, error: groupError } = await supabase
        .from('groups')
        .select('members')
        .eq('id', groupId)
        .single();

      if (groupError) {
        alert('Error fetching group members');
        return;
      }

      const updatedMembers = Array.from(new Set([...group.members, userData.id])); // prevent duplicates

      const { error: updateError } = await supabase
        .from('groups')
        .update({ members: updatedMembers })
        .eq('id', groupId);

      if (updateError) {
        alert('Failed to add member');
      } else {
        alert('Member added!');
      }
    });
  });
}

// ----------------------------
// Handle creating a new group
// ----------------------------
createForm.addEventListener('submit', async e => {
  e.preventDefault();

  const name = document.getElementById('group-name').value.trim();
  const desc = document.getElementById('group-desc').value.trim();
  const membersInput = document.getElementById('group-members').value;
  const memberEmails = membersInput.split(',').map(e => e.trim()).filter(Boolean);

  if (!name) {
    alert('Group name cannot be empty');
    return;
  }

  const memberIds = [];

  // Fetch member IDs from emails
  for (const email of memberEmails) {
    const { data: user } = await supabase.from('users').select('id').eq('email', email).single();
    if (user) memberIds.push(user.id);
  }

  const currentUser = supabase.auth.user();
  if (!currentUser) return;

  memberIds.push(currentUser.id); // include creator

  const { error } = await supabase.from('groups').insert([{
    name,
    description: desc,
    members: memberIds,
    created_at: new Date().toISOString()
  }]);

  if (error) {
    alert('Error creating group');
    console.error(error);
  } else {
    createForm.reset();
    fetchGroups();
  }
});

// ----------------------------
// Initial load
// ----------------------------
fetchGroups();
