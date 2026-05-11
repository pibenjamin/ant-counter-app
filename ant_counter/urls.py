from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.admin import admin_site

urlpatterns = [
    path("grappelli/", include("grappelli.urls")),
    path("admin/", admin_site.urls),
    path("accounts/", include("allauth.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("", include("counter.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
