from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer)
    genre = db.Column(db.JSON)  # List of genres
    themes = db.Column(db.JSON)  # List of themes
    cast = db.Column(db.JSON)  # List of cast members
    director = db.Column(db.String(100))
    plot = db.Column(db.Text)
    rating = db.Column(db.Float)
    reviews = db.Column(db.JSON)  # List of review objects
    soundtrack = db.Column(db.JSON)  # List of soundtrack details

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'year': self.year,
            'genre': self.genre,
            'themes': self.themes,
            'cast': self.cast,
            'director': self.director,
            'plot': self.plot,
            'rating': self.rating,
            'reviews': self.reviews,
            'soundtrack': self.soundtrack
        }
