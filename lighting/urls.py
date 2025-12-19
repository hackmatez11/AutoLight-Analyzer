"""
URL configuration for lighting app
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'lighting'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Upload
    path('upload/', views.upload_cad, name='upload'),
    
    # Results
    path('results/<int:cad_id>/', views.results, name='results'),
    
    # Project detail
    path('project/<int:cad_id>/', views.project_detail, name='project_detail'),
    
    # Reports
    path('report/<int:cad_id>/<str:report_type>/', views.generate_report, name='generate_report'),
    
    # AJAX endpoints
    path('api/update-fixture/', views.update_fixture_selection, name='update_fixture'),
    
    # Catalog
    path('catalog/', views.catalog_list, name='catalog'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='lighting/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='lighting:login'), name='logout'),
]
