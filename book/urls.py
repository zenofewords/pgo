from django.conf.urls import url

from book.views import BookListView


urlpatterns = (
    url(r'^$', BookListView.as_view(), name='book-list'),
)
