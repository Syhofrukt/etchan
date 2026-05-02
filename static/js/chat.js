document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file-upload');
    const previewBox = document.getElementById('preview-box');
    const previewImage = document.getElementById('preview-image');
    const removeBtn = document.getElementById('remove-btn');
    const uploadIcon = document.getElementById('upload-icon');

    let fileChosen = false;
    let previewVisible = false;
    let savedFile = null;


    fileInput.addEventListener('change', function() {
        if (fileInput.files && fileInput.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                fileChosen = true;
                previewVisible = true;
                savedFile = fileInput.files[0];
                previewBox.style.display = 'block';
            };
            reader.readAsDataURL(fileInput.files[0]);
        }
    });

    uploadIcon.addEventListener('click', function(e) {
        e.preventDefault();

        if (fileChosen) {
            previewVisible = !previewVisible;
            previewBox.style.display = previewVisible ? 'block' : 'none';
        } else {
            fileInput.click();
        }
    });

    removeBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        previewBox.style.display = 'none';
        previewVisible = false;
    });

    removeBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        previewBox.style.display = 'none';
        previewVisible = false;
        fileInput.value = '';
        fileChosen = false;
        savedFile = null;
    });
    
});
