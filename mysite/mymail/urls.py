from django.urls import path
from django.contrib.auth.views import LogoutView, LoginView
from django_registration.backends.one_step.views import RegistrationView
from . import views


urlpatterns = [
    path('', views.redir, name='home'),
    path('received/<int:page>', views.search_received, name='search_received'),
    path('send/<int:page>', views.search_send, name='search_send'),
    path('templates/<int:page>', views.search_templates, name='search_templates'),
    path('<uuid:message_url>', views.read_message, name='read_message'),
    path('new', views.create_message, name='create_message'),
    path('delete/<uuid:message_url>', views.delete, name='delete'),
    path('just_delete/<uuid:message_url>', views.just_delete, name='just_delete'),
    path('delete/<uuid:message_url>/Template', views.delete_template, name='delete_template'),
    path('new/<uuid:message_url>', views.create_from_template, name='create_from_template'),
    path(r'registration/',
         RegistrationView.as_view(template_name="mymail/registration.html", success_url="/"),
         name='registration'),
    path(r'logout/', LogoutView.as_view(), name='logout'),
    path(r'login/', LoginView.as_view(template_name="mymail/login.html"), name='login_view'),
]
''
'received/<int:page>'
'send/<int:page>'
'templates/<int:page>'
'<uuid:message_url>'
'new'
'delete/<uuid:message_url>'
'just_delete/<uuid:message_url>'
'delete/<uuid:message_url>/Template'
'new/<uuid:message_url>'
r'registration/'
r'logout/'
r'login/'
