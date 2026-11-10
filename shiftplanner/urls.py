"""URL-Routen von ShiftPlanner (deutschsprachige Pfade)."""

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from apps.planning import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'anmelden/',
        auth_views.LoginView.as_view(
            template_name='planning/login.html',
            extra_context={'demo_mode': settings.DEBUG or settings.PUBLIC_DEMO},
        ),
        name='login',
    ),
    path('abmelden/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('zeitraum/', views.period, name='period'),
    path('bedarf/', views.demand, name='demand'),
    path('oeffnungstage/', views.opening, name='opening'),
    path('vorlagen/', views.templates, name='templates'),
    path('mitarbeitende/', views.employees, name='employees'),
    path('qualifikationen/', views.qualifications, name='qualifications'),
    path('verfuegbarkeiten/', views.availability_overview, name='availability_overview'),
    path('meine-verfuegbarkeiten/', views.availability, name='availability'),
    path('verfuegbarkeiten/<int:employee_id>/', views.availability, name='employee_availability'),
    path('mein-schichtplan/', views.employee_plan, name='employee_plan'),
    path('plan/veroeffentlichen/', views.publish, name='publish'),
    path('plan/erzeugen/', views.generate, name='generate'),
    path('plan/', views.plan, name='plan'),
    path(
        'plan/position/<int:assignment_id>/', views.correct_assignment, name='correct_assignment'
    ),
    path('plan/unbesetzt/', views.unfilled, name='unfilled'),
]
handler403 = 'apps.planning.views.forbidden'
