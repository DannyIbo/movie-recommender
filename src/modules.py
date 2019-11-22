# coding: utf-8

from sqlalchemy import create_engine
import os
import pandas as pd
from sklearn.decomposition import NMF
from fuzzywuzzy import process
import numpy as np
import googleapiclient.discovery
import google_auth_oauthlib.flow
import googleapiclient.errors

def create_engine_load_data():
    '''Load data into memory and return an engine and data as a dataframe.'''
    # Load and fill database
    engine = create_engine('sqlite:///:memory:', echo=False)

    for f in os.listdir('data/movies'):
        if f[-4:] == '.csv':
            data = pd.read_csv(f'data/movies/{f}')
            data.to_sql(f[:-4], engine)
            print(f[:-4], 'loaded succesfully')

    # LOAD DATA
    query = 'SELECT "userId", ratings."movieId", movies.title, rating FROM ratings JOIN movies ON ratings."movieId" = movies."movieId";'
    all_ratings = pd.read_sql(query, engine)

    return engine, all_ratings


def setup_nmf(all_ratings=None, engine=None, number_of_genres = 10):
    ''''''
    print('Start loading NMF')
    # Create a sparse matrix of user, movie ids and their ratings (User Movie Ratings UMR)
    user_movie_ratings = pd.pivot_table(all_ratings, values='rating', index='userId', columns='movieId')

    # Fill sparse matrix' NaNs with 0 to make it dense
    user_movie_id_ratings_matrix = user_movie_ratings.fillna(0)

    # Create and fit a NMF model
    number_of_genres = number_of_genres
    m = NMF(n_components=number_of_genres)
    m.fit(user_movie_id_ratings_matrix)

    # Create a movie-genre matrix
    # Q: movie-matrix. Each genre (row) has a coefficient for each movie (columns). Number of genres is set by the NMF hyperparameter n_components=2. Q is the film submatrix.
    genre_movie_matrix = m.components_

    # P: Create a user submatrix
    # P = m.transform(user_movie_id_ratings_matrix)
    print('Done loading NMF')

    return m, genre_movie_matrix, user_movie_id_ratings_matrix


def process_user_input(user_input=None, all_ratings=None):
    '''Return a tuple: key(name of input field), value(user input string), df_guess(dataframe of pre-selected movie names), guesses(fuzzywuzzy of user input and df_guess as tuple(title, scoring and index))'''
    # Extract tuple
    user_input_key = user_input[0]
    user_input_value = user_input[1]
    # Pre-select movies from database. Select everything that contains the first 3 letters capitalized of user input
    df_guess = all_ratings[all_ratings['title'].str.contains(user_input_value[:3].lower().capitalize())].groupby('title').first().reset_index()
    # Get ordered list of the five most similar movie titles to user input. Return a tuple of title, match score and index.
    guesses = process.extract(user_input_value, df_guess['title'])

    return user_input_key, user_input_value, df_guess, guesses


def recommend_movies(
    all_ratings=None,
    user_movie_title_list=None,
    user_movie_id_ratings_matrix=None,
    genre_movie_matrix=None,
    NMF_Model=None,
    engine=None,
    number_of_recommendations=5):

    # Get movie ids for the titles that the user selected
    movie_id_list = []
    for mt in user_movie_title_list:
        movie_id = all_ratings[all_ratings['title'] == mt]['movieId'].unique()[0]
        movie_id_list.append(movie_id)

    # Get theindexes, where the movie ids are in the NMF
    movie_index_list = []
    for id_ in movie_id_list:
        index = list(user_movie_id_ratings_matrix.columns).index(id_)
        movie_index_list.append(index)

    # Setup the ratings that the user did by selecting titles and prepare prediction
    user_rating = np.zeros(user_movie_id_ratings_matrix.shape[1])
    for i in movie_index_list:
        user_rating[i] = 5
    user_rating = user_rating.reshape(-1,1)
    user_rating = user_rating.T

    # Perform prediction
    new_P = NMF_Model.transform(user_rating)
    new_user_recommendations = np.dot(new_P,genre_movie_matrix)
    list_recom_indexes = new_user_recommendations.argsort()[:,-number_of_recommendations:][0][::-1]

    #Get themovie ids for the recommended movies
    recom_movie_ids = []
    for l in list_recom_indexes:
        recom_movie_ids.append(user_movie_id_ratings_matrix.columns[l])

    # Get the titles for the recommended movie ids
    recom_movie_titles = []
    for mid in recom_movie_ids:
        title = all_ratings[all_ratings['movieId'] == mid]['title'].unique()[0]
        recom_movie_titles.append(title)

    return recom_movie_titles


def youtubeAPIkey(DEVELOPER_KEY, OAUTHLIB_INSECURE_TRANSPORT = "1", api_service_name = "youtube", api_version = "v3"):
    '''Get YouTube Data API credentials via API Key\n
    Disable OAuthlib's HTTPS verification when running locally.\n
    *DO NOT* leave this option enabled in production.'''

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = OAUTHLIB_INSECURE_TRANSPORT #"1"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey = DEVELOPER_KEY)

    return youtube


def youtubeSearchList(youtube, channelId=None, q=None, maxResults=50):
    '''
    Return a list of video snippets for a given query q (string)
    '''
    request = youtube.search().list(
        part="snippet"
        ,channelId=channelId
        ,maxResults=maxResults
        ,q=q
        ,fields='items(id,snippet),nextPageToken'
        )
    responseSearchList = request.execute()
    return responseSearchList


def get_yt_videos(youtube, titles=None):
    '''Query YouTube for a list of titles. Return a list of dictionaries. Dict contains videoId, thumbnail, desc(ritption)'''
    response_items = []
    for t in titles:
        data = {}
        q = 'movie trailer ' + t
        responseSearchList = youtubeSearchList(youtube, channelId=None, q=q, maxResults=1)
        data['video_id'] = responseSearchList['items'][0]['id']['videoId']
        data['thumbnail'] = responseSearchList['items'][0]['snippet']['thumbnails']['medium']['url']
        data['description'] = responseSearchList['items'][0]['snippet']['description']
        data['recommendation'] = t
        response_items.append(data)

    return response_items
