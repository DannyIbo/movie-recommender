from flask import Flask, render_template, request, url_for
import os
from src.modules import (
    create_engine_load_data,
    setup_nmf,
    process_user_input,
    recommend_movies,
    youtubeAPIkey,
    get_yt_videos
)

class PrefixMiddleware(object):
    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)
        else:
            start_response('404', [('Content-Type', 'text/plain')])
            return ["This url does not belong to the app.".encode()]

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

engine, all_ratings = create_engine_load_data()
NMF_Model, genre_movie_matrix, user_movie_id_ratings_matrix = setup_nmf(
all_ratings=all_ratings,
engine=engine,
number_of_genres = 10
)

app = Flask(__name__)
# app.config["APPLICATION_ROOT"] = "/flask"
app.debug = True
app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix='/flask')

@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/select')
def select():
    user_input = request.args.items()

    guesses_list = []
    for ui in user_input:
        if ui[1]:
            guesses = process_user_input(user_input=ui, all_ratings=all_ratings)
            guesses_list.append(guesses)

    return render_template(
        'select.html',
        guesses_list=guesses_list,
        user_input=user_input
    )

@app.route('/recommend')
def recommend():
    user_movie_title_list = request.args.values()
    recom_movie_titles = recommend_movies(
        all_ratings=all_ratings,
        user_movie_title_list=user_movie_title_list,
        user_movie_id_ratings_matrix=user_movie_id_ratings_matrix,
        genre_movie_matrix=genre_movie_matrix,
        NMF_Model=NMF_Model,
        engine=engine,
        number_of_recommendations=3
    )

    yt_results = ""
    if YOUTUBE_API_KEY:
        youtube = youtubeAPIkey(YOUTUBE_API_KEY)
        yt_results = get_yt_videos(youtube, titles=recom_movie_titles)
    else:
        yt_results = []
        for r in recom_movie_titles:
            dict = {}
            dict['recommendation'] = r
            yt_results.append(dict)

    return render_template(
        'recommend.html',
        yt_results=yt_results
    )

if __name__ == '__main__':
    app.run(port=5000, debug=True)
