document.addEventListener("DOMContentLoaded", function () {
    const loginButton = document.getElementById("login-button");
    const logoutButton = document.getElementById("logout-button");
    const logoutButtonMobile = document.getElementById("logout-button-mobile");
    const loginForm = document.querySelector(".popup-login form");
    const popup = document.querySelector(".popup-login");
    const closeButton = document.querySelector(".close-button");
    const registrationButton = document.getElementById("registration-button");


    
    document.querySelectorAll("input").forEach(function (input) {
        input.setAttribute("autocomplete", "off");
    });


    function openPopup() {
        popup.classList.add("active");
    }

    function closePopup() {
        popup.classList.remove("active");
    }

    loginButton.addEventListener("click", function (event) {
        event.stopPropagation();
        openPopup();
    });

    closeButton.addEventListener("click", function (event) {
        event.stopPropagation();
        closePopup();
    });

    loginForm.addEventListener("submit", function (event) {
        loginButton.style.display = "none";
        logoutButton.style.display = "inline-block";
        logoutButton.style.display = "inline-block";

        if (registrationButton) {
            registrationButton.style.display = "none";
        }

        closePopup();
    });

    logoutButton.addEventListener("click", function () {
        logoutButton.style.display = "none";
        logoutButtonMobile.style.display = "none";
        loginButton.style.display = "inline-block";

        if (registrationButton) {
            registrationButton.style.display = "inline-block";
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closePopup();
        }
    });
});
