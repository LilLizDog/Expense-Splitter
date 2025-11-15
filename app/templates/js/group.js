document.addEventListener("DOMContentLoaded", async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const groupId = urlParams.get("group_id");

    if (!groupId) {
        alert("No group selected.");
        window.location.href = "/groups.html";
        return;
    }

    const groupNameEl = document.getElementById("groupName");
    const membersListEl = document.getElementById("membersList");
    const expensesListEl = document.getElementById("expensesList");
    const addExpenseBtn = document.getElementById("addExpenseBtn");

    // Load Group Info
    async function loadGroup() {
        const res = await fetch(`/groups/${groupId}`);
        const data = await res.json();
        groupNameEl.textContent = data.name;
    }

    // Load Members
    async function loadMembers() {
        const res = await fetch(`/groups/${groupId}/members`);
        const members = await res.json();

        membersListEl.innerHTML = "";
        members.forEach(member => {
            const p = document.createElement("p");
            p.textContent = member.name;
            membersListEl.appendChild(p);
        });
    }

    // Load Expenses
    async function loadExpenses() {
        const res = await fetch(`/groups/${groupId}/expenses`);
        const expenses = await res.json();

        expensesListEl.innerHTML = "";
        expenses.forEach(exp => {
            const div = document.createElement("div");
            div.className = "expense-item";
            div.innerHTML = `
                <p><strong>${exp.title}</strong> - $${exp.amount}</p>
                <p>Paid by: ${exp.paid_by}</p>
            `;
            expensesListEl.appendChild(div);
        });
    }

    // Add Expense Button → redirect to add_expense.html
    addExpenseBtn.addEventListener("click", () => {
        window.location.href = `/add_expense.html?group_id=${groupId}`;
    });

    await loadGroup();
    await loadMembers();
    await loadExpenses();
});
