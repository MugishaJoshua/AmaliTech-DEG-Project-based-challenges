from django.urls import path 
from . import views

urlpatterns = [
    path('process-payment', views.process_payment, name='process_payment'),
    path('', views.dashboard, name='Dashboard')
]