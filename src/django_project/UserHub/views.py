from django.shortcuts import render, redirect
from django.views.generic import TemplateView, CreateView
from django.contrib.auth.models import User
from django.contrib import messages
from UserHub.forms import UserSignUpForm, EmailMessageForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth import login, authenticate, logout
from UserHub.forms import RegistrationForm, AccountAuthenticationForm
from django.shortcuts import render	

# Create your views here.

def register_view(request, *args, **kwargs):
	user = request.user
	if user.is_authenticated: 
		return HttpResponse("You are already authenticated as " + str(user.email))

	context = {}
	if request.POST:
		form = RegistrationForm(request.POST)
		if form.is_valid():

            # creates the account
			form.save()

            # getting email and password
			email = form.cleaned_data.get('email').lower()
			raw_password = form.cleaned_data.get('password1')

            # authenticating the account, with new email and password
			account = authenticate(email=email, password=raw_password)

            # log them in to the website
			login(request, account)

			destination = kwargs.get("next")
			if destination:
				return redirect(destination)
			return redirect('home')
		else:
			context['registration_form'] = form

	else:
		form = RegistrationForm()
		context['registration_form'] = form
	return render(request, 'account/register.html', context)



def home_screen_view(request):
	context = {}
	return render(request, "UserHub/home.html", context)

def logout_view(request):
	logout(request)
	return redirect("home")


def login_view(request, *args, **kwargs):
	context = {}

	user = request.user
	if user.is_authenticated: 
		return redirect("home")

	destination = get_redirect_if_exists(request)
	print("destination: " + str(destination))

	if request.POST:
		form = AccountAuthenticationForm(request.POST)
		if form.is_valid():
			email = request.POST['email']
			password = request.POST['password']
			user = authenticate(email=email, password=password)

			if user:
				login(request, user)
				if destination:
					return redirect(destination)
				return redirect("home")

	else:
		form = AccountAuthenticationForm()

	context['login_form'] = form

	return render(request, "account/login.html", context)


def get_redirect_if_exists(request):
	redirect = None
	if request.GET:
		if request.GET.get("next"):
			redirect = str(request.GET.get("next"))
	return redirect


def send_email(request):
    # do the following when a user, submits the form which sends/returns a POST request to the same view
    # and sends/returns with it the POST data submited in the form
    if request.method == 'POST':
        # instantiate a new form with the POST data submitted
        form = EmailMessageForm(request.POST)
        # check if the submitted form data is valid
        if form.is_valid():
            # get the submitted subject
            subject = form.cleaned_data['subject']

            # get the submitted message
            message = form.cleaned_data['message']

            # get the submitted user_id, which is the value of the option that was selected and submitted
            user_id = form.cleaned_data['user_id']

            # get the user associated with the passed user_id
            user = User.objects.get(id=user_id)

            #file = request.FILES['file']
            #attach = user.attach(file.name, file.read(), file.content_type())
            #email = EmailMessage(subject,message,EMAIL_HOST_USER, user_id) 
            #email.content_subtype = 'html'

            
            #email.send()
            
            # call the built in email_user method on the returned user object
            # enter the email subject, message and the name of whom the email is from
            # set it to fail silently if an error occurrs
            # this email will be sent to the users email inbox/spam folder
            user.email_user(subject, message, request.user.get_full_name(),
                                                    fail_silently=True)
            

            #file = request.FILES['file']
            #email.attach(file.name, file.read(), file.content_type())

            #email.send()

            # All emails sent will be viewed on the configured Google Email Account in the settings.py file
            # Log into the Gmail account of the configured Google Email Account in the settings.py file
            # Navigate to the sent folders to view all emails sent and any error messages sent back

            # the messages python module simply sends a message back to the HTML template 
            # rendering this view, for you to display to the user
            messages.success(request, f'An email has been sent to {user.get_full_name()}')

            # redirect the user back to the home page
            return redirect('index')
    # pass the blank email message form when a user navigates to the email page through a GET request
    else:
        form = EmailMessageForm()

    context = {
        'form': form,
    }
    return render(request, 'UserHub/send_email.html', context)


