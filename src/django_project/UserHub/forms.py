from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import CharField, Value as V, F
from django.db.models.functions import Concat

from UserHub.models import Account
class RegistrationForm(UserCreationForm):
	email = forms.EmailField(max_length=254, help_text='Required. Add a valid email address.')

	class Meta:
		model = Account
		fields = ('email', 'username', 'password1', 'password2', )

	def clean_email(self):
		email = self.cleaned_data['email'].lower()
		try:
			account = Account.objects.exclude(pk=self.instance.pk).get(email=email)
		except Account.DoesNotExist:
			return email
		raise forms.ValidationError('Email "%s" is already in use.' % account)

	def clean_username(self):
		username = self.cleaned_data['username']
		try:
			account = Account.objects.exclude(pk=self.instance.pk).get(username=username)
		except Account.DoesNotExist:
			return username
		raise forms.ValidationError('Username "%s" is already in use.' % username)

class AccountAuthenticationForm(forms.ModelForm):

	password = forms.CharField(label='Password', widget=forms.PasswordInput)

	class Meta:
		model = Account
		fields = ('email', 'password')

	def clean(self):
		if self.is_valid():
			email = self.cleaned_data['email']
			password = self.cleaned_data['password']
			if not authenticate(email=email, password=password):
				raise forms.ValidationError("Invalid login")



class UserSignUpForm(UserCreationForm):
    # doing this makes the email field a mandatory field for the user to input data
    email = forms.EmailField()

    class Meta:
        # this form is to interact with the model/database table below
        # i.e if the form is saved, save the data to the User table
        model = User
        # the form should display the following fields
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']

# we will a create a form with a drop down list of users who have signed up
# the drop down will display the names of the users, but will hold the user emails
# as the drop down/select value. This is the value that will be submited when a user submits the form

# the form will also have a large text area that can accomodate 2,000 words for the user to type the message
class EmailMessageForm(forms.Form):
    # get all active registered users
    # the values_list data is the data to be held in the drop down i.e. inside the HTML select tags
    #
    # <select>
    #   <option value="id"> User Fullname </option>
    #   <option value="1"> John Doe </option>
    # </select>
    #

    CHOICES = User.objects.all().values_list(   
                    # the data to be held in the value field of the dropdowns e.g. the HTML option tag
                    'id',
    
                    # the user friendly value that will be displayed to the user is the User Fullname
                    # which will be a concatination of the users' first_name and last_name
                    # I am placing the V(' ') between the names simply to create a space during concatination
                    Concat(
                            F('first_name'), V(' '), F('last_name'),

                            #how the data is to be outputted
                            output_field=CharField()
                        )
                )

    # the drop down to hold registered active users' (users not deleted/deactivated) fullnames and user database ids
    # the drop down is to be populated with data from the CHOICES variable above
    user_id = forms.ChoiceField(choices=CHOICES)

    # the email subject
    subject = forms.CharField(max_length=100)

    # the email message textarea
    message = forms.CharField(max_length=2000,widget=forms.Textarea)


    #attach = forms.FileField()

    def __init__(self, *args, **kwargs):
        super(EmailMessageForm, self).__init__(*args, **kwargs) # Call to ModelForm constructor
        self.fields['subject'].widget.attrs['style'] = 'width:100%;'
        self.fields['message'].widget.attrs['cols'] = 150

