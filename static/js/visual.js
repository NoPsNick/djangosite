const themeToggle = document.getElementById('theme-toggle');
const themeIcon = document.getElementById('themeIcon');
const body = document.body;

// Define o tema inicial
if (localStorage.getItem('theme') === 'dark') {
    body.classList.add('dark-mode');
    body.classList.remove('light-mode');
    themeToggle.innerHTML = '<i id="themeIcon" class="bi bi-moon-fill"></i> > ' +
        '<i id="themeIcon" class="bi bi-sun"></i>';
} else {
    body.classList.add('light-mode');
    themeToggle.innerHTML = '<i id="themeIcon" class="bi bi-sun"></i> > ' +
        '<i id="themeIcon" class="bi bi-moon-fill"></i>';
}

// Atualiza o localStorage e alterna o tema ao clicar no botão
themeToggle.addEventListener('click', () => {
    body.classList.toggle('dark-mode');
    body.classList.toggle('light-mode');

    if (body.classList.contains('dark-mode')) {
        localStorage.setItem('theme', 'dark');
        themeToggle.innerHTML = '<i id="themeIcon" class="bi bi-moon-fill"></i> > ' +
            '<i id="themeIcon" class="bi bi-sun"></i>';
    } else {
        localStorage.setItem('theme', 'light');
        themeToggle.innerHTML = '<i id="themeIcon" class="bi bi-sun"></i> > ' +
            '<i id="themeIcon" class="bi bi-moon-fill"></i>';
    }
});