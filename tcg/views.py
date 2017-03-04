from django.views.generic import ListView

from tcg.models import Deck


class DeckListView(ListView):
    model = Deck
