from django.urls import path
from scrap import views



urlpatterns = [
    path('', views.index, name='index'),
]
