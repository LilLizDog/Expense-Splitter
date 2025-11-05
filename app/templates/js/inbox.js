document.addEventListener("DOMContentLoaded", async () => {
    const searchInput = document.getElementById("searchInput");
    const threadList = document.getElementById("threadList");

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

    loadThreads();
});
