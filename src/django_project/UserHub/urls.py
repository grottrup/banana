from django.urls import path, include
from django.contrib import admin
from django.contrib.auth import views as auth_views 

urlpatterns = [

    path('admin/', admin.site.urls),


    #Path for Login
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html'
    ),
    name='login'),

    #Path for Logout
    path('logout/', auth_views.LogoutView.as_view(
        
        # Site you are sent to when logging out - @Karsten, you need to match this keyword
        next_page='dashboard'
    ),
    name='logout')

]

