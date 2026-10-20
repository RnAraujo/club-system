from django.urls import path
from . import views

app_name = 'clubs'

urlpatterns = [
    # Clubes
    path('', views.ClubListView.as_view(), name='list'),
    path('create/', views.ClubCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ClubDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.ClubUpdateView.as_view(), name='update'),

    # Directiva
    path('directives/', views.DirectiveListView.as_view(), name='directive_list'),
    path('directives/create/', views.DirectiveCreateView.as_view(), name='directive_create'),
    path('directives/<int:pk>/update/', views.DirectiveUpdateView.as_view(), name='directive_update'),
    path('directives/<int:pk>/delete/', views.DirectiveDeleteView.as_view(), name='directive_delete'),
]