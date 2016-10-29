# coding=utf-8
"""volgui URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
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

from django.conf.urls import url
# from django.contrib import admin
from web import views

app_name = 'web'
urlpatterns = [
    # url(r'^admin/', admin.site.urls),
    url(r'^$', views.index),
    url(r'^list_sessions/', views.list_sessions),
    url(r'^session/(?P<sess_id>.+)/$', views.session_page),
    url(r'createsession', views.create_session),
    url(r'^pluginoutput/(?P<plugin_id>[0-9a-fA-F]{24})/$', views.plugin_output),
    url(r'^download/(?P<query_type>.+)/(?P<object_id>[0-9a-fA-F]{24})/$', views.file_download),
    url(r'^ajaxhandler/(?P<command>.+)/$', views.ajax_handler),
]
