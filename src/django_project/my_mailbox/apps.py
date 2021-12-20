from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MyMailboxConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'my_mailbox'
    verbose_name = _("My MailBox")
