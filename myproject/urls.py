
from django.contrib import admin
from . import views
from django.urls import path, include
from django.urls import path



urlpatterns = [
    # path('admin/', admin.site.urls),
    path('user/', views.home, name='user_home'),
    path('login/', views.login_view, name='login'),
    path('admin/', views.admin_home, name='admin_home'),
    path('admin/user-management/', views.user_management, name='user_management'),
    path('user-add/', views.user_add, name='user_add'),
    path('user-delete/', views.user_delete, name='user_delete'),
    path('user-modify/', views.user_modify, name='user_modify'),
    path('recherche/', views.recherche, name='recherche'),
    path('lancer-controle/', views.lancer_controle, name='lancer_controle'),
    path('valider-controle/<int:contrat_id>/', views.valider_controle, name='valider_controle'),
    path('logout/', views.logout_view, name='logout'),


]
