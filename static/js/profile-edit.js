document.addEventListener("DOMContentLoaded", function () {
    const titleInput = document.getElementById("title");
    const descInput = document.getElementById("post-editor");
    const countResult = document.getElementById("count-result");
    const countResultDesc = document.getElementById("desc-count-result");
    const maxLength = 20;
    const maxLengthDesc = 150;

    function autoResizeInput(input) {
        input.style.height = "auto";
        input.style.height = input.scrollHeight + "px";
    }

    function resetHeight(input, minHeight) {
        input.style.height = minHeight;
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

    descInput.addEventListener("input", function () {
        autoResizeInput(descInput);
        enforceMaxLength(descInput, maxLengthDesc);
        updateCharCount(descInput, countResultDesc, maxLengthDesc);
    });

    descInput.addEventListener("input", function () {
        autoResizeInput(descInput);
    });
    
    titleInput.addEventListener("blur", function () {
        resetHeight(titleInput, "70px");
    });
    
    descInput.addEventListener("blur", function () {
        resetHeight(descInput, "100px");
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
