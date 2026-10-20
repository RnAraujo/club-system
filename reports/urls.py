from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportsIndexView.as_view(), name='index'),

    path('by-specialty-club/', views.ReportBySpecialtyAndClubView.as_view(), name='by_specialty_club'),
    path('by-specialty/', views.ReportBySpecialtyView.as_view(), name='by_specialty'),
    path('by-day/', views.ReportByDayView.as_view(), name='by_day'),

    path('export/by-specialty-club.csv', views.export_by_specialty_club_csv, name='export_specialty_club'),
    path('export/by-specialty.csv', views.export_by_specialty_csv, name='export_specialty'),
    path('export/by-day.csv', views.export_by_day_csv, name='export_by_day'),
]