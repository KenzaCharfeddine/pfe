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
                return redirect('recherche')
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
    return redirect('recherche')


def logout_view(request):
    logout(request)
    return redirect('login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('admin_home' if request.user.is_superuser else 'recherche')

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
                return redirect('admin_home' if user.is_superuser else 'recherche')

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
        descriptions = Contrats.objects.values_list('description', flat=True).distinct().order_by('description')
        return render(request, 'contrats_management.html', {'contrats': contrats,'descriptions':descriptions})

    return render(request, 'adminHome.html')


@login_required(login_url='login')
def recherche(request):
    descriptions = Contrats.objects.values_list('description', flat=True).distinct().order_by('description')
    return render(request, 'recherche.html', {'descriptions': descriptions})


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


def rechercheContrat(request):
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
        date_effet = request.POST.get('date_effet') 
        date_emission = request.POST.get('date_emission')
        date_controle = request.POST.get('date_control')
        type_controle = request.POST.get('type_control')
        statut_controle = request.POST.get('statut_control')
        motif_reserve = request.POST.get('motif_reserve')

        def parse_date(date_str):
            """
            Tente de parser date_str en format dd/MM/YYYY ou YYYY-MM-DD,
            retourne la date formatée en dd/MM/YYYY ou None si invalide.
            """
            for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(date_str, fmt).strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    continue
            return None

        # Parsing + formatage
        date_effet_fmt = parse_date(date_effet)
        date_emission_fmt = parse_date(date_emission)
        date_controle_fmt = parse_date(date_controle) if date_controle else None

        # Validation
        if not all([numero_police, description, date_effet_fmt, date_emission_fmt]):
            return JsonResponse({'success': False, 'message': "Champs obligatoires manquants ou dates invalides."})
        if date_controle and not date_controle_fmt:
            return JsonResponse({'success': False, 'message': "Date de contrôle invalide (jj/mm/aaaa ou aaaa-mm-jj)."})

        try:
            contrat = Contrats.objects.get(
                numero_police=numero_police,
                description=description,
                date_effet=date_effet_fmt,
                date_emission=date_emission_fmt
            )
        except Contrats.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Contrat non trouvé.'})

        # Mise à jour des champs (dates en dd/MM/YYYY)
        contrat.date_effet = date_effet_fmt
        contrat.date_emission = date_emission_fmt
        contrat.date_controle = date_controle_fmt
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
    data = request.POST
    numero_attestation = data.get('numero_attestation')
    numero_police = data.get('numero_police')
    description = data.get('description')
    agence = data.get('agence')
    type_mouvement = data.get('type_mouvement')
    branche = 'AUTO'
    produit = 'Auto Particulier'
    date_effet_raw = data.get('date_effet')
    date_emission_raw = data.get('date_emission')

    try:
        date_effet = datetime.strptime(date_effet_raw, "%Y-%m-%d").strftime("%d/%m/%Y")
        date_emission = datetime.strptime(date_emission_raw, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return JsonResponse({'success': False, 'message': "Dates invalides."})

    if not all([numero_attestation, numero_police, description, agence, type_mouvement]):
        return JsonResponse({'success': False, 'message': "Tous les champs doivent être remplis."})

    if Contrats.objects.filter(numero_attestation=numero_attestation).exists():
        return JsonResponse({'success': False, 'message': f"Contrat '{numero_attestation}' existe déjà."})

    contrat = Contrats.objects.create(
        numero_attestation=numero_attestation,
        numero_police=numero_police,
        description=description,
        agence=agence,
        type_mouvement=type_mouvement,
        branche=branche,
        produit=produit,
        date_effet=date_effet,
        date_emission=date_emission
    )

    return JsonResponse({
        'success': True,
        'message': f"Contrat '{numero_attestation}' ajouté.",
        'contrat': {
            'numero_attestation': contrat.numero_attestation,
            'numero_police': contrat.numero_police,
            'description': contrat.description,
            'agence': contrat.agence,
            'type_mouvement': contrat.type_mouvement,
            'branche': contrat.branche,
            'produit': contrat.produit,
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
    data = request.POST
    numero_attestation = data.get('numero_attestation')
    contrat = get_object_or_404(Contrats, numero_attestation=numero_attestation)

    contrat.numero_police = data.get('numero_police', contrat.numero_police)
    contrat.description = data.get('description', contrat.description)
    contrat.agence = data.get('agence', contrat.agence)
    contrat.type_mouvement = data.get('type_mouvement', contrat.type_mouvement)

    def dt_str(raw):
        dt = parse_date(raw)
        return dt.strftime("%d/%m/%Y") if dt else None

    if data.get('date_effet'):
        contrat.date_effet = dt_str(data['date_effet']) or contrat.date_effet
    if data.get('date_emission'):
        contrat.date_emission = dt_str(data['date_emission']) or contrat.date_emission

    contrat.save()

    return JsonResponse({
        'success': True,
        'message': f"Contrat '{numero_attestation}' mis à jour.",
        'contrat': {
            'numero_attestation': contrat.numero_attestation,
            'numero_police': contrat.numero_police,
            'description': contrat.description,
            'agence': contrat.agence,
            'type_mouvement': contrat.type_mouvement,
            'branche': contrat.branche,
            'produit': contrat.produit,
            'date_effet': contrat.date_effet,
            'date_emission': contrat.date_emission,
        }
    })
    
def parse_date(date_str):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except:
            pass
    return None