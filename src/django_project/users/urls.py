from django.urls import path, include
from django.contrib import admin
# import the built in django authentication views and rename it to auth_views
# renaming an import enables us to import views from other sources with the same name avoiding confusion and collision
# e.g. from django.contrib.auth import views as auth_views
# e.g. from users import views as users_views

# you can create your own log in and log out view methods, but using the builtin django views makes the work easier
from django.contrib.auth import views as auth_views

# import the user views
from users.views import Event, index, signup, send_email, CalendarView, event
from . import views

urlpatterns = [
    # the name param in the path method is the name passed to the url tag inside the HTML template pages
    # e.g <a href=" {% url 'signup' %} "> This is an example of a link</a>
    # the url tag above will then resolve the name param to the appropriate http url
    # e.g http://127.0.0.1/signup   
    path('', index, name='index'),
    path('signup/', signup, name='signup'), 
    path('send_email/', send_email, name='send_email'), 
    path('calendar/', CalendarView.as_view(), name='calendar'),
    path('event/new/', views.Event, name='new_event'),
    path('event/edit/(?P<event_id>\d+)/', views.Event, name='event_edit'),
    path('favorite/', auth_views.LoginView.as_view(template_name="users/favorite.html"), name='favorite'),

    # this url will use the builtin django log in view, but we have to pass a template
    # that the view will use to pass its authentication/log in form to for users to enter log in credentials
    path('login/', auth_views.LoginView.as_view(template_name="users/login.html"), name='login'),

    # we will utilise the builtin django views on the urls below
    path('logout/', auth_views.LogoutView.as_view(template_name="users/logout.html"), name='logout'),
    # a path to a page where you enter your email to request for a password reset
    path('passwod-reset/', auth_views.PasswordResetView.
         as_view(template_name="users/password_reset.html"),
         name='password_reset'),
    # the link to the page where you will reset your password, this link will be emailed to you
    # using the email settings provided in the projects settings.py file
    path('passwod-reset-confirm/<uidb64>/<token>', auth_views.PasswordResetConfirmView.
         as_view(template_name="users/password_reset_confirm.html"),
         name='password_reset_confirm'),
    # a page to inform the user that an email with the link above has xbeen successfully sent
    path('passwod-reset/done/', auth_views.PasswordResetDoneView.
         as_view(template_name="users/password_reset_done.html"),
         name='password_reset_done'),
    # the page a user will be redirected to once they reset their email from the emailed link above
    path('passwod-reset-complete', auth_views.PasswordResetCompleteView.
         as_view(template_name="users/password_reset_complete.html"),
         name='password_reset_complete'),
]
