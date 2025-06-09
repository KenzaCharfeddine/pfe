from django.db import models

class Contrats(models.Model):
    numero_attestation=models.IntegerField(primary_key=True)
    numero_police = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    motif_reserve = models.TextField(null=True, blank=True)
    date_effet = models.TextField(null=True, blank=True)
    date_emission = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'Contrats'  
        managed = False      

    def __str__(self):
        return self.numero_police