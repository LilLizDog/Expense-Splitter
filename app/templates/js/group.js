import { supabase } from './supabaseClient.js';

const params = new URLSearchParams(window.location.search);
const groupId = params.get('id');

const groupNameElem = document.getElementById('group-name');
const groupDescriptionElem = document.getElementById('group-description');
const expensesList = document.getElementById('expenses-list');

const expenseForm = document.getElementById('create-expense-form');
const expenseNameInput = document.getElementById('expense-name');
const expenseAmountInput = document.getElementById('expense-amount');

async function loadGroup() {
    if (!groupId) return;

    const user = supabase.auth.user();
    if (!user) return;

    // Fetch group details
    const { data: group, error } = await supabase
        .from('groups')
        .select('*')
        .eq('id', groupId)
        .single();

    if (error) {
        console.error('Error fetching group:', error);
        groupNameElem.textContent = 'Group not found or access denied.';
        return;
    }

    // Access control
    if (!group.members.includes(user.id)) {
        groupNameElem.textContent = 'You are not a member of this group.';
        return;
    }

    groupNameElem.textContent = group.name;
    groupDescriptionElem.textContent = group.description || '';

    await loadExpenses();
}

async function loadExpenses() {
    const { data: expenses, error } = await supabase
        .from('expenses')
        .select('*')
        .eq('group_id', groupId);

    if (error) {
        console.error('Error fetching expenses:', error);
        return;
    }

    expensesList.innerHTML = '';

    if (expenses.length === 0) {
        const li = document.createElement('li');
        li.textContent = 'No expenses yet.';
        expensesList.appendChild(li);
        return;
    }

    expenses.forEach(exp => {
        const li = document.createElement('li');
        li.textContent = `${exp.name} - $${exp.amount.toFixed(2)}`;
        expensesList.appendChild(li);
    });
}

// Handle creating a new expense
expenseForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = expenseNameInput.value.trim();
    const amount = parseFloat(expenseAmountInput.value);

    if (!name || isNaN(amount) || amount <= 0) {
        alert('Please enter a valid name and amount.');
        return;
    }

    const user = supabase.auth.user();
    if (!user) {
        alert('You must be logged in to add an expense.');
        return;
    }

    const { data, error } = await supabase
        .from('expenses')
        .insert([{ name, amount, group_id: groupId, user_id: user.id }]);

    if (error) {
        console.error('Error adding expense:', error);
        alert('Failed to add expense.');
    } else {
        expenseForm.reset();
        loadExpenses();
    }
});

loadGroup();
