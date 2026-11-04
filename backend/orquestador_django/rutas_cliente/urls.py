from django.urls import path
from . import views

urlpatterns = [
    path('optimizar/', views.solicitar_optimizacion, name='solicitar_optimizacion'),
]