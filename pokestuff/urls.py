from django.conf import settings
from django.conf.urls import include
from django.urls import path
from django.conf.urls.static import static
from django.contrib import admin

from pgo.api.urls import pgo_api_urls


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-pgo/', include((pgo_api_urls, 'api-pgo'), namespace='api-pgo')),

    path('', include('pgo.urls', namespace='pgo')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
admin.site.enable_nav_sidebar = False

if settings.DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
