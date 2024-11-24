from flask_frozen import Freezer
from app import app
import os
import shutil

# Ensure the build directory exists
if not os.path.exists('build'):
    os.makedirs('build')

# Copy the database to the build directory
if os.path.exists('instance/movies.db'):
    os.makedirs('build/instance', exist_ok=True)
    shutil.copy2('instance/movies.db', 'build/instance/movies.db')

os.environ['GITHUB_PAGES'] = 'true'

app.config['FREEZER_DESTINATION'] = 'build'
app.config['FREEZER_BASE_URL'] = 'https://sck000.github.io/MovieMatch/'
app.config['FREEZER_RELATIVE_URLS'] = True

freezer = Freezer(app)

@freezer.register_generator
def movie_details():
    # Generate URLs for movie details pages
    # This is just an example, you might want to adjust based on your actual movies
    for movie_id in range(1, 1000):  # Generate for first 1000 movies
        yield {'movie_id': movie_id}

if __name__ == '__main__':
    freezer.freeze()
