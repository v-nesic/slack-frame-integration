from django.conf.urls import include, url

from django.contrib import admin

admin.autodiscover()

import slacktoframe.views


urlpatterns = [
    url(r'^slack/([a-zA-Z_][0-9a-zA-Z\-_.]*)/slash-cmd', slacktoframe.views.slack_slash_cmd_request, name='slack-slash-cmd'),
    url(r'^frame/instance/([0-9a-zA-Z-_]+)/', slacktoframe.views.frame_instance_request, name='frame-instance'),
    url(r'^admin/', include(admin.site.urls)),
]
