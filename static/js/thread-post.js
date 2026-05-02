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
    }
});