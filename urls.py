"""NWP URL configurations"""

from django.urls import path
from nwp import views


app_name = 'nwp'
urlpatterns = [
    path('', views.home, name='home'),
    path('play/', views.play, name='play'),
    path('get_sentence/', views.get_sentence, name='get_sentence'),
    path('save_guesses/', views.save_guesses, name='save_guesses')
]
