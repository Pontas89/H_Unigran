from django.db import models

# Create your models here.

class Perguntas(models.Model):
    pergunta = models.CharField(max_length=200)

    def __str__(self):
        return self.pergunta

class Resposta(models.Model):

    CHOICES_TIPO = [
        ('certa', 'Certa'),
        ('errada', 'Errada'),
    ]
    pergunta = models.ForeignKey(Perguntas, on_delete=models.CASCADE)
    resposta_correta = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=CHOICES_TIPO)

    def __str__(self):
        return self.resposta_correta 
    