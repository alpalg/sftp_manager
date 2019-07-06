from django.db import models
from django import forms
from django.contrib.auth.models import User

# Create your models here.


class Connection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    host = models.CharField(max_length=30)
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.username}@{self.host}'

    def set_user(self, value):
        self.user = value
