# movie-recommender
At a glance:
A movie recommending system running in flask. 

Functionality:
User can type in movies and get by default 5 recommendations for similar movies they most likely like. 

Technology:
A Non-Nagative-Matrix-Factorization Model gets trained on the start of the server. The training is based on the small MovieLens dataset available on https://grouplens.org/datasets/movielens/.

YouTube API:
Optionally a YouTube Data API Key can be defined. This will allow the app to display the trailers as embedded YouTube videos.
