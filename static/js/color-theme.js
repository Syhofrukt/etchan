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

function applySavedTheme() {
    const savedTheme = getCookie("Color_Theme") || "dark";
    document.body.classList.remove("light-theme", "dark-theme");
    document.body.classList.add(`${savedTheme}-theme`);
}

function toggleTheme() {
    const isCurrentlyLight = document.body.classList.contains("light-theme");
    const newTheme = isCurrentlyLight ? "dark" : "light";
    document.body.classList.remove("light-theme", "dark-theme");
    document.body.classList.add(`${newTheme}-theme`);
    setCookie("Color_Theme", newTheme);
}

document.addEventListener("DOMContentLoaded", () => {
    applySavedTheme();

    const themeButtonIds = ["theme-toggle", "theme-toggle-mobile"];

    themeButtonIds.forEach(id => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener("click", toggleTheme);
        }
    });
});
