let currentPage = 1;
const resultsPerPage = 10;
let allMovies = [];

document.addEventListener('DOMContentLoaded', () => {
    const searchBtn = document.getElementById('searchBtn');
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    const movieSearch = document.getElementById('movieSearch');
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');

    // Mobile menu toggle
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            const icon = mobileMenuBtn.querySelector('i');
            icon.classList.toggle('fa-bars');
            icon.classList.toggle('fa-times');
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!mobileMenuBtn.contains(e.target) && !navLinks.contains(e.target) && navLinks.classList.contains('active')) {
                navLinks.classList.remove('active');
                const icon = mobileMenuBtn.querySelector('i');
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
    }

    searchBtn.addEventListener('click', searchMovies);

    movieSearch.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchMovies();
        }
    });

    loadMoreBtn.addEventListener('click', loadMore);
});

function searchMovies() {
    const movieTitle = document.getElementById('movieSearch').value;
    if (!movieTitle) return;

    // Show loading indicator and results section
    document.getElementById('loadingIndicator').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'block';
    document.getElementById('movieResults').innerHTML = '';
    document.getElementById('loadMoreBtn').style.display = 'none';

    fetch('/api/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            title: movieTitle
        })
    })
    .then(response => response.json())
    .then(data => {
        // Hide loading indicator
        document.getElementById('loadingIndicator').style.display = 'none';
        
        allMovies = data;
        currentPage = 1;
        displayMovies();
        updateLoadMoreButton();
    })
    .catch(error => {
        // Hide loading indicator and show error
        document.getElementById('loadingIndicator').style.display = 'none';
        console.error('Error:', error);
        document.getElementById('movieResults').innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                <p>Error fetching movie recommendations</p>
            </div>
        `;
    });
}

function displayMovies() {
    const startIdx = (currentPage - 1) * resultsPerPage;
    const endIdx = startIdx + resultsPerPage;
    const moviesToShow = allMovies.slice(startIdx, endIdx);

    const resultsContainer = document.getElementById('movieResults');
    
    if (currentPage === 1) {
        resultsContainer.innerHTML = '';
    }

    moviesToShow.forEach((movie, index) => {
        const movieCard = createMovieCard(movie);
        movieCard.style.animationDelay = `${index * 0.1}s`;
        resultsContainer.appendChild(movieCard);
    });
}

function createMovieCard(movie) {
    const card = document.createElement('div');
    card.className = 'movie-card';
    
    console.log('Raw similarity score:', movie.similarity_score);
    const similarityScore = Math.round(movie.similarity_score * 100);
    console.log('Calculated similarity:', similarityScore);
    const displayScore = Math.max(0, Math.min(100, similarityScore));
    const posterUrl = movie.poster_path 
        ? `https://image.tmdb.org/t/p/w500${movie.poster_path}`
        : '/static/images/no-poster.png';

    const releaseYear = movie.release_date ? movie.release_date.substring(0, 4) : 'N/A';
    const rating = movie.vote_average ? movie.vote_average.toFixed(1) : 'N/A';
    const runtime = movie.runtime ? `${movie.runtime} min` : 'N/A';
    const overview = movie.overview 
        ? (movie.overview.length > 200 ? movie.overview.substring(0, 200) + '...' : movie.overview)
        : 'No overview available.';

    card.innerHTML = `
        <div class="movie-poster">
            <img src="${posterUrl}" alt="${movie.title} poster">
            <div class="similarity-score">
                <span>${displayScore}%</span>
                <small>Match</small>
            </div>
        </div>
        <div class="movie-info">
            <h3>${movie.title}</h3>
            <div class="movie-meta">
                <span class="year">${releaseYear}</span>
                <span class="runtime">${runtime}</span>
                <span class="rating">
                    <i class="fas fa-star"></i>
                    ${rating}
                </span>
            </div>
            <p class="overview">${overview}</p>
            <div class="movie-actions">
                <a href="/movie/${movie.id}" class="details-btn">
                    <i class="fas fa-info-circle"></i>
                    Details
                </a>
            </div>
        </div>
    `;
    
    return card;
}

function getSimilarityColor(score) {
    if (score >= 80) return '#22c55e';  // Green
    if (score >= 60) return '#3b82f6';  // Blue
    if (score >= 40) return '#f59e0b';  // Orange
    return '#ef4444';  // Red
}

function createReviewsSection(reviews) {
    if (!reviews || reviews.length === 0) return '';

    let reviewsHtml = '<div class="movie-reviews"><h4>Reviews</h4>';
    reviews.forEach(review => {
        reviewsHtml += `
            <div class="review">
                <p>${review.text}</p>
                ${review.rating ? `<small>Rating: ${review.rating}/10</small>` : ''}
            </div>
        `;
    });
    reviewsHtml += '</div>';
    return reviewsHtml;
}

function loadMore() {
    currentPage++;
    displayMovies();
    updateLoadMoreButton();
}

function updateLoadMoreButton() {
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    const hasMoreMovies = currentPage * resultsPerPage < allMovies.length;
    loadMoreBtn.style.display = hasMoreMovies ? 'block' : 'none';
}
