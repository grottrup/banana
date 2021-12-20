from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from django.db.models.functions import Concat
from django.forms import ModelForm, DateInput
from users.models import event, User

class UserSignUpForm(UserCreationForm):
    # doing this makes the email field a mandatory field for the user to input data
    email = forms.EmailField()
    email_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        # this form is to interact with the model/database table below
        # i.e if the form is saved, save the data to the User table
        model = User
        # the form should display the following fields
        fields = ['first_name', 'last_name', 'username', 'email','email_password', 'password1', 'password2']
        

class EmailMessageForm(forms.Form):
    
    # the email recipients
    to_email = forms.EmailField()
    cc = forms.EmailField()
    bcc = forms.EmailField()
    # the email subject
    subject = forms.CharField(max_length=100)

    # the email message textarea
    message = forms.CharField(max_length=2000,widget=forms.Textarea)
    #the email attachment(s)
    attachment = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple':True}))

    def __init__(self, *args, **kwargs):
        super(EmailMessageForm, self).__init__(*args, **kwargs) # Call to ModelForm constructor
        self.fields['subject'].widget.attrs['style'] = 'width:100%;'
        self.fields['message'].widget.attrs['cols'] = 150
        self.fields['attachment'].widget.attrs['id'] = 'attachment-id'
        
        self.fields['cc'].required = False
        self.fields['bcc'].required = False
        self.fields['attachment'].required = False
        
        self.fields['to_email'].label=u''
        self.fields['cc'].label=u''
        self.fields['bcc'].label=u''
        self.fields['subject'].label=u''
        self.fields['message'].label=u''
        self.fields['attachment'].label=u''

class EventForm(ModelForm):
  class Meta:
    model = event
    # datetime-local is a HTML5 input type, format to make date time show on fields
    widgets = {
      'start_time': DateInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
      'end_time': DateInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
    }
    fields = '__all__'

  def __init__(self, *args, **kwargs):
    super(EventForm, self).__init__(*args, **kwargs)
    # input_formats to parse HTML5 datetime-local input to datetime field
    self.fields['start_time'].input_formats = ('%Y-%m-%dT%H:%M',)
    self.fields['end_time'].input_formats = ('%Y-%m-%dT%H:%M',)
    self.fields['description'].widget.attrs['style'] = 'resize: none;'