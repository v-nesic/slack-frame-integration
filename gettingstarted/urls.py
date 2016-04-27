from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

import hello.views

# Examples:
# url(r'^$', 'gettingstarted.views.home', name='home'),
# url(r'^blog/', include('blog.urls')),

urlpatterns = [
    url(r'^$', hello.views.index, name='index'),
    url(r'^db', hello.views.db, name='db'),
	url(r'^slackframecmd/$', hello.views.slack, name='Slack\'s /frame commend implementation'),
	url(r'^frame/([^/]+)', hello.views.frame, name='Frame instance mapping'),
    url(r'^admin/', include(admin.site.urls)),
]
