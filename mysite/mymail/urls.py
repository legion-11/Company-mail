from django.urls import path
from django.contrib.auth.views import LogoutView, LoginView

from . import views

urlpatterns = [
    path('', views.redir, name='home'),
    path('received/<int:page>', views.search_received, name='search_received'),
    path('send/<int:page>', views.search_send, name='search_send'),
    path('<uuid:message_url>', views.read_message, name='read_message'),
    path('new', views.create_message, name='create_message'),
    path(r'registration/', views.registration, name='registration'),
    path(r'logout/', LogoutView.as_view(), name='logout'),
    path(r'login/', LoginView.as_view(template_name="mymail/login.html"), name='login_view'),

]
