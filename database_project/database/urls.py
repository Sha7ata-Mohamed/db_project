from django.urls import path
from .views import search_view, home_view


urlpatterns = [
    path("", home_view, name="home"),
    path("search/", search_view, name="search"),
]
