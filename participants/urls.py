from django.urls import path
from . import views

app_name = 'participants'

urlpatterns = [
    path('', views.ParticipantListView.as_view(), name='list'),
    path('create/', views.ParticipantCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ParticipantDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.ParticipantUpdateView.as_view(), name='update'),
]