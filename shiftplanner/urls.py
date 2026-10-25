from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from apps.planning import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('anmelden/', auth_views.LoginView.as_view(template_name='planning/login.html', extra_context={'demo_mode': settings.DEBUG}), name='login'),
    path('abmelden/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('bedarf/', views.demand, name='demand'),
    path('vorlagen/', views.templates, name='templates'),
    path('qualifikationen/', views.qualifications, name='qualifications'),
    path('verfuegbarkeiten/', views.availability_overview, name='availability_overview'),
    path('meine-verfuegbarkeiten/', views.availability, name='availability'),
    path('verfuegbarkeiten/<int:employee_id>/', views.availability, name='employee_availability'),
    path('plan/erzeugen/', views.generate, name='generate'),
    path('plan/', views.plan, name='plan'),
    path('plan/unbesetzt/', views.unfilled, name='unfilled'),
]
handler403 = 'apps.planning.views.forbidden'
