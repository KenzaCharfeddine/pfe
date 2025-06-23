from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [

    path('', views.root_redirect, name='root_redirect'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

   
    path('user/', views.home, name='user_home'),


    path('admin/', views.admin_home, name='admin_home'),
   

    path('user-add/', views.user_add, name='user_add'),
    path('user-delete/', views.user_delete, name='user_delete'),
    path('user-modify/', views.user_modify, name='user_modify'),


    path('recherche/', views.recherche, name='recherche'),
    path('update-contrat/', views.update_contrat, name='update_contrat'),
    # path('valider-controle/<int:contrat_id>/', views.valider_controle, name='valider_controle'),  # à activer si tu l'utilises
    
    path('contrat-add/', views.contrat_add, name='contrat_add'),
    path('contrat-delete/', views.contrat_delete, name='contrat_delete'),
    path('contrat-modify/', views.contrat_modify, name='contrat_modify'),
]
