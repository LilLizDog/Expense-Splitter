// ------------------ Elements ------------------
const searchInput = document.getElementById("searchInput");
const threadList = document.getElementById("threadList");
const notificationsList = document.getElementById("notificationsList");

// ------------------ Load Messages ------------------
async function loadMessages() {
    threadList.innerHTML = "";

    try {
        const res = await fetch("/inbox/data");
        const data = await res.json();

        if (!Array.isArray(data) || data.length === 0) {
            threadList.innerHTML = "<li class='p-2 text-gray-500'>No messages</li>";
            return;
        }

        data.forEach(thread => {
            const li = document.createElement("li");
            li.className = "p-2 border-b";
            li.textContent = `${thread.name}: ${thread.last_message}`;
            li.dataset.name = thread.name.toLowerCase();
            threadList.appendChild(li);
        });
    } catch (err) {
        console.error(err);
        threadList.innerHTML = "<li class='p-2 text-gray-500'>No messages</li>";
    }
}

// ------------------ Load Notifications ------------------
async function loadNotifications() {
    notificationsList.innerHTML = "";

    try {
        const res = await fetch("/inbox/notifications");
        const data = await res.json();

        const badge = document.getElementById("notificationBadge");
        badge.textContent = data.length;
        badge.style.display = data.length > 0 ? "inline-block" : "none";

        if (!Array.isArray(data) || data.length === 0) {
            notificationsList.innerHTML = "<li class='p-2 text-gray-500'>No notifications</li>";
            return;
        }

        data.forEach(notif => {
            const li = document.createElement("li");
            li.className = "p-2 border-b flex justify-between items-center";

            let text = "";
            if (notif.type === "Friend Request") {
                text = `Friend Request from ${notif.from_user}`;
            } else if (notif.type === "Group Invite") {
                text = `Group Invite to '${notif.group_name}' from ${notif.from_user}`;
            } else {
                text = notif.type ? `${notif.type} from ${notif.from_user}` : "Notification";
            }

            li.innerHTML = `<span>${text}</span>`;

            if (notif.type === "Friend Request" || notif.type === "Group Invite") {
                const buttons = document.createElement("div");

                const acceptBtn = document.createElement("button");
                acceptBtn.textContent = "Accept";
                acceptBtn.className = "bg-green-500 text-white px-2 py-1 rounded mr-2";
                acceptBtn.onclick = () => handleNotification(notif.id, "accept", li);

                const declineBtn = document.createElement("button");
                declineBtn.textContent = "Decline";
                declineBtn.className = "bg-red-500 text-white px-2 py-1 rounded";
                declineBtn.onclick = () => handleNotification(notif.id, "decline", li);

                buttons.appendChild(acceptBtn);
                buttons.appendChild(declineBtn);
                li.appendChild(buttons);
            }

            notificationsList.appendChild(li);
        });
    } catch (err) {
        console.error(err);
        notificationsList.innerHTML = "<li class='p-2 text-gray-500'>No notifications</li>";
    }
}

// ------------------ Handle Accept/Decline ------------------
async function handleNotification(notifId, action, liElement) {
    try {
        const res = await fetch(`/inbox/notifications/${notifId}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ action })
        });

        const data = await res.json();
        if (data.success) {
            liElement.remove();
            const badge = document.getElementById("notificationBadge");
            const count = notificationsList.querySelectorAll("li").length;
            badge.textContent = count;
            badge.style.display = count > 0 ? "inline-block" : "none";
        }
    } catch (err) {
        console.error("Error handling notification:", err);
    }
}

// ------------------ Search Filter ------------------
searchInput.addEventListener("input", () => {
    const query = searchInput.value.toLowerCase();
    threadList.querySelectorAll("li").forEach(li => {
        if (li.dataset.name && li.dataset.name.includes(query)) {
            li.style.display = "";
        } else {
            li.style.display = "none";
        }
    });
});

// ------------------ Initialize ------------------
document.addEventListener("DOMContentLoaded", () => {
    loadMessages();
    loadNotifications();
});
