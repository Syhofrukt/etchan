document.addEventListener("DOMContentLoaded", function () {
    const titleInput = document.getElementById("title");
    const textarea = document.getElementById("post-editor");
    const countResult = document.getElementById("count-result");
    const maxLength = 20;

    const tagInput = document.getElementById("tag");
    const tagCountResult = document.getElementById("tag-count-result");

    function autoResizeInput(input) {
        input.style.height = "auto";
        input.style.height = input.scrollHeight + "px";
    }

    function updateCharCount(input, countElement, maxLength) {
        const length = input.value.length;
        countElement.textContent = `${length}/${maxLength}`;
        

        if (length >= maxLength) {

            countElement.style.color = 'red';

        }

        if (length < maxLength) {

            countElement.style.color = '#d0d0d0';

        }
        
    }

    function enforceMaxLength(input, maxLength) {
        if (input.value.length > maxLength) {
            input.value = input.value.substring(0, maxLength);
        }
    }

    titleInput.addEventListener("input", function () {
        autoResizeInput(titleInput);
        enforceMaxLength(titleInput, maxLength);
        updateCharCount(titleInput, countResult, maxLength);
    });

    tagInput.addEventListener("input", function () {
        enforceMaxLength(tagInput, maxLength);
        updateCharCount(tagInput, tagCountResult, maxLength);
    });

    titleInput.addEventListener("blur", function () {
        titleInput.style.height = "70px";
    });

    textarea.addEventListener("input", function () {
        autoResizeInput(textarea);
    });

    textarea.addEventListener("blur", function () {
        textarea.style.height = "100px";
    });
});



function previewImage(event, type) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            let previewImg = document.getElementById(type + "Preview");
            let text = document.getElementById(type + "Text");

            previewImg.src = e.target.result;
            previewImg.classList.remove("hidden");
            text.classList.add("hidden");
        };
        reader.readAsDataURL(file);
    }
}