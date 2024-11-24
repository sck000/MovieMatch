from app import app, db
from models.movie import Movie

# Sample movie data
movies = [
    {
        'title': 'Inception',
        'year': 2010,
        'genre': ['Sci-Fi', 'Action', 'Thriller'],
        'themes': ['Dreams', 'Reality', 'Memory', 'Time'],
        'cast': ['Leonardo DiCaprio', 'Joseph Gordon-Levitt', 'Ellen Page'],
        'director': 'Christopher Nolan',
        'plot': 'A thief who enters the dreams of others to steal secrets from their subconscious.',
        'rating': 8.8,
        'reviews': [
            {'text': 'A mind-bending masterpiece', 'rating': 9.0},
            {'text': 'Visually stunning and intellectually challenging', 'rating': 8.5},
            {'text': 'Complex but rewarding', 'rating': 8.0}
        ],
        'soundtrack': ['Time', 'Dream is Collapsing', 'We Built Our Own World']
    },
    {
        'title': 'Interstellar',
        'year': 2014,
        'genre': ['Sci-Fi', 'Drama', 'Adventure'],
        'themes': ['Space', 'Time', 'Family', 'Survival'],
        'cast': ['Matthew McConaughey', 'Anne Hathaway', 'Jessica Chastain'],
        'director': 'Christopher Nolan',
        'plot': 'A team of explorers travel through a wormhole in space to ensure humanity\'s survival.',
        'rating': 8.6,
        'reviews': [
            {'text': 'An emotional journey through space and time', 'rating': 9.0},
            {'text': 'Spectacular visuals and moving story', 'rating': 8.5},
            {'text': 'Amazing soundtrack and cinematography', 'rating': 8.8}
        ],
        'soundtrack': ['Mountains', 'Stay', 'No Time for Caution']
    },
    {
        'title': 'The Matrix',
        'year': 1999,
        'genre': ['Sci-Fi', 'Action'],
        'themes': ['Reality', 'Technology', 'Freedom', 'Identity'],
        'cast': ['Keanu Reeves', 'Laurence Fishburne', 'Carrie-Anne Moss'],
        'director': 'Lana and Lilly Wachowski',
        'plot': 'A computer programmer discovers that reality as he knows it is a simulation.',
        'rating': 8.7,
        'reviews': [
            {'text': 'Revolutionary sci-fi that changed the genre', 'rating': 9.0},
            {'text': 'Groundbreaking special effects', 'rating': 8.5},
            {'text': 'Perfect blend of action and philosophy', 'rating': 8.8}
        ],
        'soundtrack': ['Wake Up', 'Rock is Dead', 'Clubbed to Death']
    },
    {
        'title': 'Arrival',
        'year': 2016,
        'genre': ['Sci-Fi', 'Drama'],
        'themes': ['Communication', 'Time', 'Language', 'Humanity'],
        'cast': ['Amy Adams', 'Jeremy Renner', 'Forest Whitaker'],
        'director': 'Denis Villeneuve',
        'plot': 'A linguist works with the military to communicate with alien lifeforms.',
        'rating': 7.9,
        'reviews': [
            {'text': 'Thoughtful and intelligent sci-fi', 'rating': 8.0},
            {'text': 'Beautiful and moving story', 'rating': 7.8},
            {'text': 'Unique take on alien contact', 'rating': 8.2}
        ],
        'soundtrack': ['Arrival', 'Heptapod B', 'First Encounter']
    },
    {
        'title': 'Ex Machina',
        'year': 2014,
        'genre': ['Sci-Fi', 'Drama', 'Thriller'],
        'themes': ['Artificial Intelligence', 'Consciousness', 'Identity', 'Technology'],
        'cast': ['Alicia Vikander', 'Domhnall Gleeson', 'Oscar Isaac'],
        'director': 'Alex Garland',
        'plot': 'A programmer participates in an experiment involving artificial intelligence.',
        'rating': 7.7,
        'reviews': [
            {'text': 'Thought-provoking exploration of AI', 'rating': 8.0},
            {'text': 'Tense and atmospheric', 'rating': 7.5},
            {'text': 'Great performances and writing', 'rating': 7.8}
        ],
        'soundtrack': ['The Turing Test', 'Bunsen Burner', 'Skin']
    }
]

def populate_database():
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Add movies
        for movie_data in movies:
            movie = Movie(**movie_data)
            db.session.add(movie)
        
        # Commit changes
        db.session.commit()
        print("Database populated successfully!")

if __name__ == '__main__':
    populate_database()
