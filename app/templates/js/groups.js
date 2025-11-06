import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm";

const supabaseUrl = "https://YOUR_SUPABASE_URL";
const supabaseKey = "YOUR_SUPABASE_ANON_KEY";
const supabase = createClient(supabaseUrl, supabaseKey);

const groupsList = document.getElementById("groups-list");
const createForm = document.getElementById("create-group-form");

async function loadGroups() {
  const { data, error } = await supabase.from("groups").select("*");
  if (error) {
    console.error(error);
    groupsList.innerHTML = "<li>Error loading groups</li>";
    return;
  }

  groupsList.innerHTML = "";
  data.forEach(g => {
    const li = document.createElement("li");
    li.textContent = g.name;
    groupsList.appendChild(li);
  });
}

createForm.addEventListener("submit", async e => {
  e.preventDefault();
  const name = document.getElementById("group-name").value;
  const description = document.getElementById("group-description").value;

  const { data, error } = await supabase.from("groups").insert([{ name, description }]);
  if (error) {
    alert("Error creating group");
    console.error(error);
  } else {
    loadGroups();
    createForm.reset();
  }
});

loadGroups();
