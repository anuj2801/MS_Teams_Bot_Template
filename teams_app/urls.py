from django.contrib import admin
from django.urls import path
from teams_app import views

urlpatterns = [
    path('webhook', views.webhook.as_view(), name='webhook'),
]
