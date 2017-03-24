from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin

from pgo.api.routers import pgo_router

from zenofewords.views import HomeView


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^api-pgo/', include(pgo_router.urls, namespace='api-pgo')),
    url(r'^api-auth/', include(
        'rest_framework.urls', namespace='rest_framework')),

    url(r'^blog/', include('blog.urls', namespace='blog')),
    url(r'^pgo/', include('pgo.urls', namespace='pgo')),
    url(r'^book/', include('book.urls', namespace='book')),
    url(r'^tcg/', include('tcg.urls', namespace='tcg')),
    url(r'^$', HomeView.as_view(), name='home'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
