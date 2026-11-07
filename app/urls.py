"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
"""
from django.contrib import admin
from django.urls import include, path

from accounts.views import ApresentacaoView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', ApresentacaoView.as_view(), name='home'),  # apresentação (ou início, se já entrou)
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('game/', include('game.urls', namespace='game')),
]
