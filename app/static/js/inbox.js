// --- Elements ---
const threadList = document.getElementById("threadList");
const notificationsList = document.getElementById("notificationsList");
const searchInput = document.getElementById("searchInput");

// --- Fetch messages ---
async function fetchMessages() {
    try {
        const res = await fetch("/inbox/data");
        if (!res.ok) throw new Error("Failed to fetch messages");
        const threads = await res.json();

        threadList.innerHTML = ""; // Clear old threads

        threads.forEach(thread => {
            const li = document.createElement("li");
            li.className = "p-3 hover:bg-gray-100 cursor-pointer";
            li.textContent = `${thread.name}: ${thread.last_message}`;
            threadList.appendChild(li);
        });
    } catch (err) {
        console.error("Error fetching messages:", err);
        threadList.innerHTML = "<li class='p-3 text-red-500'>Could not load messages</li>";
    }
}

// --- Fetch notifications ---
async function fetchNotifications() {
    try {
        const res = await fetch("/inbox/notifications");
        if (!res.ok) throw new Error("Failed to fetch notifications");
        const notifications = await res.json();

        notificationsList.innerHTML = ""; // Clear old notifications

        notifications.forEach(notif => {
            const li = document.createElement("li");
            li.className = "p-3 flex justify-between items-center hover:bg-gray-100";

            li.innerHTML = `
                <span>${notif.type} from ${notif.from_user}</span>
                <div>
                    <button class="accept-btn bg-green-500 text-white px-2 py-1 rounded mr-2" data-id="${notif.id}">Accept</button>
                    <button class="decline-btn bg-red-500 text-white px-2 py-1 rounded" data-id="${notif.id}">Decline</button>
                </div>
            `;
            notificationsList.appendChild(li);
        });

        // Add click handlers
        document.querySelectorAll(".accept-btn").forEach(btn => {
            btn.addEventListener("click", () => handleNotification(btn.dataset.id, "accept"));
        });
        document.querySelectorAll(".decline-btn").forEach(btn => {
            btn.addEventListener("click", () => handleNotification(btn.dataset.id, "decline"));
        });
    } catch (err) {
        console.error("Error fetching notifications:", err);
        notificationsList.innerHTML = "<li class='p-3 text-red-500'>Could not load notifications</li>";
    }
}

// --- Handle accept/decline ---
async function handleNotification(notificationId, action) {
    try {
        const res = await fetch("/inbox/notifications/action", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ notification_id: notificationId, action })
        });
        if (!res.ok) throw new Error("Failed to update notification");

        fetchNotifications();
    } catch (err) {
        console.error("Error handling notification:", err);
    }
}

// --- Search messages ---
searchInput.addEventListener("input", () => {
    const query = searchInput.value.toLowerCase();
    threadList.querySelectorAll("li").forEach(li => {
        li.style.display = li.textContent.toLowerCase().includes(query) ? "" : "none";
    });
});

// --- Initial fetch ---
fetchMessages();
fetchNotifications();
