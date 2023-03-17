# Django
from django.urls import path
from django.contrib.auth.decorators import login_required

# This app
from .views import MovieView, DragMovieStaffView, LikeDislikeView, MovieReviewView

app_name="movies"
urlpatterns = [
    path("<slug>/<pk>/", MovieView.as_view(), name="movie_path"),
    path("<slug>/<pk>/rate/", login_required(LikeDislikeView.as_view()), name="like_dislike_path"),
    path("<slug>/<pk>/reviews/", MovieReviewView.as_view(), name="like_dislike_path"),
    path("<slug>/<pk>/drag-staff/<job>/", DragMovieStaffView.as_view(), name="drag_movie_staff_path"),
]
