from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

import hello.views

# Examples:
# url(r'^$', 'gettingstarted.views.home', name='home'),
# url(r'^blog/', include('blog.urls')),

urlpatterns_slackcmd = [
	url(r'frame/$', hello.views.slack, name='slack-cmd-frame')
]

urlpatterns_frameinstance = [
	url(r'run/([^/]+)', hello.views.frame, name='frame-instance-run')
]

urlpatterns = [
    url(r'^$', hello.views.index, name='index'),
    url(r'^db', hello.views.db, name='db'),
	url(r'^slack/cmd/', include(urlpatterns_slackcmd), name='slack-cmd'),
	url(r'^frame/instance/', include(urlpatterns_frameinstance), name='frame-instance'),
    url(r'^admin/', include(admin.site.urls)),
]
