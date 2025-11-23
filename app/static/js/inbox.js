document.addEventListener("DOMContentLoaded", async () => {
    const searchInput = document.getElementById("searchInput");
    const threadList = document.getElementById("threadList");
    const notificationsList = document.getElementById("notificationsList");

    // --- Load messages ---
    async function loadThreads() {
        const res = await fetch("/inbox/data");
        const threads = await res.json();
        renderThreads(threads);

        searchInput.addEventListener("input", () => {
            const filtered = threads.filter(t =>
                t.name.toLowerCase().includes(searchInput.value.toLowerCase()) ||
                t.last_message.toLowerCase().includes(searchInput.value.toLowerCase())
            );
            renderThreads(filtered);
        });
    }

    function renderThreads(data) {
        threadList.innerHTML = "";
        data.forEach(t => {
            const li = document.createElement("li");
            li.className = "p-3 hover:bg-gray-100 cursor-pointer";
            li.innerHTML = `
                <div class="font-bold">${t.name}</div>
                <div class="text-sm text-gray-600">${t.last_message}</div>
            `;
            li.onclick = () => window.location.href = `/conversation/${t.thread_id}`;
            threadList.appendChild(li);
        });
    }

    // --- Load notifications ---
    async function loadNotifications() {
        const res = await fetch("/inbox/notifications");
        const notifications = await res.json();
        renderNotifications(notifications);
    }

    function renderNotifications(notifications) {
        notificationsList.innerHTML = "";
        notifications.forEach(n => {
            const li = document.createElement("li");
            li.className = "p-3 flex justify-between items-center hover:bg-gray-100";

            li.innerHTML = `
                <div>
                    <span class="font-bold">${n.from_user_name}</span>
                    <span class="text-sm text-gray-600">${n.type === 'friend_request' ? 'sent you a friend request' : 'invited you to a group: ' + (n.group_name || '')}</span>
                </div>
                <div class="space-x-2">
                    <button class="accept-btn bg-green-500 text-white px-3 py-1 rounded">Accept</button>
                    <button class="decline-btn bg-red-500 text-white px-3 py-1 rounded">Decline</button>
                </div>
            `;

            li.querySelector(".accept-btn").addEventListener("click", () => handleAction(n.id, "accept", li));
            li.querySelector(".decline-btn").addEventListener("click", () => handleAction(n.id, "decline", li));

            notificationsList.appendChild(li);
        });
    }

    async function handleAction(notificationId, action, liElement) {
        const res = await fetch("/inbox/notifications/action", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ notification_id: notificationId, action })
        });
        if (res.ok) {
            liElement.remove();
        } else {
            alert("Failed to process notification.");
        }
    }

    loadThreads();
    loadNotifications();
});
