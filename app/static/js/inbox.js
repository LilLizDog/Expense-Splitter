// Simple notifications only inbox

// Core elements
const notificationsList = document.getElementById("notificationsList");

// Build one notification line of text based on type
function buildNotificationText(notif) {
  const type = notif.type || "";
  const fromName = notif.from_user || "Someone";
  const groupName = notif.group_name || null;

  if (type === "Friend Added") {
    return `${fromName} added you as a friend`;
  }
  if (type === "Friend Removed") {
    return `${fromName} removed you as a friend`;
  }
  if (type === "Group Created") {
    return groupName
      ? `'${groupName}' was created by ${fromName}`
      : `A group was created by ${fromName}`;
  }
  if (type === "Group Deleted") {
    return groupName
      ? `'${groupName}' was deleted by ${fromName}`
      : `A group was deleted by ${fromName}`;
  }
  if (type === "Group Member Added") {
    return groupName
      ? `You were added to '${groupName}' by ${fromName}`
      : `You were added to a group by ${fromName}`;
  }
  if (type === "Group Member Removed") {
    return groupName
      ? `You were removed from '${groupName}' by ${fromName}`
      : `You were removed from a group by ${fromName}`;
  }
  if (type === "Expense") {
    return groupName
      ? `New expense found for you in '${groupName}'. Check your history.`
      : `New expense found for you. Check your history.`;
  }
  if (type) {
    return `${type} from ${fromName}`;
  }
  return "Notification";
}

// Load notifications from backend
async function loadNotifications() {
  if (!notificationsList) {
    return;
  }
  notificationsList.innerHTML = "";

  try {
    const res = await fetch("/inbox/notifications");
    const data = await res.json();

    const badge = document.getElementById("notificationBadge");
    const count = Array.isArray(data) ? data.length : 0;
    if (badge) {
      badge.textContent = String(count);
      badge.style.display = count > 0 ? "inline-flex" : "none";
    }

    if (!Array.isArray(data) || data.length === 0) {
      notificationsList.innerHTML =
        "<li class='p-3 text-gray-500'>No notifications</li>";
      return;
    }

    data.forEach((notif) => {
      const li = document.createElement("li");
      li.className = "p-3 flex justify-between items-center";

      const left = document.createElement("div");
      left.className = "flex flex-col";

      const textSpan = document.createElement("span");
      textSpan.textContent = buildNotificationText(notif);
      left.appendChild(textSpan);

      let dateLabel = "";
      if (notif.created_at) {
        const d = new Date(notif.created_at);
        if (!Number.isNaN(d.getTime())) {
          dateLabel = d.toLocaleDateString(undefined, {
            year: "numeric",
            month: "short",
            day: "numeric",
          });
        }
      }

      const right = document.createElement("div");
      right.className = "text-sm text-gray-400 ml-4 whitespace-nowrap";
      right.textContent = dateLabel;

      li.appendChild(left);
      li.appendChild(right);
      notificationsList.appendChild(li);
    });
  } catch (err) {
    console.error("Error loading notifications", err);
    notificationsList.innerHTML =
      "<li class='p-3 text-gray-500'>No notifications</li>";
  }
}

// Init
document.addEventListener("DOMContentLoaded", () => {
  loadNotifications();
});
