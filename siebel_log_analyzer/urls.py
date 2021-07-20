from django.urls import path
from . import views
urlpatterns = [path('',views.home,name='home'),
                path('home',views.home,name='home'),
                path('fetchsql',views.fetchsql, name = 'fetchsql'),
                path('fetchinsertupdate',views.fetchinsertupdate, name = 'fetchinsertupdate'),
                path('evntcntxt',views.evntcntxt, name = 'evntcntxt'),
                path('executiontime',views.executiontime, name = 'executiontime'),
                path('initialfetchtime',views.initialfetchtime, name = 'initialfetchtime'),
                path('preparetime',views.preparetime, name = 'preparetime'),
               path('analyze',views.analyze,name = 'analyze')]