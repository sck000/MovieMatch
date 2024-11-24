from flask import Flask, render_template, request, jsonify
from models.movie import Movie, db
import numpy as np
import requests
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from collections import defaultdict
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

TMDB_API_KEY = os.getenv('VITE_TMDB_API_KEY')
TMDB_ACCESS_TOKEN = os.getenv('VITE_TMDB_ACCESS_TOKEN')
TMDB_BASE_URL = "https://api.themoviedb.org/3"

db.init_app(app)

def fetch_tmdb_data(url, headers, params=None):
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data from {url}: {str(e)}")
        return None

def get_movie_details(movie_id, headers):
    details_url = f"{TMDB_BASE_URL}/movie/{movie_id}"
    params = {
        "append_to_response": "credits,keywords,reviews,recommendations,similar"
    }
    return fetch_tmdb_data(details_url, headers, params)

def get_movies_by_collection(collection_id, headers):
    collection_url = f"{TMDB_BASE_URL}/collection/{collection_id}"
    return fetch_tmdb_data(collection_url, headers)

def get_director_movies(director_id, headers):
    person_url = f"{TMDB_BASE_URL}/person/{director_id}/movie_credits"
    return fetch_tmdb_data(person_url, headers)

def calculate_similarity(movie1, movie2, weights):
    base_score = 0
    bonus_score = 0

    # Genre similarity (30%)
    if 'genres' in movie1 and 'genres' in movie2:
        genres1 = set(g['id'] for g in movie1['genres'])
        genres2 = set(g['id'] for g in movie2['genres'])
        if genres1 and genres2:
            genre_similarity = len(genres1 & genres2) / len(genres1 | genres2)
            base_score += weights['genre'] * (0.5 + 0.5 * genre_similarity) * 100

    # Keywords similarity (25%)
    keywords1 = set(k['id'] for k in movie1.get('keywords', {}).get('keywords', []))
    keywords2 = set(k['id'] for k in movie2.get('keywords', {}).get('keywords', []))
    if keywords1 and keywords2:
        keyword_similarity = len(keywords1 & keywords2) / len(keywords1 | keywords2)
        base_score += weights['keywords'] * (0.4 + 0.6 * keyword_similarity) * 100

    # Cast similarity (15%)
    cast1 = set(c['id'] for c in movie1['credits']['cast'][:5])
    cast2 = set(c['id'] for c in movie2['credits']['cast'][:5])
    if cast1 and cast2:
        cast_similarity = len(cast1 & cast2) / len(cast1 | cast2)
        base_score += weights['cast'] * (0.3 + 0.7 * cast_similarity) * 100

    # Director similarity (15%)
    director1 = next((c['id'] for c in movie1['credits']['crew'] if c['job'] == 'Director'), None)
    director2 = next((c['id'] for c in movie2['credits']['crew'] if c['job'] == 'Director'), None)
    if director1 and director2:
        director_similarity = 1 if director1 == director2 else 0
        base_score += weights['director'] * director_similarity * 100
        if director_similarity == 1:
            bonus_score += 10  # Bonus for same director

    # Release year similarity (10%)
    year1 = int(movie1['release_date'][:4]) if movie1.get('release_date') else None
    year2 = int(movie2['release_date'][:4]) if movie2.get('release_date') else None
    if year1 is not None and year2 is not None:
        year_diff = abs(year1 - year2)
        year_similarity = max(0, 10 - year_diff) / 10
        base_score += weights['year'] * (0.5 + 0.5 * year_similarity) * 100

    # Rating similarity (5%)
    rating1 = movie1.get('vote_average')
    rating2 = movie2.get('vote_average')
    if rating1 is not None and rating2 is not None:
        rating_diff = abs(rating1 - rating2)
        rating_similarity = max(0, 10 - rating_diff) / 10
        base_score += weights['rating'] * (0.4 + 0.6 * rating_similarity) * 100

    # Add source bonuses (normalized to contribute max 20 points)
    if movie2.get('source_bonus'):
        bonus_score += min(20, movie2['source_bonus'])

    # Add recency bonus (normalized to contribute max 10 points)
    from datetime import datetime
    current_year = datetime.now().year
    movie2_year = int(movie2['release_date'][:4]) if movie2.get('release_date') else current_year
    years_from_now = current_year - movie2_year
    recency_bonus = max(0, 10 - (years_from_now * 0.5))
    bonus_score += min(10, recency_bonus)

    # Add base similarity score (20 points)
    base_score += 20

    # Normalize final score to 0-100 range
    # Base score is 80% of total, bonus is 20% of total
    normalized_base = min(80, base_score * 0.8)
    normalized_bonus = min(20, bonus_score)
    
    final_score = normalized_base + normalized_bonus
    return min(100, max(0, final_score))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/api/search', methods=['POST'])
def search_movies():
    try:
        movie_title = request.json.get('title')
        if not movie_title:
            return jsonify({'error': 'Movie title is required'}), 400

        headers = {
            "Authorization": f"Bearer {TMDB_ACCESS_TOKEN}",
            "accept": "application/json"
        }

        # 1. Search for the base movie
        search_url = f"{TMDB_BASE_URL}/search/movie"
        search_results = fetch_tmdb_data(search_url, headers, {
            "query": movie_title,
            "include_adult": False,
            "language": "en-US",
            "page": 1
        })

        if not search_results or not search_results.get('results'):
            return jsonify({'error': 'Movie not found'}), 404

        base_movie = search_results['results'][0]
        base_movie_id = base_movie['id']

        # 2. Get detailed information about the base movie
        base_movie_details = get_movie_details(base_movie_id, headers)
        if not base_movie_details:
            return jsonify({'error': 'Failed to fetch movie details'}), 500

        # 3. Collect candidate movies from multiple sources
        candidate_movies = defaultdict(lambda: {'movie': None, 'sources': set()})

        # 3.1 Add movies from the same collection (franchise)
        if base_movie_details.get('belongs_to_collection'):
            collection_data = get_movies_by_collection(
                base_movie_details['belongs_to_collection']['id'], 
                headers
            )
            if collection_data and 'parts' in collection_data:
                for movie in collection_data['parts']:
                    candidate_movies[movie['id']]['movie'] = movie
                    candidate_movies[movie['id']]['sources'].add('collection')

        # 3.2 Add movies from the same director (limited to top 5 by rating)
        director = next((crew for crew in base_movie_details.get('credits', {}).get('crew', [])
                       if crew['job'] == 'Director'), None)
        if director:
            director_movies = get_director_movies(director['id'], headers)
            if director_movies and 'crew' in director_movies:
                # Filter only directing credits and sort by vote_average
                directed_movies = [
                    movie for movie in director_movies['crew']
                    if movie['job'] == 'Director' and movie.get('vote_average') is not None
                ]
                directed_movies.sort(key=lambda x: x.get('vote_average', 0), reverse=True)
                
                # Take only top 5 rated movies
                for movie in directed_movies[:5]:
                    candidate_movies[movie['id']]['movie'] = movie
                    candidate_movies[movie['id']]['sources'].add('director')

        # 3.3 Add similar movies (increased number)
        if 'similar' in base_movie_details and 'results' in base_movie_details['similar']:
            for movie in base_movie_details['similar']['results'][:15]:  # Increased from default
                candidate_movies[movie['id']]['movie'] = movie
                candidate_movies[movie['id']]['sources'].add('similar')

        # 3.4 Add recommended movies (increased number)
        if 'recommendations' in base_movie_details and 'results' in base_movie_details['recommendations']:
            for movie in base_movie_details['recommendations']['results'][:15]:  # Increased from default
                candidate_movies[movie['id']]['movie'] = movie
                candidate_movies[movie['id']]['sources'].add('recommendations')

        # 4. Get detailed information for all candidate movies
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_movie = {
                executor.submit(get_movie_details, movie_id, headers): (movie_id, data)
                for movie_id, data in candidate_movies.items()
                if movie_id != base_movie_id
            }

            detailed_candidates = []
            for future in future_to_movie:
                movie_id, data = future_to_movie[future]
                try:
                    movie_details = future.result()
                    if movie_details:
                        detailed_candidates.append({
                            'details': movie_details,
                            'sources': data['sources']
                        })
                except Exception as e:
                    print(f"Error processing movie {movie_id}: {str(e)}")

        # 5. Calculate similarity scores and process results
        processed_movies = []
        base_genres = {genre['id'] for genre in base_movie_details.get('genres', [])}
        base_keywords = {kw['id'] for kw in base_movie_details.get('keywords', {}).get('keywords', [])}
        base_cast = {cast['id'] for cast in base_movie_details.get('credits', {}).get('cast', [])[:5]}
        base_director = next((crew['id'] for crew in base_movie_details.get('credits', {}).get('crew', [])
                            if crew['job'] == 'Director'), None)
        base_year = int(base_movie_details['release_date'][:4]) if base_movie_details.get('release_date') else None

        # Get current date for release date comparison
        from datetime import datetime
        current_date = datetime.now().strftime('%Y-%m-%d')

        weights = {
            'genre': 0.32,      # Increased from 30%
            'keywords': 0.27,   # Increased from 25%
            'cast': 0.17,       # Increased from 15%
            'director': 0.08,   # Decreased from 15%
            'year': 0.11,       # Increased from 10%
            'rating': 0.05      # Maintained at 5%
        }

        source_bonuses = {
            'collection': 20,   # Same franchise bonus
            'director': 10,     # Reduced from 15 to match new weight
            'similar': 10,      # TMDB similar movies bonus
            'recommendations': 5  # TMDB recommendations bonus
        }

        for candidate in detailed_candidates:
            movie = candidate['details']
            sources = candidate['sources']
            
            # Skip movies that haven't been released yet
            if movie.get('release_date') and movie['release_date'] > current_date:
                continue

            score = calculate_similarity(base_movie_details, movie, weights)

            # Add source bonuses
            for source in sources:
                movie['source_bonus'] = source_bonuses.get(source, 0)

            # Add recency bonus (favor newer movies)
            from datetime import datetime
            current_year = datetime.now().year
            movie_year = int(movie['release_date'][:4]) if movie.get('release_date') else current_year
            years_from_now = current_year - movie_year
            recency_bonus = max(0, 10 - (years_from_now * 0.5))  # Increased bonus points for newer movies
            movie['recency_bonus'] = recency_bonus

            if score >= 40:  # Increased threshold for better quality
                processed_movies.append({
                    'id': movie['id'],
                    'title': movie['title'],
                    'year': int(movie['release_date'][:4]) if movie.get('release_date') else None,
                    'similarity_score': score,
                    'genre': [genre['name'] for genre in movie.get('genres', [])],
                    'director': next((crew['name'] for crew in movie.get('credits', {}).get('crew', [])
                                   if crew['job'] == 'Director'), 'Unknown'),
                    'rating': round(movie['vote_average'], 1),
                    'reviews': process_reviews(movie.get('reviews', {}).get('results', [])),
                    'poster_path': movie['poster_path'],
                    'overview': movie['overview']
                })

        # Sort by similarity score
        processed_movies.sort(key=lambda x: x['similarity_score'], reverse=True)
        return jsonify(processed_movies[:20])  # Return top 20 movies

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def process_reviews(reviews):
    processed = []
    for review in reviews[:3]:
        processed.append({
            'text': review.get('content', '')[:200] + '...',
            'rating': review.get('author_details', {}).get('rating', 0)
        })
    return processed

@app.context_processor
def inject_year():
    return {'year': datetime.now().year}

@app.route('/movie/<int:movie_id>')
def movie_details(movie_id):
    try:
        headers = {
            "Authorization": f"Bearer {TMDB_ACCESS_TOKEN}",
            "accept": "application/json"
        }
        
        # Get detailed movie information
        movie_details = get_movie_details(movie_id, headers)
        if not movie_details:
            return render_template('error.html', message='Movie not found'), 404

        # Process cast (limit to top 10)
        cast = movie_details.get('credits', {}).get('cast', [])[:10]
        
        # Process crew (get director and key roles)
        crew = movie_details.get('credits', {}).get('crew', [])
        director = next((member for member in crew if member['job'] == 'Director'), None)
        key_crew = [member for member in crew if member['job'] in ['Director', 'Writer', 'Producer', 'Cinematographer']][:5]
        
        # Process reviews
        reviews = movie_details.get('reviews', {}).get('results', [])
        processed_reviews = []
        for review in reviews:
            processed_reviews.append({
                'author': review.get('author', 'Anonymous'),
                'content': review.get('content', ''),
                'rating': review.get('author_details', {}).get('rating'),
                'created_at': review.get('created_at', '').split('T')[0]
            })

        # Get collection info if movie is part of a collection
        collection = None
        if movie_details.get('belongs_to_collection'):
            collection_data = get_movies_by_collection(
                movie_details['belongs_to_collection']['id'],
                headers
            )
            if collection_data:
                collection = {
                    'name': collection_data.get('name'),
                    'movies': sorted(collection_data.get('parts', []), key=lambda x: x.get('release_date', ''))
                }

        return render_template('movie_details.html',
                             movie=movie_details,
                             cast=cast,
                             director=director,
                             key_crew=key_crew,
                             reviews=processed_reviews[:5],
                             collection=collection)
    except Exception as e:
        print(f"Error fetching movie details: {str(e)}")
        return render_template('error.html', message='Failed to load movie details'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
