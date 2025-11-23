// ------------------------
// Inbox JS
// ------------------------

// Fetch and display messages
async function loadMessages() {
    const threadList = document.getElementById("threadList");
    threadList.innerHTML = "";

    try {
        const response = await fetch("/inbox/data");
        const threads = await response.json();

        if (!threads || threads.length === 0) {
            threadList.innerHTML = `<li class="p-2 text-gray-500">No messages</li>`;
            return;
        }

        threads.forEach(thread => {
            const li = document.createElement("li");
            li.className = "p-2 border-b";
            li.textContent = `${thread.name}: ${thread.last_message}`;
            threadList.appendChild(li);
        });
    } catch (err) {
        threadList.innerHTML = `<li class="p-2 text-red-500">Could not load messages</li>`;
        console.error(err);
    }
}

// Fetch and display notifications
async function loadNotifications() {
    const notificationsList = document.getElementById("notificationsList");
    notificationsList.innerHTML = "";

    try {
        const response = await fetch("/inbox/notifications");
        const notifications = await response.json();

        if (!notifications || notifications.length === 0) {
            notificationsList.innerHTML = `<li class="p-2 text-gray-500">No notifications</li>`;
            return;
        }

        notifications.forEach(notif => {
            const li = document.createElement("li");
            li.className = "p-2 border-b flex justify-between items-center";

            const textSpan = document.createElement("span");
            textSpan.textContent = `${notif.type} from ${notif.from_user}`;
            li.appendChild(textSpan);

            // Only show buttons for friend requests or group invites
            if (notif.type === "friend_request" || notif.type === "group_invite") {
                const buttonContainer = document.createElement("div");

                const acceptBtn = document.createElement("button");
                acceptBtn.className = "mr-2 px-2 py-1 bg-green-500 text-white rounded";
                acceptBtn.textContent = "Accept";
                acceptBtn.onclick = () => handleNotificationAction(notif.id, "accept");

                const declineBtn = document.createElement("button");
                declineBtn.className = "px-2 py-1 bg-red-500 text-white rounded";
                declineBtn.textContent = "Decline";
                declineBtn.onclick = () => handleNotificationAction(notif.id, "decline");

                buttonContainer.appendChild(acceptBtn);
                buttonContainer.appendChild(declineBtn);
                li.appendChild(buttonContainer);
            }

            notificationsList.appendChild(li);
        });
    } catch (err) {
        notificationsList.innerHTML = `<li class="p-2 text-red-500">Could not load notifications</li>`;
        console.error(err);
    }
}

// Handle Accept / Decline actions
async function handleNotificationAction(notificationId, action) {
    try {
        const response = await fetch("/inbox/notifications/action", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ notification_id: notificationId, action })
        });

        const data = await response.json();
        if (data.success) {
            // Refresh notifications after action
            loadNotifications();
        } else {
            alert("Failed to process action: " + (data.error || "Unknown error"));
        }
    } catch (err) {
        alert("Error performing action: " + err);
        console.error(err);
    }
}

// Optional: Search messages
document.getElementById("searchInput")?.addEventListener("input", function () {
    const query = this.value.toLowerCase();
    const threadList = document.getElementById("threadList");
    [...threadList.children].forEach(li => {
        li.style.display = li.textContent.toLowerCase().includes(query) ? "" : "none";
    });
});

// Initialize inbox
document.addEventListener("DOMContentLoaded", () => {
    loadMessages();
    loadNotifications();
});
