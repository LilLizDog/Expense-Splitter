// ------------------ Elements ------------------
const searchInput = document.getElementById("searchInput");
const threadList = document.getElementById("threadList");
const notificationsList = document.getElementById("notificationsList");

// ------------------ Load Messages ------------------
async function loadMessages() {
    threadList.innerHTML = ""; // clear previous

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
    notificationsList.innerHTML = ""; // clear previous

    try {
        const res = await fetch("/inbox/notifications");
        const data = await res.json();

        if (!Array.isArray(data) || data.length === 0) {
            notificationsList.innerHTML = "<li class='p-2 text-gray-500'>No notifications</li>";
            return;
        }

        data.forEach(notif => {
            const li = document.createElement("li");
            li.className = "p-2 border-b";
            li.textContent = notif.type ? `${notif.type} from ${notif.from_user}` : "Notification";
            notificationsList.appendChild(li);
        });
    } catch (err) {
        console.error(err);
        notificationsList.innerHTML = "<li class='p-2 text-gray-500'>No notifications</li>";
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
