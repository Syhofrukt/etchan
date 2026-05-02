document.addEventListener("DOMContentLoaded", () => {
    const langToggle = document.getElementById("lang-toggle");
    const langToggleMobile = document.getElementById("lang-toggle-mobile");

    let currentLang = getCookie("Language") || "EN";

    if (langToggle) langToggle.textContent = currentLang;
    if (langToggleMobile) langToggleMobile.textContent = currentLang;

    function setCookie(name, value, days = 365) {
        const date = new Date();
        date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
        const expires = "expires=" + date.toUTCString();
        document.cookie = `${name}=${value}; ${expires}; path=/`;
    }

    function getCookie(name) {
        const nameEQ = name + "=";
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            let c = cookies[i].trim();
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length);
        }
        return null;
    }

    function setText(selector, value, isPlaceholder = false) {
        const el = document.querySelector(selector);
        if (el && value) {
            if (isPlaceholder) el.placeholder = value;
            else el.textContent = value;
        }
    }

    function loadLanguage(lang) {
        fetch(`/static/js/lang/${lang}.json`)
            .then((res) => res.json())
            .then((data) => {
                document.querySelectorAll("[data-i18n]").forEach((el) => {
                    const key = el.getAttribute("data-i18n");
                    if (data[key]) el.textContent = data[key];
                });

                document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
                    const key = el.getAttribute("data-i18n-placeholder");
                    if (data[key]) el.setAttribute("placeholder", data[key]);
                });

                setText("#login-button", data.login);
                setText("#logout-button", data.logout);
                setText("#registration-button", data.signup);
                setText("#send-button", data.send);
                setText("#messageText", data.messageText, true);
                setText("input[placeholder]", data.search_placeholder, true);
                setText("label[for='list']", data.select_topic);
                setText("label[for='title']", data.title);
                setText("label[for='post-editor']", data.description);
                setText("#avatarText", data.upload_media);
                setText("label[for='tag']", data.tag);
                setText("#bannerText", data.banner);
                setText("#errorFriends", data.errorFriends);

                const links = document.querySelectorAll("a");
                links.forEach((link) => {
                    switch (link.getAttribute("href")) {
                        case "/me":
                            if (data.profile) link.textContent = data.profile;
                            break;
                        case "/friends":
                            if (data.friends) link.textContent = data.friends;
                            break;
                        case "/notifications":
                            if (data.notifications) link.textContent = data.notifications;
                            break;
                        case "/threads":
                            if (data.threads) link.textContent = data.threads;
                            break;
                        case "/thread-create":
                            if (data.create_thread) link.textContent = data.create_thread;
                            break;
                        case "/leaderboard":
                            if (data.leaderboard) link.textContent = data.leaderboard;
                            break;
                    }
                });

                setText(".right-window-title h3", data.advertisement);
            })
            .catch((err) => {
                console.error("Ошибка загрузки языка:", err);
            });
    }

    loadLanguage(currentLang);

    if (langToggle) {
        langToggle.addEventListener("click", () => {
            currentLang = currentLang === "EN" ? "UK" : "EN";
            langToggle.textContent = currentLang;
            if (langToggleMobile) langToggleMobile.textContent = currentLang;
            loadLanguage(currentLang);
            setCookie("Language", currentLang);
        });
    }

    if (langToggleMobile) {
        langToggleMobile.addEventListener("click", () => {
            currentLang = currentLang === "EN" ? "UK" : "EN";
            langToggleMobile.textContent = currentLang;
            if (langToggle) langToggle.textContent = currentLang;
            loadLanguage(currentLang);
            setCookie("Language", currentLang);
        });
    }
});
