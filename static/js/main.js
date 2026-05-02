document.addEventListener('click', function (e) {
    const toggler = e.target.closest('.dropdown-toggle');
    const dropdown = e.target.closest('.dropdown');

    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        if (!dropdown || !dropdown.contains(menu)) {
        menu.classList.remove('show');
        }
    });

    if (toggler && dropdown) {
        const menu = dropdown.querySelector('.dropdown-menu');
        menu.classList.toggle('show');
        e.preventDefault();
    }
});

    function toggleMenu() {
    const leftWindow = document.querySelector('.left-window');
    leftWindow.classList.toggle('mobile-active');
}

document.addEventListener("DOMContentLoaded", () => {
    const menuToggle = document.querySelector(".navbar-menu-toggle");
    const mobileMenu = document.getElementById("mobile-navbar-buttons");

    if (menuToggle && mobileMenu) {
        menuToggle.addEventListener("click", (e) => {
            e.stopPropagation();
            mobileMenu.classList.toggle("show");
        });

        document.addEventListener("click", (e) => {
            const target = e.target;
            const clickedOutside = !mobileMenu.contains(target) && !menuToggle.contains(target);

            if (clickedOutside && mobileMenu.classList.contains("show")) {
                mobileMenu.classList.remove("show");
            }
        });
    }
});