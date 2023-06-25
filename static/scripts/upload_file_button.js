document.getElementById('cover').addEventListener('change', function() {
    var fileInput = this;
    var fileNameSpan = document.getElementById('file-name');

    if (fileInput.files.length > 0) {
        fileNameSpan.textContent = fileInput.files[0].name;
        fileNameSpan.style.display = 'inline';
    } else {
        fileNameSpan.textContent = 'Файл не выбран';
        fileNameSpan.style.display = 'none';
    }
});