from django.db import models

# Create your models here.

class Perguntas(models.Model):
    ALT_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]
    pergunta = models.CharField(max_length=200)
    alternativa_a = models.CharField(max_length=100)
    alternativa_b = models.CharField(max_length=100)
    alternativa_c = models.CharField(max_length=100)
    alternativa_d = models.CharField(max_length=100)
    resposta_correta = models.CharField(max_length=1, choices=ALT_CHOICES)

    def __str__(self):
        return self.pergunta