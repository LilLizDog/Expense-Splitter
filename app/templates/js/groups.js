import { supabase } from './supabaseClient.js';

const groupsList = document.getElementById('groups-list');
const createForm = document.getElementById('create-group-form');

async function fetchGroups() {
  const user = supabase.auth.user();
  const { data: groups, error } = await supabase
    .from('groups')
    .select('*')
    .contains('members', [user.id])
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
        <a href="group.html?id=${group.id}" class="name">${group.name}</a>
        <div class="meta">${group.description || ''}</div>
        <div class="meta">Created: ${new Date(group.created_at).toLocaleDateString()}</div>
      </div>
      <button class="btn add-member" data-id="${group.id}">Add Member</button>
    `;
    groupsList.appendChild(div);
  });

  document.querySelectorAll('.add-member').forEach(btn => {
    btn.addEventListener('click', async () => {
      const memberEmail = prompt('Enter member email to add:');
      if (!memberEmail) return;

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
      const { data: group } = await supabase
        .from('groups')
        .select('members')
        .eq('id', groupId)
        .single();

      const updatedMembers = [...group.members, userData.id];

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

createForm.addEventListener('submit', async e => {
  e.preventDefault();
  const name = document.getElementById('group-name').value;
  const desc = document.getElementById('group-desc').value;
  const membersInput = document.getElementById('group-members').value;
  const memberEmails = membersInput.split(',').map(e => e.trim()).filter(Boolean);

  // Fetch user IDs for members
  const memberIds = [];
  for (const email of memberEmails) {
    const { data: user } = await supabase.from('users').select('id').eq('email', email).single();
    if (user) memberIds.push(user.id);
  }

  const currentUser = supabase.auth.user();
  memberIds.push(currentUser.id); // include creator

  const { error } = await supabase.from('groups').insert([{
    name, description: desc, members: memberIds, created_at: new Date().toISOString()
  }]);

  if (error) {
    alert('Error creating group');
    console.error(error);
  } else {
    createForm.reset();
    fetchGroups();
  }
});

fetchGroups();
