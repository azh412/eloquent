from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    rating = models.IntegerField(default=1200)