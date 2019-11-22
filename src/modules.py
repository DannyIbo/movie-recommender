# coding: utf-8

from sqlalchemy import create_engine
import os
import pandas as pd
from sklearn.decomposition import NMF
from fuzzywuzzy import process

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
    df_data = pd.read_sql(query, engine)

    return engine, df_data


def setup_nmf(engine, number_of_genres = 10):
    ''''''

    # Create a sparse matrix of user, movie ids and their ratings (User Movie Ratings UMR)
    umr = pd.pivot_table(df_data, values='rating', index='userId', columns='movieId')

    # Fill sparse matrix' NaNs with 0 to make it dense
    R = umr.fillna(0)

    # Create and fit a NMF model
    number_of_genres = number_of_genres
    m = NMF(n_components=number_of_genres)
    m.fit(R)

    # Create a movie-genre matrix
    # Q: movie-matrix. Each genre (row) has a coefficient for each movie (columns). Number of genres is set by the NMF hyperparameter n_components=2. Q is the film submatrix.
    Q = m.components_

    # P: Create a user submatrix
    P = m.transform(R)

    return df_data, m, P, Q, R


def process_user_input(user_input, df_data):
    '''Return a tuple with title, scoring and index for df_data.'''
    # Pre-select movies from database. Select everything that contains the first 3 letters capitalized of user input
    df_guess = df_data[df_data['title'].str.contains(user_input[:3].lower().capitalize())].groupby('title').first().reset_index()
    # Get ordered list of the five most similar movie titles to user input. Return a tuple of title, match score and index.
    guesses = process.extract(user_input, df_guess['title'])

    return guesses, df_guess
