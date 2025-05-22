from django.db import models

class Contrat(models.Model):
    numero_police = models.CharField(max_length=100)
    acte_gestion = models.CharField(max_length=100)
    numero_acte = models.CharField(max_length=100)
    date_boc = models.DateField(null=True, blank=True)
    statut_controle = models.CharField(max_length=100, default='Non contrôlé')
    motif_reserve = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.numero_police
