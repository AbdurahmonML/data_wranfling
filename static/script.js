// Function to fetch films from the backend API with search and sort parameters
async function fetchFilms() {
    const searchTerm = document.getElementById('search').value;
    const sortBy = document.getElementById('sort').value;
    const order = document.getElementById('order').value;

    const response = await fetch(`/api/films?search=${searchTerm}&sort=${sortBy}&order=${order}`);
    const films = await response.json();
    renderFilms(films);
}

// Function to render films in the table
function renderFilms(filmsArray) {
    const tbody = document.querySelector("#film-table tbody");
    tbody.innerHTML = ""; // Clear existing rows

    filmsArray.forEach(film => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${film.title}</td>
            <td>${film.directors}</td>
            <td>${film.year}</td>
            <td>${film.revenue}</td>
            <td>${film.country}</td>
        `;
        tbody.appendChild(row);
    });
}

// Function to handle the search action
function searchFilms() {
    fetchFilms();
}

// Function to handle sorting change
function sortFilms() {
    fetchFilms();
}

// Initial render (if you have an API)
document.addEventListener("DOMContentLoaded", function() {
    fetchFilms();
});
