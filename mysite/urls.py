from django.contrib import admin
from django.urls import path, include
from reports.views import DashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', DashboardView.as_view(), name='dashboard'),
    path('accounts/', include('accounts.urls')),
    path('clubs/', include('clubs.urls')),
    path('participants/', include('participants.urls')),
    path('specialties/', include('specialties.urls')),
    path('registrations/', include('registrations.urls')),
    path('reports/', include('reports.urls')),
]