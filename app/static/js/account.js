// static/js/account.js
// Runs as a module inside <script type="module"> in account.html

console.log("account.js loaded!");

const el = (id) => document.getElementById(id);

// Elements - will be set in initAccountPage
let profileDisplay, displayFullName, displayUsername, displayEmail, displayPhoneNumber, displayCurrency, editProfileBtn;
let profileForm, full_name, username, email, phone_number, currency, cancelEditBtn, profileStatus;
let logoutBtn, logoutStatus;

function setStatus(node, msg, ok = true) {
  if (!node) return;
  node.textContent = msg || '';
  node.classList.toggle('ok', ok);
  node.classList.toggle('err', !ok);
}

function showViewMode() {
  if (profileDisplay) profileDisplay.style.display = "block";
  if (profileForm) profileForm.style.display = "none";
  setStatus(profileStatus, "");
}

function showEditMode() {
  if (profileDisplay) profileDisplay.style.display = "none";
  if (profileForm) profileForm.style.display = "block";
  setStatus(profileStatus, "");
}


function validateForm() {
  if (!full_name.value.trim()) {
    setStatus(profileStatus, 'Name is required', false);
    return false;
  }
  if (!username.value.trim()) {
    setStatus(profileStatus, 'Username is required', false);
    return false;
  }
  if (phone_number.value && !phone_number.checkValidity()) {
    setStatus(profileStatus, 'Invalid phone', false);
    return false;
  }
  return true;
}

async function saveProfile() {
  if (!validateForm()) return;

  const payload = {
    full_name: full_name.value.trim(),
    username:  username.value.trim(),
    phone_number: phone_number.value.trim(),
    display_currency: currency.value,
  };

  console.log("Saving profile with payload:", payload);

  let resp;
  try {
    resp = await fetch("/api/account", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (e) {
    console.error("Network error saving profile:", e);
    setStatus(profileStatus, "Network error", false);
    return;
  }

  if (!resp.ok) {
    const errorText = await resp.text();
    console.error("Save failed with status", resp.status, ":", errorText);
    setStatus(profileStatus, "Save failed", false);
    return;
  }

  const data = await resp.json();
  console.log("Server response:", data);
  const user = data.user || {};

  // Update the view and form from the server response
  displayFullName.textContent    = user.full_name || "—";
  displayUsername.textContent    = user.username || "—";
  displayEmail.textContent       = user.email || "—";
  displayPhoneNumber.textContent = user.phone_number || "—";
  displayCurrency.textContent    = user.display_currency || "USD";

  full_name.value     = user.full_name || "";
  username.value      = user.username || "";
  email.value         = user.email || "";
  phone_number.value  = user.phone_number || "";
  currency.value      = user.display_currency || "USD";

  setStatus(profileStatus, "Saved", true);
  showViewMode();
}

function initAccountPage() {
  // Get all elements after DOM is loaded
  profileDisplay = el('profileDisplay');
  displayFullName = el('display_full_name');
  displayUsername = el('display_username');
  displayEmail = el('display_email');
  displayPhoneNumber = el('display_phone_number');
  displayCurrency = el('display_currency');
  editProfileBtn = el('editProfileBtn');
  
  profileForm = el('profileForm');
  full_name = el('full_name');
  username = el('username');
  email = el('email');
  phone_number = el('phone_number');
  currency = el('currency');
  cancelEditBtn = el('cancelEditBtn');
  profileStatus = el('profileStatus');
  
  logoutBtn = el('logoutBtn');
  logoutStatus = el('logoutStatus');

  console.log("Initializing account page...");
  console.log("Elements found:", {
    profileDisplay: !!profileDisplay,
    profileForm: !!profileForm,
    editProfileBtn: !!editProfileBtn,
    cancelEditBtn: !!cancelEditBtn,
    full_name: !!full_name,
    username: !!username,
    email: !!email,
    phone_number: !!phone_number,
    currency: !!currency
  });

  showViewMode(); // HTML already has initial values from Jinja

  if (editProfileBtn) {
    editProfileBtn.addEventListener("click", () => {
      console.log("Edit button clicked");
      showEditMode();
    });
  } else {
    console.error("editProfileBtn not found!");
  }

  if (cancelEditBtn) {
    cancelEditBtn.addEventListener("click", () => {
      // Reset form to current display values
      full_name.value    = displayFullName.textContent === "—" ? "" : displayFullName.textContent;
      username.value     = displayUsername.textContent === "—" ? "" : displayUsername.textContent;
      email.value        = displayEmail.textContent === "—" ? "" : displayEmail.textContent;
      phone_number.value = displayPhoneNumber.textContent === "—" ? "" : displayPhoneNumber.textContent;
      currency.value     = displayCurrency.textContent || "USD";
      showViewMode();
    });
  }

  if (profileForm) {
    profileForm.addEventListener("submit", (e) => {
      e.preventDefault();
      console.log("Form submitted");
      saveProfile();
    });
  } else {
    console.error("profileForm not found!");
  }

  // Handle logout
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      try {
        // Sign out from Supabase if client is available
        if (window.sb && window.sb.auth) {
          await window.sb.auth.signOut();
        }
        // Redirect to login page
        window.location.href = "/login";
      } catch (err) {
        console.error("Error during logout:", err);
        // Still redirect even if there's an error
        window.location.href = "/login";
      }
    });
  }
}

// Wait for DOM to be ready before initializing
console.log("Setting up DOMContentLoaded listener, readyState:", document.readyState);
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAccountPage);
} else {
  // DOM is already ready
  console.log("DOM already ready, initializing now");
  initAccountPage();
}
