const bookTitles = document.querySelectorAll('.book-title');
  bookTitles.forEach((title) => {
    const fullTitle = title.dataset.fullTitle;
    const shortTitle = (fullTitle.length > 25) ? fullTitle.slice(0, 25) + '...' : fullTitle;
    title.textContent = shortTitle;

    title.addEventListener('mouseover', () => {
      title.textContent = fullTitle;
    });

    title.addEventListener('mouseout', () => {
      title.textContent = shortTitle;
    });
  });