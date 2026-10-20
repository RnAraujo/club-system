from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('by-specialty-club/', views.ReportBySpecialtyAndClubView.as_view(), name='by_specialty_club'),
    path('by-specialty/', views.ReportBySpecialtyView.as_view(), name='by_specialty'),
    path('by-day/', views.ReportByDayView.as_view(), name='by_day'),
    path('export/by-specialty-club.csv', views.export_by_specialty_club_csv, name='export_specialty_club'),
]