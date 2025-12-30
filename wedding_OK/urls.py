from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from rest_framework import routers
from apps.main.api import views as main_views

router = routers.DefaultRouter()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', main_views.index, name='index'),
    path('api/main/', include('apps.main.api.urls')),
    path('api/gallery/', include('apps.gallery.api.urls')),
    path('api/invitations/', include('apps.invitations.api.urls')),
    path('', include('apps.invitations.urls')),  # Маршруты для приглашений
]

if settings.DEBUG:
    import debug_toolbar
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()
