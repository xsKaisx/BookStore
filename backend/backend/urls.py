"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.urls import path, include, re_path
from django.contrib.staticfiles import views
from django.conf.urls.static import static



from apps.users import urls as users_url
from apps.models import urls as books_url

urlpatterns = []
apis = []
apis += users_url.urlpatterns
apis += books_url.urlpatterns

urlpatterns.append(
    path('api/', include((apis, 'book-store-apis'), namespace='book-store-apis')),
)

if settings.DEBUG:
    urlpatterns += [
        re_path('^admin/', admin.site.urls),
        re_path('^accounts/', admin.site.urls),
        re_path(r'^static/(?P<path>.*)$', views.serve)
    ]
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
