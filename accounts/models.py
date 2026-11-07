from django.db import models

# Create your models here.

class Account(models.Model):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=50)
    codigo_aluno = models.CharField(max_length=20, unique=True)

    class Meta:
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'

    def __str__(self):
        return self.username
