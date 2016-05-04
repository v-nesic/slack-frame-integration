from django.conf.urls import include, url

from django.contrib import admin

admin.autodiscover()

import hello.views


# Examples:
# url(r'^$', 'gettingstarted.views.home', name='home'),
# url(r'^blog/', include('blog.urls')),

urlpatterns_frameinstance = [
    url(r'run/([0-9a-zA-Z-_]+)/', hello.views.frame, name='frame-instance-run')
]

urlpatterns = [
    url(r'^$', hello.views.index, name='index'),
    url(r'^db', hello.views.db, name='db'),
    url(r'^slack/([a-zA-Z_][0-9a-zA-Z\-_.]*)/slash-cmd', hello.views.slack_slash_cmd_request, name='slack-slash-cmd'),
    url(r'^frame/instance/', include(urlpatterns_frameinstance), name='frame-instance'),
    url(r'^admin/', include(admin.site.urls)),
]
