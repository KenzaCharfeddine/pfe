from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import random
import string
from django.db.models import Q
from django.db import models 
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect 
from contrats.models import Contrats

def logout_view(request):
    logout(request)
    return redirect('login')

def home(request):
    return render(request, 'home.html') 

@login_required
def admin_home(request):
    return render(request, 'adminHome.html')


def generate_password(length=12):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))


def login_view(request):
    if request.method == 'POST':
        username_or_email = request.POST['username']
        password = request.POST['password']

        # Essayer de trouver l'utilisateur via email ou username
        try:
            user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
        except User.DoesNotExist:
            user = None

        if user:
            user = authenticate(request, username=user.username, password=password)
            if user:
                login(request, user)
                if user.is_superuser:
                    return redirect('admin_home') 
                else:
                    descriptions =Contrats.objects.values_list('description', flat=True).order_by('description').distinct()
                    return render(request, 'home.html', {'descriptions': descriptions})
        return render(request, 'login.html', {'error': "Identifiants incorrects."})
    return render(request, 'login.html')

def user_management(request):
    users = User.objects.all()
    user_to_modify = None
    if 'user_id' in request.GET:
        user_to_modify = get_object_or_404(User, id=request.GET['user_id'])
    return render(request, 'user_management.html', {
        'users': users,
        'user_to_modify': user_to_modify
    })

def user_add(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        role = request.POST['role']
        # password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        password = '123'
        user = User.objects.create_user(username=username, email=email, password=password)
        if role == 'Admin':
            user.is_staff = True
            user.is_superuser = True
        user.save()

        messages.success(request, f"Utilisateur {username} ajouté avec mot de passe : {password}")
    return redirect('user_management')

def user_delete(request):
    if request.method == 'POST':
        user_id = request.POST['user_id']
        user = get_object_or_404(User, id=user_id)
        user.delete()
        messages.success(request, "Utilisateur supprimé.")
    return redirect('user_management')


def user_modify(request):
    if request.method == 'GET':
        users = User.objects.order_by('username')
        u_to_mod = request.GET.get('user_id')
        user_to_modify = get_object_or_404(User, pk=u_to_mod) if u_to_mod else None
        return render(request, 'user_management.html', {
  # <-- Ici le bon nom du template
            'users': users,
            'user_to_modify': user_to_modify
        })

    # POST (modification de l’utilisateur)
    u = get_object_or_404(User, pk=request.POST['user_id'])
    email = request.POST.get('email')
    if email:
        u.email = email
    new_pw = generate_password()
    u.set_password(new_pw)
    u.save()
    messages.success(request, f"Nouveau mot de passe pour {u.username} : {new_pw}")
    return redirect('user_management')  # <-- Redirige vers la vue user_management (pas un template) 


from django.contrib import messages

from django.http import JsonResponse

from datetime import datetime

def format_date_to_ddmmyyyy(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return ""
    
def recherche(request):
    if request.method == 'POST':
        police = request.POST.get('numero_police')
        desc = request.POST.get('description')
        date_effet = format_date_to_ddmmyyyy(request.POST.get('date_effet'))
        date_emission = format_date_to_ddmmyyyy(request.POST.get('date_emission'))


        if police and desc and date_effet and date_emission:
            contrats = list(Contrats.objects.filter(
                numero_police__icontains=police,
                description__icontains=desc,
                date_effet__icontains=date_effet,
                date_emission__icontains=date_emission
            ).values())
            
            return JsonResponse({'success': True, 'contrats': contrats})
        else:
            return JsonResponse({'success': False, 'message': 'Veuillez remplir tous les champs.'})
    return JsonResponse({'success': False, 'message': 'Requête invalide.'})


def lancer_controle(request):
    if request.method == 'POST':
        contrat_id = request.POST.get('contrat_id')
        contrat = get_object_or_404(Contrats, id=contrat_id)
        return render(request, 'controle.html', {'contrat': contrat})
    
def valider_controle(request, contrat_id):
    contrat = get_object_or_404(Contrats, id=contrat_id)

    if request.method == 'POST':
        contrat.date_boc = request.POST.get('date_boc')
        contrat.statut = request.POST.get('statut')
        contrat.motif_reserve = request.POST.get('motif_reserve')
        contrat.save()
        return render(request, 'confirmation.html', {'contrat': contrat})

