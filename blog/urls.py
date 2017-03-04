from django.conf.urls import url

from blog.views import BlogListView


urlpatterns = (
    url(r'^$', BlogListView.as_view(), name='blog-list'),
)
