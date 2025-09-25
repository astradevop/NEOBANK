from django.db import models

# Create your models here.
class UserManager(BaseUserManager):
    use_in_migrations = True

