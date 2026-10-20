from django.urls import path
from . import views

app_name = 'clubs'

urlpatterns = [
    path('', views.ClubListView.as_view(), name='list'),
    path('create/', views.ClubCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ClubDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.ClubUpdateView.as_view(), name='update'),
    path('directives/', views.DirectiveListView.as_view(), name='directive_list'),
    path('directives/create/', views.DirectiveCreateView.as_view(), name='directive_create'),
]