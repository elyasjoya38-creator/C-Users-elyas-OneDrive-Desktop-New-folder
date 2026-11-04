from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.user_login, name="login"),
    path("register/", views.user_register, name="register"),
    path("logout/", views.user_logout, name="logout"),
    path("", views.home, name="home"),
    path("my-account/", views.user_dashboard, name="user_dashboard"),
    path("addpdc/", views.pdcadd, name="addpdc"),
    path("managepdc/", views.managepdc, name="managepdc"),
    path("updatepdc/<int:id>/", views.updatepdc, name="updatepdc"),
    path("deletes/<int:id>/", views.deletes, name="deletes"),
]
