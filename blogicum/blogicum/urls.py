from django.contrib import admin
from django.urls import path, include
from django.conf import settings

urlpatterns = [
    path('', include('blog.urls', namespace='blog')),
    path('pages/', include('pages.urls', namespace='pages')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += (path('__debug__', include(debug_toolbar.urls)),)


handler404 = 'core.views.page_not_found'
handler500 = 'core.views.server_error'
