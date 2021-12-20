from calendar import calendar
from django.core import mail
from django.db.models.functions.text import Reverse
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import CreateView

from django.contrib import messages

from users.forms import UserSignUpForm, EmailMessageForm
from users.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage, send_mail
from my_django_project import settings

import json
import os
from datetime import date, datetime, timedelta
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from django.utils.safestring import mark_safe
from django.urls import reverse

import calendar

from .models import *
from .utils import Calendar
from .forms import EventForm

#from django_email_blacklist import DisposableEmailChecker

with open('config.json') as conf_file:
    config = json.load(conf_file)

# Create your views here.
@login_required
def index(request):
    return render(request, 'users/index.html')
        

def signup(request):
    # do the following when a user, submits the form which sends/returns a POST request to the same view
    # and sends/returns with it the POST data submited in the form
    if request.method == 'POST':
        # instantiate a new form with the POST data submitted
        form = UserSignUpForm(request.POST)
        # check if the submitted form data is valid
        if form.is_valid():
            # call the form save method to save the data into the DB
            form.save()
            # the messages python module simply sends a message back to the HTML template 
            # rendering this view, for you to display to the user
            messages.success(request, f'Your account has been created')
            return redirect('login')
    # pass the blank sign up form when a user navigates to this page through a GET request
    else:
        form = UserSignUpForm()
    return render(request, 'users/signup.html', {'form': form})

# we will use the django built in method/decorator called @login_required
# to force a user to log in first before accessing this view/webpage
@login_required
def send_email(request):

    # do the following when a user, submits the form which sends/returns a POST request to the same view
    # and sends/returns with it the POST data submited in the form
    if request.method == 'POST':
        # instantiate a new form with the POST data submitted
        form = EmailMessageForm(request.POST or None, request.FILES or None)
        # check if the submitted form data is valid
        if form.is_valid():
            # get the submitted subject
            subject = form.cleaned_data['subject']

            # get the submitted message
            message = form.cleaned_data['message']

            # get the sender
            from_email = request.user.email

            # used to get data from forms.py
            to_email = form.cleaned_data
            cc = form.cleaned_data
            bcc = form.cleaned_data
            
            # gets a list of files
            files = request.FILES.getlist('attachment')
         
            if from_email and to_email:
                try:
                    mailmsg = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=request.user.email,
                    reply_to=[request.user.email],
                    to=[to_email['to_email']],
                    bcc=[bcc['bcc']],
                    cc=[cc['cc']])

                    is_attachment_empty = bool(files)
                    #for loop for cycling through multiple attachments
                    if is_attachment_empty == True:
                        for f in files:
                            mailmsg.attach(f.name, f.read(), f.content_type)
                    
                    #make so the email content type is html
                    mailmsg.content_subtype = 'html'
                    mailmsg.send()
                    messages.success(request, f'An email has been sent')
                # except Exception as ex:
                except ArithmeticError as aex:
                    print(aex.args)
                    return HttpResponse('Invalid header found')
                return redirect('index')
            else:
                return HttpResponse('Make sure all fields are entered and valid.')
            # pass the blank email message form when a user navigates to the email page through a GET request
    else:
        form = EmailMessageForm()

        context = {
            'form': form,
        }
    return render(request, 'users/send_email.html', context)

class CalendarView(generic.ListView):
    model = event
    template_name = 'users/cal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # use today's date for the calendar
        d = get_date(self.request.GET.get('month', None))

        # Instantiate our calendar class with today's year and date
        cal = Calendar(d.year, d.month)

        # Call the formatmonth method, which returns our calendar as a table
        html_cal = cal.formatmonth(withyear=True)
        context['calendar'] = mark_safe(html_cal)
        context['prev_month'] = prev_month(d)
        context['next_month'] = next_month(d)
        return context

def get_date(req_day):
    if req_day:
        year, month = (int(x) for x in req_day.split('-'))
        return date(year, month, day=1)
    return datetime.today()

def prev_month(d):
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    month = 'month=' + str(prev_month.year) + '-' + str(prev_month.month)
    return month

def next_month(d):
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
    return month

def Event(request, event_id=None):
    instance = event()
    if event_id:
        instance = get_object_or_404(event, pk=event_id)
    else:
        instance = event()
    
    form = EventForm(request.POST or None, instance=instance)
    if request.POST and form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('calendar'))
    return render(request, 'users/event.html', {'form': form})

#email_checker = DisposableEmailChecker()
#email_checker.is_disposable("foo@guerrillamail.com")