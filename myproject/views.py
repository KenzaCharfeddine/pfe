import json
import random
import string
from datetime import datetime
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from datetime import datetime
from contrats.models import Contrats


# === Décorateurs ===

def admin_required_redirect(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            if not request.user.is_superuser:
                return redirect('user_home')
        else:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def user_required_redirect(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return redirect('admin_home')
        else:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


# === Authentification & Navigation ===

def root_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_superuser:
        return redirect('admin_home')
    return redirect('user_home')


def logout_view(request):
    logout(request)
    return redirect('login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('admin_home' if request.user.is_superuser else 'user_home')

    if request.method == 'POST':
        username_or_email = request.POST['username']
        password = request.POST['password']

        try:
            user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
        except User.DoesNotExist:
            user = None

        if user:
            user = authenticate(request, username=user.username, password=password)
            if user:
                login(request, user)
                return redirect('admin_home' if user.is_superuser else 'user_home')

        return render(request, 'login.html', {'error': "Identifiants incorrects.",'username': username_or_email })

    return render(request, 'login.html')


@login_required(login_url='login')
@admin_required_redirect
def admin_home(request):
    page = request.GET.get('page', 'users')

    if page == 'users':
        users = User.objects.all()
        return render(request, 'user_management.html', {'users': users})

    elif page == 'contracts':
        contrats = Contrats.objects.all().order_by("numero_attestation")
        return render(request, 'contrats_management.html', {'contrats': contrats})

    return render(request, 'adminHome.html')


@login_required(login_url='login')
@user_required_redirect
def home(request):
    descriptions = Contrats.objects.values_list('description', flat=True).distinct().order_by('description')
    return render(request, 'home.html', {'descriptions': descriptions})


# === Utilisateurs ===

def generate_password(length=12):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))


def user_add(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        role = request.POST.get('role')
        password = generate_password()

        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_superuser = role == 'Admin'
        user.is_staff = user.is_superuser
        user.save()

        messages.success(request, f"Utilisateur '{username}' ajouté avec succès. Mot de passe : {password}")
    return HttpResponseRedirect(reverse('admin_home') + '?page=users')


def user_delete(request):
    if request.method == 'POST':
        user_id = request.POST['user_id']
        user = get_object_or_404(User, id=user_id)
        user.delete()
        messages.success(request, "Utilisateur supprimé.")
    return HttpResponseRedirect(reverse('admin_home') + '?page=users')


def user_modify(request):
    if request.method == 'POST':
        user = get_object_or_404(User, pk=request.POST['user_id'])
        email = request.POST.get('email')
        if email:
            user.email = email
        new_pw = generate_password()
        user.set_password(new_pw)
        user.save()
        messages.success(request, f"Nouveau mot de passe pour {user.username} : {new_pw}")
        return HttpResponseRedirect(reverse('admin_home') + '?page=users')

    # GET
    return HttpResponseRedirect(reverse('admin_home') + '?page=users')


# === Contrats ===

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


def update_contrat(request):
    if request.method == 'POST':
        numero_police = request.POST.get('numero_police')
        description = request.POST.get('description')
        date_effet = request.POST.get('date_effet')  # attendu: dd/MM/YYYY
        date_emission = request.POST.get('date_emission')
        date_controle = request.POST.get('date_control')
        type_controle = request.POST.get('type_control')
        statut_controle = request.POST.get('statut_control')
        motif_reserve = request.POST.get('motif_reserve')

        def is_valid_ddmmyyyy(date_str):
            try:
                datetime.strptime(date_str, "%d/%m/%Y")
                return True
            except:
                return False
            
        try:    
            date_controle = datetime.strptime(date_controle, "%Y-%m-%d").strftime("%d/%m/%Y")
        except: 
            return JsonResponse({'success': False, 'message': "Date de contrôle invalide (jj/mm/aaaa)."})
            

        # Validation
        if not all([numero_police, description, date_effet, date_emission]):
            return JsonResponse({'success': False, 'message': "Champs de recherche manquants."})
        if not is_valid_ddmmyyyy(date_effet) or not is_valid_ddmmyyyy(date_emission):
            return JsonResponse({'success': False, 'message': "Dates effet et émission doivent être au format jj/mm/aaaa."})
        if date_controle and not is_valid_ddmmyyyy(date_controle):
            return JsonResponse({'success': False, 'message': "Date de contrôle invalide (jj/mm/aaaa)."})

        try:
            contrat = Contrats.objects.get(
                numero_police=numero_police,
                description=description,
                date_effet=date_effet,
                date_emission=date_emission
            )
        except Contrats.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Contrat non trouvé.'})

        contrat.date_controle = date_controle or None
        contrat.type_controle = type_controle or None
        contrat.statut_controle = statut_controle or None
        contrat.motif_reserve = motif_reserve or None
        contrat.save()

        return JsonResponse({'success': True, 'message': 'Contrat mis à jour avec succès.'})

    return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})


@login_required(login_url='login')
@admin_required_redirect
@require_http_methods(["POST"])
def contrat_add(request):
    numero_attestation = request.POST.get('numero_attestation')
    numero_police = request.POST.get('numero_police')
    description = request.POST.get('description')
    date_effet = request.POST.get('date_effet')  # format HTML: YYYY-MM-DD
    date_emission = request.POST.get('date_emission')  # format HTML: YYYY-MM-DD

    # Conversion en format dd/MM/YYYY pour stockage
    try:
        date_effet = datetime.strptime(date_effet, "%Y-%m-%d").strftime("%d/%m/%Y")
        date_emission = datetime.strptime(date_emission, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return JsonResponse({'success': False, 'message': "Les dates doivent être au format valide."})

    if not all([numero_attestation, numero_police, description, date_effet, date_emission]):
        return JsonResponse({'success': False, 'message': "Tous les champs doivent être remplis."})

    if Contrats.objects.filter(numero_attestation=numero_attestation).exists():
        return JsonResponse({'success': False, 'message': f"Le contrat avec l'attestation '{numero_attestation}' existe déjà."})

    contrat = Contrats(
        numero_attestation=numero_attestation,
        numero_police=numero_police,
        description=description,
        date_effet=date_effet,
        date_emission=date_emission,
        motif_reserve=None,
        date_controle=None,
        type_controle=None,
        statut_controle=None
    )
    contrat.save()

    return JsonResponse({
        'success': True,
        'message': f"Contrat '{numero_attestation}' ajouté avec succès.",
        'contrat': {
            'numero_attestation': contrat.numero_attestation,
            'numero_police': contrat.numero_police,
            'description': contrat.description,
            'date_effet': contrat.date_effet,
            'date_emission': contrat.date_emission,
        }
    })
   
    
@login_required(login_url='login')
@admin_required_redirect
@require_http_methods(["POST"])
def contrat_delete(request):
    numero_attestation = request.POST.get('numero_attestation')
    contrat = get_object_or_404(Contrats, numero_attestation=numero_attestation)
    contrat.delete()
    return JsonResponse({'success': True, 'message': f"Contrat '{numero_attestation}' supprimé."})


@login_required(login_url='login')
@admin_required_redirect
@require_http_methods(["POST"])
def contrat_modify(request):
    numero_attestation = request.POST.get('numero_attestation')
    contrat = get_object_or_404(Contrats, numero_attestation=numero_attestation)

    contrat.numero_police = request.POST.get('numero_police', contrat.numero_police)
    contrat.description = request.POST.get('description', contrat.description)
    contrat.date_effet = request.POST.get('date_effet', contrat.date_effet)
    contrat.date_emission = request.POST.get('date_emission', contrat.date_emission)

    # Plus de gestion des champs supprimés (motif_reserve, date_controle, etc.)

    contrat.save()
    messages.success(request, f"Contrat '{numero_attestation}' modifié avec succès.")
    return HttpResponseRedirect(reverse('admin_home') + '?page=contracts')
