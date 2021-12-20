from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
#from disposable_email_checker.fields import DisposableEmailField
# Create your models here.

class event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    @property
    def get_html_url(self):
        url = reverse('event_edit', args=(self.id,))
        return f'<a href="{url}"> {self.title} </a>'


class MyAccountManager(BaseUserManager):
    def create_user(self, email, username, email_password=None, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')
            
        user = self.model(
			email=self.normalize_email(email),
			username=username,
            email_password=email_password,
		)

        user.set_password(password)
        user.save(using=self._db)
        return user
        
    def create_superuser(self, email, username, email_password, password):
        user = self.create_user(
            email=self.normalize_email(email),
			password=password,
			username=username,
            email_password=email_password,
		)
        user.is_admin = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    email 					= models.EmailField(verbose_name="email", max_length=60, unique=True)
    username 				= models.CharField(max_length=30, unique=True)
    email_password			= models.CharField(max_length=150, blank=True)
    first_name 				= models.CharField(max_length=150, blank=True)
    last_name 				= models.CharField(max_length=150, blank=True)
    date_joined				= models.DateTimeField(verbose_name='date joined', auto_now_add=True)
    last_login				= models.DateTimeField(verbose_name='last login', auto_now=True)
    is_admin				= models.BooleanField(default=False)
    is_active				= models.BooleanField(default=True)
    is_staff				= models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username','email_password']
    
    objects = MyAccountManager()

    def __str__(self): 
        return self.email

    # For checking permissions. to keep it simple all admin have ALL permissons
    def has_perm(self, perm, obj=None): 
        return self.is_admin

	# Does this user have permission to view this app? (ALWAYS YES FOR SIMPLICITY)
    def has_module_perms(self, app_label):
        return True

#class MyModel(models.Model):
#    email = DisposableEmailField()