from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin

from pgo.api.urls import pgo_api_urls


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api-pgo/', include(pgo_api_urls, namespace='api-pgo')),

    url(r'^', include('pgo.urls', namespace='pgo')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
