from django.db import models
from companies.models import Company

class GroupPlacement(models.Model):
    name=models.CharField(max_length=100)
    description=models.CharField(max_length=500,blank=True)
    notes=models.CharField(max_length=300,blank=True)
    company=models.ForeignKey(Company, on_delete=models.CASCADE)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'company'], name="Group_Unique"),   
        ]
    def _str_(self):
        return self.name
