from django.views.generic import ListView

from book.models import Book


class BookListView(ListView):
    model = Book
