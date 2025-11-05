import { supabase } from './supabaseClient.js';

const form = document.getElementById('create-group-form');
const list = document.getElementById('groups-list');

// Load groups the current user belongs to
async function loadGroups() {
    const user = supabase.auth.user();
    if (!user) return;

    const { data: groups, error } = await supabase
        .from('groups')
        .select('*')
        .contains('members', [user.id]); // members is array of user IDs

    if (error) {
        console.error('Error fetching groups:', error);
        return;
    }

    list.innerHTML = '';

    if (groups.length === 0) {
        const li = document.createElement('li');
        li.textContent = 'You are not a member of any groups yet.';
        list.appendChild(li);
        return;
    }

    // Display groups as clickable links
    groups.forEach(group => {
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.href = `group.html?id=${group.id}`;
        a.textContent = group.name + (group.description ? ` - ${group.description}` : '');
        li.appendChild(a);
        list.appendChild(li);
    });
}

// Handle creating a new group
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = document.getElementById('group-name').value.trim();
    const description = document.getElementById('group-description').value.trim();

    if (!name) {
        alert('Group name cannot be empty!');
        return;
    }

    const user = supabase.auth.user();
    if (!user) {
        alert('You must be logged in to create a group.');
        return;
    }

    const { data, error } = await supabase
        .from('groups')
        .insert([{ name, description, members: [user.id] }]);

    if (error) {
        console.error('Error creating group:', error);
        alert('Failed to create group.');
    } else {
        form.reset();
        loadGroups();
    }
});

loadGroups();
