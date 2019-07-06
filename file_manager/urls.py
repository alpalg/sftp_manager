from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('register/', views.register, name='register'),
    path('connections/', views.all_connections, name='all_connections'),
    path('add/', views.add_connection, name='add_connection'),
    path('edit/<str:username>@<str:host>/',
         views.edit_connection, name='edit_connection'),
    path('del/<str:username>@<str:host>/',
         views.delete_connection, name='delete_connection'),
    path('open_connection/<username>@<host>:<current_dir>/',
         views.open_connection, name='open_connection'),
    path('get_file/<username>@<host>:<path>/',
         views.get_file, name='get_file'),
]
