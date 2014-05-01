from django.conf.urls import patterns, include, url
from hellosign import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'django_site.views.home', name='home'),
    # url(r'^django_site/', include('django_site.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'hellosign.views.index'),
    url(r'^embedded_signing', views.embedded_signing, name='embedded_signing'),
    url(r'^embedded_requesting', views.embedded_requesting, name='embedded_requesting'),
    url(r'^embedded_template_requesting', views.embedded_template_requesting, name='embedded_template_requesting'),
    url(r'^oauth$', views.oauth, name='oauth'),
    url(r'^oauth_callback', views.oauth_callback, name='oauth_callback'),

)
urlpatterns += staticfiles_urlpatterns()
