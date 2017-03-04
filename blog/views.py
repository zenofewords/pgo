from django.views.generic import ListView

from blog.models import Blog


class BlogListView(ListView):
    model = Blog
