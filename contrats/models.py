from django.db import models

class Contrats(models.Model):
    numero_attestation=models.CharField(primary_key=True,max_length=100)
    numero_police = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    motif_reserve = models.TextField(null=True, blank=True)
    date_effet = models.TextField(null=True, blank=True)
    date_emission = models.TextField(null=True, blank=True)
    date_controle = models.TextField(null=True, blank=True)
    type_controle = models.TextField(null=True, blank=True)
    statut_controle = models.TextField(null=True, blank=True)
    agence = models.TextField(null=True, blank=True)
    type_mouvement = models.TextField(null=True, blank=True)
    branche = models.TextField(null=True, blank=True)
    produit = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'Contrats'  
        managed = False      

    def __str__(self):
        return self.numero_police