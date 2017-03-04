from django.conf.urls import url

from tcg.views import DeckListView


urlpatterns = (
    url(r'^$', DeckListView.as_view(), name='deck-list'),
)
