# monitoring/urls.py
from django.urls import path
from . import views
from .utils import role_required
from .views import (
    CustomLoginView,
    CustomLogoutView,
    MachineListView,
    MachineDetailView,
)

app_name = 'monitoring'

urlpatterns = [
    # Машины
    path('machines/',
         role_required(['client', 'service', 'manager'])(views.MachineListView.as_view()),
         name='machine_list'),

    path('machine/<int:pk>/',
         role_required(['client', 'service', 'manager'])(views.MachineDetailView.as_view()),
         name='machine_detail'),

    path('machine/<int:pk>/edit/',
         role_required(['manager'])(views.MachineUpdateView.as_view()),
         name='machine_edit'),

    path('machine/add/', views.MachineCreateView.as_view(), name='machine_add'),

    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('search/', views.MachineSearchView.as_view(), name='machine_search'),

    # Техническое обслуживание
    path('technical-services/',  # Новый путь для списка ТО
         role_required(['client', 'service', 'manager'])(views.TechnicalServiceListView.as_view()),
         name='technical_service_list'),

    path('technical-service/create/<int:machine_id>/',
         role_required(['client', 'service', 'manager'])(views.TechnicalServiceCreateView.as_view()),
         name='service_create'),

    path('technical-service/<int:pk>/',  # Новый путь для деталей ТО
         role_required(['client', 'service', 'manager'])(views.TechnicalServiceDetailView.as_view()),
         name='technical_service_detail'),

    path('technical-service/<int:pk>/edit/',
         role_required(['client', 'service', 'manager'])(views.TechnicalServiceUpdateView.as_view()),
         name='service_edit'),

    # Рекламации
    path('reclamations/',  # Новый путь для списка рекламаций
         role_required(['client', 'service', 'manager'])(views.ReclamationListView.as_view()),
         name='reclamation_list'),

    path('reclamation/create/<int:machine_id>/',
         role_required(['service', 'manager'])(views.ReclamationCreateView.as_view()),
         name='reclamation_create'),

    path('reclamation/<int:pk>/',  # Новый путь для деталей рекламации
         role_required(['client', 'service', 'manager'])(views.ReclamationDetailView.as_view()),
         name='reclamation_detail'),

    path('reclamation/<int:pk>/edit/',
         role_required(['service', 'manager'])(views.ReclamationUpdateView.as_view()),
         name='reclamation_edit'),

    # Справочники
    path('references/',
         role_required(['client', 'service', 'manager'])(views.ReferenceListView.as_view()),
         name='reference_list'),

    path('references/add/',
         role_required(['manager'])(views.ReferenceCreateView.as_view()),
         name='reference_add'),

    path('references/<int:pk>/edit/',
         role_required(['manager'])(views.ReferenceUpdateView.as_view()),
         name='reference_edit'),
]