from django.shortcuts import render, redirect
from django.views.generic import TemplateView, CreateView
from django.contrib.auth.models import User
from django.contrib import messages
#from UserHub.forms import UserSignUpForm, EmailMessageForm
from django.contrib.auth.decorators import login_required

# Create your views here.

class DashboardView(TemplateView):
    template_name= 'dashboard.html'
