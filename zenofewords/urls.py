from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin

from pgo.api.urls import pgo_api_urls


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api-pgo/', include((pgo_api_urls, 'api-pgo'), namespace='api-pgo')),

    url(r'^', include('pgo.urls', namespace='pgo')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
