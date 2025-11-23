import { supabase } from './supabaseClient.js';

const params = new URLSearchParams(window.location.search);
const groupId = params.get('group_id');
if (!groupId) window.location.href = '/groups.html';

const nameEl = document.getElementById('group-name');
const descEl = document.getElementById('group-desc');
const dateEl = document.getElementById('group-date');
const txList = document.getElementById('tx-list');
const addMemberBtn = document.getElementById('add-member-btn');
const addExpenseBtn = document.getElementById('add-expense-btn');

async function loadGroup() {
  const { data, error } = await supabase.from('groups').select('*').eq('id', groupId).single();
  if (error) return alert('Group not found');
  nameEl.textContent = data.name;
  descEl.textContent = data.description || '';
  dateEl.textContent = new Date(data.created_at).toLocaleDateString();
}

async function loadTransactions() {
  const { data, error } = await supabase.from('transactions').select('*').eq('group_id', groupId).order('created_at', { ascending: false }).limit(10);
  txList.innerHTML = '';
  if (error || !data.length) txList.innerHTML = '<div class="muted">No transactions yet.</div>';
  data?.forEach(t => {
    const sign = t.amount >= 0 ? 'positive' : 'negative';
    txList.innerHTML += `
      <div class="tx">
        <div class="left">
          <div class="name">${t.name}</div>
          <div class="meta">${new Date(t.created_at).toLocaleDateString()}</div>
        </div>
        <div class="amt ${sign}">${sign === 'positive' ? '+' : '-'}$${Math.abs(t.amount).toFixed(2)}</div>
      </div>`;
  });
}

addMemberBtn.addEventListener('click', async () => {
  const email = prompt('Enter member email to add:');
  if (!email) return;
  const { data: user } = await supabase.from('users').select('id').eq('email', email).single();
  if (!user) return alert('User not found');
  const { data: group } = await supabase.from('groups').select('members').eq('id', groupId).single();
  const updated = [...new Set([...group.members, user.id])];
  await supabase.from('groups').update({ members: updated }).eq('id', groupId);
  alert('Member added!');
});

addExpenseBtn.addEventListener('click', () => {
  window.location.href = `/add_expense.html?group_id=${groupId}`;
});

loadGroup();
loadTransactions();
