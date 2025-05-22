
from django.contrib import admin
from . import views
from django.urls import path, include
from django.urls import path



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('user-management/', views.user_management, name='user_management'),
    path('user-add/', views.user_add, name='user_add'),
    path('user-delete/', views.user_delete, name='user_delete'),
    path('user-modify/', views.user_modify, name='user_modify'),
    path('recherche/', views.rechercher_contrats, name='rechercher_contrats'),
    path('lancer-controle/', views.lancer_controle, name='lancer_controle'),
    path('valider-controle/<int:contrat_id>/', views.valider_controle, name='valider_controle'),
    

]
