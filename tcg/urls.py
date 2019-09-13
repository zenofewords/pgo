from django.urls import path

from tcg.views import DeckListView


urlpatterns = (
    path('', DeckListView.as_view(), name='deck-list'),
)
