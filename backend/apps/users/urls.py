from rest_framework.urls import path

from . import views

app_name ='users'

urlpatterns = [
    path('signup', views.SignUpView.as_view({'post': 'signup'}), name='signup'),
    path('login', views.AuthenticationView.as_view({'post': 'login'}), name='login'),
    path('login_status', views.login_status, name='get_login_status'),
    path('accounts/logout', views.AccountViews.as_view({'post': 'log_out'}), name = 'logout')
]