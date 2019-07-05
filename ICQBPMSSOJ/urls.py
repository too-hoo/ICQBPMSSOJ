"""ICQBPMSSOJ URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    # url(r'^admin/', admin.site.urls),
    url(r"^api/", include("account.urls.uicqbpmssoj")),
    url(r"^api/admin/", include("account.urls.uiadmin")),
    url(r"^api/", include("announcement.urls.uicqbpmssoj")),
    url(r"^api/admin/", include("announcement.urls.uiadmin")),
    url(r"^api/", include("contest.urls.uicqbpmssoj")),
    url(r"^api/admin/", include("contest.urls.uiadmin")),
    url(r"^api/", include("problem.urls.uicqbpmssoj")),
    url(r"^api/admin/", include("problem.urls.uiadmin")),
    url(r"^api/", include("submission.urls.uicqbpmssoj")),
    url(r"^api/admin/", include("submission.urls.uiadmin")),
    url(r"^api/", include("conf.urls.uicqbpmssoj")),
    url(r"^api/admin/", include("conf.urls.uiadmin")),
]
