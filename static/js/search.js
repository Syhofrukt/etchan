document.addEventListener("DOMContentLoaded", () => {
    const input = document.querySelector(".search-box input");
    const filter = document.querySelector(".search-filter");
    const resultsContainer = document.getElementById("search-results");
    const socket = new WebSocket("wss://" + window.location.host + "/ws/search");

    input.addEventListener("keydown", async (e) => {
        if (e.key === "Enter") {
            e.preventDefault();

            const query = input.value.trim();
            const category = filter.value;

            if (!query) {
                input.placeholder = " Please input search query";
                return;
            }

            const formData = new FormData();
            formData.append("query", query);
            formData.append("category", category);

            await fetch("/get_search_results", {
                method: "POST",
                body: formData
            });

            socket.send("search");
        }
    });

    socket.onmessage = async (event) => {
        if (event.data === "search_complete") {
            fetchSearchResults();
        }
    };

    async function fetchSearchResults() {
        const query = input.value.trim();
        const category = filter.value;

        const formData = new FormData();
        formData.append("query", query);
        formData.append("category", category);

        const response = await fetch("/get_search_results", {
            method: "POST",
            body: formData
        });

        const html = await response.text();
        resultsContainer.innerHTML = html;
        
        resultsContainer.classList.add("active");
    }

    input.addEventListener("focus", () => {
        filter.classList.add("active");
    });

    document.addEventListener("click", (e) => {
        const container = document.querySelector(".search-container");
        if (!container.contains(e.target)) {
            filter.classList.remove("active");
            resultsContainer.classList.remove("active");
            input.placeholder = " Search";
        }
    });
});