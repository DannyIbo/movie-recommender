# movie-recommender
At a glance:
A movie recommending system running in flask. 

Running version online: https://movie-recommender-dannyibo.herokuapp.com/

Functionality:
User can type in movie names and get by default 5 recommendations for similar movies they most likely like. 

Technology:
A Non-Nagative-Matrix-Factorization Model gets trained on the start of the server. The training is based on the small MovieLens dataset available on https://grouplens.org/datasets/movielens/.

YouTube API:
Optionally a YouTube Data API Key can be defined. This will allow the app to display the trailer videos for the recommended movies as embedded YouTube videos.
