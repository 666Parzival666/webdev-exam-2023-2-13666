function deleteBookModal(bookId) {
    const deleteModal = document.getElementById('deleteModal');
    const deleteYesBtn = document.getElementById('deleteYesBtn');
    const deleteNoBtn = document.getElementById('deleteNoBtn');

    deleteModal.style.display = 'flex';

    deleteNoBtn.addEventListener('click', () => {
        deleteModal.style.display = 'none';
    });

    deleteYesBtn.addEventListener('click', () => {
        deleteModal.style.display = 'none';
        deleteBook(bookId);
    });
}

function deleteBook(bookId) {
    fetch(`/delete_book/${bookId}`, { method: 'POST' })
        .then(response => {
            if (response.ok) {
                // Успешно удалено
                window.location.reload();
            } else {
                throw new Error('Ошибка при удалении книги');
            }
        })
        .catch(error => {
            console.error('Ошибка при удалении книги:', error);
        });
}

// Добавляем обработчик ошибок для отображения в консоли
window.addEventListener('error', function (event) {
    console.error('Произошла ошибка:', event.error);
});