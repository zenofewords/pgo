from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin

from zenofewords.views import HomeView


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^blog/', include('blog.urls', namespace='blog')),
    url(r'^pgo/', include('pgo.urls', namespace='pgo')),
    url(r'^book/', include('book.urls', namespace='book')),
    url(r'^tcg/', include('tcg.urls', namespace='tcg')),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
