# vim: et:sta:bs=2:sw=4:
from django.conf.urls.defaults import *
from django.conf import settings

from tkb import views

urlpatterns = patterns('',
        url(r'^static/(?P<path>.*)$', views.direct_to_folder,
                {'root': settings.MEDIA_ROOT}),
        url(r'^api/by-room/?$', views.api_by_room, name='api-by-room'),
        url(r'^push/?$', views.push, name='push'),
        url(r'^$', views.home)
)
