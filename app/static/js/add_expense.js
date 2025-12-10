// FILE: static/js/add_expense.js

// Prefill the date field with today's date and block future dates
function presetToday() {
  const d = document.getElementById("date");
  if (!d) {
    return;
  }

  const t = new Date();
  const mm = String(t.getMonth() + 1).padStart(2, "0");
  const dd = String(t.getDate()).padStart(2, "0");
  const todayStr = `${t.getFullYear()}-${mm}-${dd}`;

  d.value = todayStr;
  d.max = todayStr;
}

// Small helper to avoid using numeric ids as uuids
function isLikelyUuid(val) {
  if (!val) return false;
  if (typeof val !== "string") return false;
  const s = val.trim();
  if (!s) return false;
  if (/^\d+$/.test(s)) return false;
  if (s.includes("-")) return true;
  return s.length >= 16;
}

document.addEventListener("DOMContentLoaded", () => {
  // Set initial date value when the page is ready
  presetToday();

  // Core elements
  const form = document.getElementById("expenseForm");
  const saveBtn = document.querySelector(".actions .btn.primary");
  const saveHint = document.getElementById("saveHint");

  // Group vs non group controls
  const groupRadioYes = document.querySelector(
    'input[name="is_group_expense"][value="yes"]'
  );
  const groupRadioNo = document.querySelector(
    'input[name="is_group_expense"][value="no"]'
  );

  const groupSection = document.getElementById("groupSection");
  const friendSection = document.getElementById("friendSection");
  const friendSplitSection = document.getElementById("friendSplitSection");

  const friendSplitYes = document.querySelector(
    'input[name="friend_split"][value="yes"]'
  );
  const friendSplitNo = document.querySelector(
    'input[name="friend_split"][value="no"]'
  );

  const friendCustomAmountWrap = document.getElementById(
    "friendCustomAmountWrap"
  );
  const friendCustomAmountInput = document.getElementById(
    "friendCustomAmount"
  );
  const friendCustomPercentWrap = document.getElementById(
    "friendCustomPercentWrap"
  );
  const friendCustomPercentInput = document.getElementById(
    "friendCustomPercent"
  );

  // Group split controls
  const groupSelect = document.getElementById("group");
  const memberBtn = document.getElementById("memberBtn");
  const memberPanel = document.getElementById("memberPanel");
  const memberSelectAll = document.getElementById("memberSelectAll");
  const memberSearch = document.getElementById("memberSearch");
  const memberList = document.getElementById("memberList");
  const memberDone = document.getElementById("memberDone");
  const memberClear = document.getElementById("memberClear");
  const memberHiddenInputs = document.getElementById("memberHiddenInputs");

  const splitTypeSection = document.getElementById("splitTypeSection");
  const splitError = document.getElementById("splitError");
  const splitTypeRadios = document.querySelectorAll('input[name="split_type"]');

  const customAmountSection = document.getElementById("customAmountSection");
  const customAmountRows = document.getElementById("customAmountRows");
  const amountRemaining = document.getElementById("amountRemaining");

  const customPercentageSection = document.getElementById(
    "customPercentageSection"
  );
  const customPercentageRows = document.getElementById("customPercentageRows");
  const percentageRemaining = document.getElementById("percentageRemaining");

  // Shared fields
  const friendSelect = document.getElementById("friendSelect");
  const dateInput = document.getElementById("date");
  const expenseTypeSelect = document.getElementById("expense_type");
  const descriptionInput = document.getElementById("description");
  const totalInput = document.getElementById("total");

  // In memory lookup for group members so we can show names in custom rows
  const groupMembersById = new Map();

  // Helper: get selected values
  function isGroupExpense() {
    return groupRadioYes.checked;
  }

  function getFriendSplitValue() {
    return friendSplitYes.checked ? "yes" : "no";
  }

  function getSplitTypeValue() {
    const checked = document.querySelector('input[name="split_type"]:checked');
    return checked ? checked.value : "equal";
  }

  function getNumericValue(input) {
    if (!input) {
      return NaN;
    }
    const v = parseFloat(input.value);
    return Number.isFinite(v) ? v : NaN;
  }

  // Helper: manage disabled state and message
  function setSaveEnabled(enabled, message) {
    if (!saveBtn) return;

    saveBtn.disabled = !enabled;

    if (saveHint) {
      if (message) {
        saveHint.textContent = message;
        saveHint.style.display = "block";
      } else {
        saveHint.textContent = "";
        saveHint.style.display = "none";
      }
    }
  }

  // Visibility for group vs friend modes
  function updateModeVisibility() {
    if (isGroupExpense()) {
      groupSection.classList.remove("hidden");
      friendSection.classList.add("hidden");
      friendSplitSection.classList.add("hidden");

      splitTypeSection.classList.remove("hidden");
      friendCustomAmountWrap.classList.add("hidden");
      friendCustomPercentWrap.classList.add("hidden");
    } else {
      groupSection.classList.add("hidden");
      friendSection.classList.remove("hidden");
      friendSplitSection.classList.remove("hidden");

      // In non group mode the main split section is only needed when splitting with friend
      if (getFriendSplitValue() === "yes") {
        splitTypeSection.classList.remove("hidden");
      } else {
        splitTypeSection.classList.add("hidden");
      }

      // Custom group sections are not used in non group mode
      customAmountSection.classList.add("hidden");
      customPercentageSection.classList.add("hidden");
    }

    updateSplitDetailsVisibility();
  }

  // Visibility for custom split sections
  function updateSplitDetailsVisibility() {
    const splitType = getSplitTypeValue();

    if (isGroupExpense()) {
      // Group expense uses group custom sections
      if (splitType === "equal") {
        customAmountSection.classList.add("hidden");
        customPercentageSection.classList.add("hidden");
      } else if (splitType === "amount") {
        customAmountSection.classList.remove("hidden");
        customPercentageSection.classList.add("hidden");
      } else if (splitType === "percentage") {
        customAmountSection.classList.add("hidden");
        customPercentageSection.classList.remove("hidden");
      }

      // Friend specific custom controls are hidden in group mode
      friendCustomAmountWrap.classList.add("hidden");
      friendCustomPercentWrap.classList.add("hidden");
    } else {
      // Non group mode, only if splitting with friend
      if (getFriendSplitValue() === "yes") {
        if (splitType === "equal") {
          friendCustomAmountWrap.classList.add("hidden");
          friendCustomPercentWrap.classList.add("hidden");
        } else if (splitType === "amount") {
          friendCustomAmountWrap.classList.remove("hidden");
          friendCustomPercentWrap.classList.add("hidden");
        } else if (splitType === "percentage") {
          friendCustomAmountWrap.classList.add("hidden");
          friendCustomPercentWrap.classList.remove("hidden");
        }
      } else {
        friendCustomAmountWrap.classList.add("hidden");
        friendCustomPercentWrap.classList.add("hidden");
      }
    }
  }

  // Build selected member id list from hidden inputs
  function getSelectedMemberIds() {
    const inputs = memberHiddenInputs.querySelectorAll(
      'input[name="member_ids[]"]'
    );
    return Array.from(inputs).map((el) => el.value);
  }

  // Group member rows for custom splits
  function rebuildCustomRows() {
    const memberIds = getSelectedMemberIds();
    customAmountRows.innerHTML = "";
    customPercentageRows.innerHTML = "";

    memberIds.forEach((id) => {
      const member = groupMembersById.get(id);
      const displayName = member ? member.display_name : "Member";

      const amountRow = document.createElement("div");
      amountRow.className = "split-row";
      amountRow.dataset.memberId = id;
      amountRow.innerHTML = `
        <label style="flex:1 1 auto; min-width:120px;">
          ${displayName}
        </label>
        <div class="money-field" style="max-width:200px; flex:0 0 auto;">
          <span class="prefix" aria-hidden="true">$</span>
          <input
            type="number"
            step="0.01"
            inputmode="decimal"
            placeholder="0.00"
            min="0"
            data-role="amount-input"
          />
        </div>
      `;
      customAmountRows.appendChild(amountRow);

      const percentRow = document.createElement("div");
      percentRow.className = "split-row";
      percentRow.dataset.memberId = id;
      percentRow.innerHTML = `
        <label style="flex:1 1 auto; min-width:120px;">
          ${displayName}
        </label>
        <div style="display:flex; align-items:center; gap:6px; max-width:220px;">
          <input
            type="number"
            step="0.01"
            inputmode="decimal"
            placeholder="0"
            min="0"
            max="100"
            style="width:80px;"
            data-role="percent-input"
          />
          <span>%</span>
        </div>
      `;
      customPercentageRows.appendChild(percentRow);
    });

    amountRemaining.textContent = "";
    amountRemaining.style.display = "none";
    percentageRemaining.textContent = "";
    percentageRemaining.style.display = "none";
  }

  // Validation for group custom splits
  function validateGroupSplits(totalValue) {
    const splitType = getSplitTypeValue();
    splitError.textContent = "";
    splitError.style.display = "none";

    amountRemaining.style.display = "none";
    percentageRemaining.style.display = "none";

    if (splitType === "equal") {
      return { ok: true, message: "" };
    }

    if (splitType === "amount") {
      let sum = 0;
      const inputs = customAmountRows.querySelectorAll(
        'input[data-role="amount-input"]'
      );
      inputs.forEach((input) => {
        const v = parseFloat(input.value);
        if (Number.isFinite(v)) {
          sum += v;
        }
      });

      const diff = sum - totalValue;
      const eps = 0.01;

      if (Math.abs(diff) <= eps) {
        amountRemaining.classList.remove("under", "over");
        amountRemaining.textContent = "Split balances with the total.";
        amountRemaining.style.display = "block";
        return { ok: true, message: "" };
      }

      if (diff < 0) {
        amountRemaining.classList.add("under");
        amountRemaining.classList.remove("over");
        amountRemaining.textContent = `You still have $${Math.abs(
          diff
        ).toFixed(2)} left to assign.`;
      } else {
        amountRemaining.classList.add("over");
        amountRemaining.classList.remove("under");
        amountRemaining.textContent = `You assigned $${diff.toFixed(
          2
        )} more than the total.`;
      }
      amountRemaining.style.display = "block";

      return { ok: false, message: "Custom amounts must match the total." };
    }

    if (splitType === "percentage") {
      let sum = 0;
      const inputs = customPercentageRows.querySelectorAll(
        'input[data-role="percent-input"]'
      );
      inputs.forEach((input) => {
        const v = parseFloat(input.value);
        if (Number.isFinite(v)) {
          sum += v;
        }
      });

      const diff = sum - 100;
      const eps = 0.01;

      if (Math.abs(diff) <= eps) {
        percentageRemaining.classList.remove("under", "over");
        percentageRemaining.textContent = "Percentages add up to 100%.";
        percentageRemaining.style.display = "block";
        return { ok: true, message: "" };
      }

      if (diff < 0) {
        percentageRemaining.classList.add("under");
        percentageRemaining.classList.remove("over");
        percentageRemaining.textContent = `You still have ${Math.abs(
          diff
        ).toFixed(2)}% left to assign.`;
      } else {
        percentageRemaining.classList.add("over");
        percentageRemaining.classList.remove("under");
        percentageRemaining.textContent = `You assigned ${diff.toFixed(
          2
        )}% more than 100%.`;
      }
      percentageRemaining.style.display = "block";

      return {
        ok: false,
        message: "Custom percentages must add up to 100%.",
      };
    }

    return { ok: true, message: "" };
  }

  // Validation for non group friend mode
  function validateFriendMode(totalValue) {
    if (!friendSelect.value) {
      return { ok: false, message: "Select a friend for this expense." };
    }

    const splitWithFriend = getFriendSplitValue();

    if (splitWithFriend === "no") {
      // Friend owes the full amount, no extra details needed
      return { ok: true, message: "" };
    }

    const splitType = getSplitTypeValue();

    if (splitType === "equal") {
      // Two way equal split, backend can interpret this as needed
      return { ok: true, message: "" };
    }

    if (splitType === "amount") {
      const friendAmount = getNumericValue(friendCustomAmountInput);

      if (!Number.isFinite(friendAmount) || friendAmount <= 0) {
        return {
          ok: false,
          message: "Enter how much this friend should owe.",
        };
      }
      if (friendAmount > totalValue + 0.01) {
        return {
          ok: false,
          message: "Friend amount cannot be more than the total.",
        };
      }
      return { ok: true, message: "" };
    }

    if (splitType === "percentage") {
      const friendPercent = getNumericValue(friendCustomPercentInput);

      if (!Number.isFinite(friendPercent) || friendPercent <= 0) {
        return {
          ok: false,
          message: "Enter what percent the friend should owe.",
        };
      }
      if (friendPercent > 100.01) {
        return {
          ok: false,
          message: "Friend percent cannot be more than 100%.",
        };
      }
      return { ok: true, message: "" };
    }

    return { ok: true, message: "" };
  }

  // Main validation that controls the Save button state
  function recalcSaveState() {
    const dateVal = dateInput.value;
    const typeVal = expenseTypeSelect.value;
    const totalValue = getNumericValue(totalInput);

    // Basic required fields
    if (!dateVal || !typeVal || !Number.isFinite(totalValue) || totalValue <= 0) {
      setSaveEnabled(false, "Fill all required fields and a positive total.");
      return;
    }

    if (isGroupExpense()) {
      if (!groupSelect.value) {
        setSaveEnabled(false, "Select a group for this expense.");
        return;
      }

      const memberIds = getSelectedMemberIds();
      if (!memberIds.length) {
        setSaveEnabled(false, "Select at least one member.");
        return;
      }

      const splitCheck = validateGroupSplits(totalValue);
      if (!splitCheck.ok) {
        setSaveEnabled(false, splitCheck.message);
        return;
      }

      setSaveEnabled(true, "");
    } else {
      const friendCheck = validateFriendMode(totalValue);
      if (!friendCheck.ok) {
        setSaveEnabled(false, friendCheck.message);
        return;
      }
      setSaveEnabled(true, "");
    }
  }

  // Load helpers
  async function fetchJson(url) {
    const resp = await fetch(url, { headers: { Accept: "application/json" } });
    if (!resp.ok) {
      throw new Error(`Request failed with status ${resp.status}`);
    }
    return resp.json();
  }

  // Normalize different response shapes into a simple array
  function normalizeRows(payload) {
    if (Array.isArray(payload)) return payload;
    if (Array.isArray(payload?.data)) return payload.data;
    if (Array.isArray(payload?.members)) return payload.members;
    if (Array.isArray(payload?.groups)) return payload.groups;
    if (Array.isArray(payload?.friends)) return payload.friends;
    return [];
  }

  async function loadGroups() {
    try {
      const raw = await fetchJson("/api/groups");
      const data = normalizeRows(raw);

      groupSelect.innerHTML =
        '<option value="" disabled selected>Select a group...</option>';

      if (!data.length) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = "No groups found";
        opt.disabled = true;
        groupSelect.appendChild(opt);
        groupSelect.disabled = true;
        memberBtn.disabled = true;
        memberBtn.textContent = "Choose a group first.";
        return;
      }

      data.forEach((g) => {
        const id = g.id ?? g.group_id ?? g.uuid ?? g.pk;
        const name = g.name ?? g.group_name ?? g.title ?? `Group ${id}`;
        if (id != null) {
          const opt = document.createElement("option");
          opt.value = String(id);
          opt.textContent = String(name);
          groupSelect.appendChild(opt);
        }
      });

      groupSelect.disabled = false;
      memberBtn.disabled = true;
      memberBtn.textContent = "Choose a group first.";
    } catch (err) {
      console.error("Failed to load groups:", err);
      groupSelect.innerHTML =
        '<option value="" disabled selected>Error loading groups</option>';
      groupSelect.disabled = true;
      memberBtn.disabled = true;
      memberBtn.textContent = "Error loading members";
    }
  }

  async function loadFriends() {
    const sel = friendSelect;
    if (!sel) {
      console.error("friendSelect element not found");
      return;
    }

    console.log("Loading friends...");
    
    try {
      const res = await fetch("/api/friends", {
        headers: { Accept: "application/json" },
      });

      console.log("Friends API response status:", res.status);
      
      if (!res.ok) {
        console.error("Friends API failed:", res.status, res.statusText);
        const errorText = await res.text();
        console.error("Error details:", errorText);
        sel.innerHTML = '<option disabled>Error loading friends</option>';
        return;
      }

      const json = await res.json();
      console.log("friends API response:", json);

      const friends = Array.isArray(json.friends) ? json.friends : [];
      console.log("Number of friends:", friends.length);

      sel.innerHTML =
        '<option value="" disabled selected>Select a friend...</option>';

      friends.forEach((f) => {
        // Use the real user uuid coming from the API
        const userId =
          f.friend_user_id ||
          f.user_id ||
          f.friend_id ||
          f.id;

        if (!userId) {
          console.warn("Friend missing user ID:", f);
          return;
        }

        const displayName =
          f.name ||
          f.full_name ||
          f.username ||
          f.email ||
          "Friend";

        const opt = document.createElement("option");
        opt.value = String(userId);
        opt.textContent = String(displayName);
        sel.appendChild(opt);
      });

      if (friends.length === 0) {
        sel.innerHTML = '<option disabled>No friends found</option>';
      }
      
      console.log("Friends loaded successfully");
    } catch (err) {
      console.error("Failed to load friends", err);
      sel.innerHTML = '<option disabled>Error loading friends</option>';
    }
  }


  // Load members for a specific group from the API and render the list
  async function loadMembersFor(groupId) {
    memberList.innerHTML =
      '<div class="muted" style="padding:8px;">Loading members…</div>';
    memberSelectAll.checked = false;
    memberHiddenInputs.innerHTML = "";
    groupMembersById.clear();

    try {
      const rows = normalizeRows(
        await fetchJson(`/api/groups/${groupId}/members`)
      );

      if (!rows.length) {
        memberList.innerHTML =
          '<div class="muted" style="padding:8px;">No members in this group.</div>';
        return;
      }

      memberList.innerHTML = "";

      rows.forEach((m) => {
        // Prefer the user uuid fields over any numeric id
        let rawMemberId =
          m.member_id ||
          m.user_id ||
          (m.member && (m.member.id || m.member.user_id)) ||
          (m.user && (m.user.id || m.user.user_id));

        // Fall back to id only if it looks like a uuid
        if (!rawMemberId && isLikelyUuid(String(m.id))) {
          rawMemberId = String(m.id);
        }

        if (!rawMemberId) {
          return;
        }

        const id = String(rawMemberId);
        const name = String(
          m.display_name ||
            m.name ||
            m.full_name ||
            m.username ||
            (m.member &&
              (m.member.name ||
                m.member.full_name ||
                m.member.username ||
                m.member.email)) ||
            (m.user &&
              (m.user.name ||
                m.user.full_name ||
                m.user.username ||
                m.user.email)) ||
            `User ${id}`
        );

        groupMembersById.set(id, { display_name: name });

        const item = document.createElement("div");
        item.className = "dd-item";
        item.dataset.memberId = id;

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";

        const labelSpan = document.createElement("span");
        labelSpan.textContent = name;

        item.appendChild(checkbox);
        item.appendChild(labelSpan);

        item.addEventListener("click", (evt) => {
          if (evt.target.tagName.toLowerCase() !== "input") {
            checkbox.checked = !checkbox.checked;
          }
        });

        memberList.appendChild(item);
      });
    } catch (err) {
      console.error("Failed to load members:", err);
      memberList.innerHTML =
        '<div class="muted" style="padding:8px;">Error loading members.</div>';
    }
  }

  function openMemberPanel() {
    if (!groupSelect.value) {
      return;
    }

    if (!memberList.innerHTML.trim()) {
      memberList.innerHTML =
        '<div class="muted" style="padding:8px;">No members in this group.</div>';
    }

    memberPanel.classList.remove("hidden");
    memberBtn.setAttribute("aria-expanded", "true");
    memberSearch.value = "";
    memberSelectAll.checked = false;
  }

  function closeMemberPanel() {
    memberPanel.classList.add("hidden");
    memberBtn.setAttribute("aria-expanded", "false");
  }

  function syncSelectedMembersFromPanel() {
    memberHiddenInputs.innerHTML = "";

    const items = memberList.querySelectorAll(".dd-item");
    const selectedIds = [];

    items.forEach((item) => {
      const checkbox = item.querySelector("input[type='checkbox']");
      if (checkbox && checkbox.checked) {
        const memberId = item.dataset.memberId;
        selectedIds.push(memberId);
      }
    });

    selectedIds.forEach((id) => {
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = "member_ids[]";
      input.value = id;
      memberHiddenInputs.appendChild(input);
    });

    if (selectedIds.length) {
      memberBtn.textContent = `${selectedIds.length} member(s) selected`;
    } else {
      memberBtn.textContent = "Select members";
    }

    rebuildCustomRows();
    recalcSaveState();
  }

  function applyMemberSearchFilter() {
    const term = memberSearch.value.trim().toLowerCase();

    const items = memberList.querySelectorAll(".dd-item");
    items.forEach((item) => {
      const text = item.textContent.toLowerCase();
      item.style.display = text.includes(term) ? "flex" : "none";
    });
  }

  function toggleMemberSelectAll() {
    const items = memberList.querySelectorAll(".dd-item");
    items.forEach((item) => {
      const checkbox = item.querySelector("input[type='checkbox']");
      if (checkbox) {
        checkbox.checked = memberSelectAll.checked;
      }
    });
  }

  function clearAllMembers() {
    const items = memberList.querySelectorAll(".dd-item");
    items.forEach((item) => {
      const checkbox = item.querySelector("input[type='checkbox']");
      if (checkbox) {
        checkbox.checked = false;
      }
    });
    memberSelectAll.checked = false;
    syncSelectedMembersFromPanel();
  }

  // Build payload and submit to backend
  async function handleSaveClick(event) {
    event.preventDefault();
    if (saveBtn.disabled) {
      return;
    }

    // Read total as the amount the backend expects
    const amountValue = getNumericValue(totalInput);

    // Base payload fields the backend expects
    const basePayload = {
      amount: amountValue,
      expense_date: dateInput.value,
      expense_type: expenseTypeSelect.value,
      description: descriptionInput.value || "",
    };

    let payload;

    if (isGroupExpense()) {
      // Group expense flow
      const splitType = getSplitTypeValue();
      const memberIds = getSelectedMemberIds();

      payload = {
        ...basePayload,
        group_id: groupSelect.value,
        member_ids: memberIds,
        split_type: splitType,
      };

      // Custom amount split for group members
      if (splitType === "amount") {
        const rows = customAmountRows.querySelectorAll("[data-member-id]");
        payload.custom_amounts = Array.from(rows).map((row) => {
          const input = row.querySelector('input[data-role="amount-input"]');
          const v = getNumericValue(input);
          return Number.isFinite(v) && v >= 0 ? v : 0;
        });
      }

      // Custom percentage split for group members
      if (splitType === "percentage") {
        const rows = customPercentageRows.querySelectorAll("[data-member-id]");
        payload.custom_percentages = Array.from(rows).map((row) => {
          const input = row.querySelector('input[data-role="percent-input"]');
          const v = getNumericValue(input);
          return Number.isFinite(v) && v >= 0 ? v : 0;
        });
      }
    } else {
      // Non group friend flow
      const friendId = friendSelect.value;
      const splitWithFriend = getFriendSplitValue();

      // Default friend share is full amount
      let friendShare = amountValue;

      if (splitWithFriend === "yes") {
        const splitType = getSplitTypeValue();

        if (splitType === "equal") {
          // Two way equal split between you and the friend
          friendShare = +(amountValue / 2).toFixed(2);
        } else if (splitType === "amount") {
          const v = getNumericValue(friendCustomAmountInput);
          if (Number.isFinite(v) && v > 0) {
            friendShare = v;
          }
        } else if (splitType === "percentage") {
          const p = getNumericValue(friendCustomPercentInput);
          if (Number.isFinite(p) && p > 0) {
            friendShare = +(amountValue * (p / 100)).toFixed(2);
          }
        }
      }

      // Backend expects a group like payload even for friend case
      payload = {
        ...basePayload,
        group_id: null,
        member_ids: [friendId],
        split_type: "amount",
        custom_amounts: [friendShare],
      };
    }

    setSaveEnabled(false, "Saving expense, please wait.");

    try {
      const resp = await fetch("/expenses/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        console.error("Save expense failed, status:", resp.status);
        setSaveEnabled(true, "Could not save expense. Try again.");
        return;
      }

      // After successful save redirect to history page
      window.location.href = "/history";
    } catch (err) {
      console.error("Error saving expense", err);
      setSaveEnabled(true, "Could not save expense. Check your connection.");
    }
  }

  // Wire up event listeners
  groupRadioYes.addEventListener("change", () => {
    updateModeVisibility();
    recalcSaveState();
  });

  groupRadioNo.addEventListener("change", () => {
    updateModeVisibility();
    recalcSaveState();
  });

  friendSplitYes.addEventListener("change", () => {
    updateModeVisibility();
    recalcSaveState();
  });

  friendSplitNo.addEventListener("change", () => {
    updateModeVisibility();
    recalcSaveState();
  });

  splitTypeRadios.forEach((radio) => {
    radio.addEventListener("change", () => {
      updateSplitDetailsVisibility();
      recalcSaveState();
    });
  });

  [dateInput, expenseTypeSelect, totalInput, descriptionInput].forEach((el) => {
    el.addEventListener("input", recalcSaveState);
    el.addEventListener("change", recalcSaveState);
  });

  friendSelect.addEventListener("change", recalcSaveState);

  friendCustomAmountInput.addEventListener("input", recalcSaveState);
  friendCustomPercentInput.addEventListener("input", recalcSaveState);

  customAmountSection.addEventListener("input", (evt) => {
    if (evt.target.matches('input[data-role="amount-input"]')) {
      recalcSaveState();
    }
  });

  customPercentageSection.addEventListener("input", (evt) => {
    if (evt.target.matches('input[data-role="percent-input"]')) {
      recalcSaveState();
    }
  });

  memberBtn.addEventListener("click", openMemberPanel);
  memberDone.addEventListener("click", () => {
    syncSelectedMembersFromPanel();
    closeMemberPanel();
  });
  memberClear.addEventListener("click", clearAllMembers);
  memberSelectAll.addEventListener("change", toggleMemberSelectAll);
  memberSearch.addEventListener("input", applyMemberSearchFilter);

  // When group changes, load its members and enable the button
  groupSelect.addEventListener("change", (e) => {
    const gid = e.target.value;
    if (!gid) {
      memberBtn.disabled = true;
      memberBtn.textContent = "Choose a group first.";
      memberList.innerHTML = "";
      memberHiddenInputs.innerHTML = "";
      groupMembersById.clear();
      rebuildCustomRows();
      recalcSaveState();
      return;
    }

    memberBtn.disabled = false;
    memberBtn.textContent = "Select members";
    closeMemberPanel();
    loadMembersFor(gid);
  });

  // Close member panel when clicking outside
  document.addEventListener("click", (evt) => {
    if (
      !memberPanel.classList.contains("hidden") &&
      !memberPanel.contains(evt.target) &&
      evt.target !== memberBtn
    ) {
      closeMemberPanel();
    }
  });

  // Final wiring
  if (saveBtn) {
    saveBtn.addEventListener("click", handleSaveClick);
  }

  // Initial state
  updateModeVisibility();
  recalcSaveState();
  loadGroups();
  loadFriends();
});
