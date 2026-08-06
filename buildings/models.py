from django.db import models
from companies.models import Company
from accounts.storage import OverwriteStorage
from django.conf import settings 

#path for Building
def building_path(instance,filename):
    buildingId=instance.id
    if instance.id == None:
        building = Building.objects.last()
        buildingId = int(building.id)+1
    return settings.MEDIA_ROOT + '/{0}/{1}'.format(buildingId, 'building.png')

# path for BuildingImages
def floor_path(instance,filename): 
    return settings.MEDIA_ROOT + '/{0}/{1}'.format(instance.building.id, filename)
    
class Building(models.Model):
    name = models.CharField(max_length=50,verbose_name="Building Name")
    address= models.CharField(max_length=300,blank=True)
    postal = models.CharField(max_length=30,verbose_name="Postal Code")
    city = models.CharField(max_length=20,blank=True)
    province = models.CharField(max_length=20,blank=True)
    country = models.CharField(max_length=20,blank=True)
    phone = models.CharField(max_length=20,blank=True)
    email= models.EmailField(max_length=30,blank=True)
    contact= models.CharField(max_length=30,blank=True)   
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    img=models.ImageField(upload_to=building_path,blank=True,max_length=5000, storage=OverwriteStorage())  
    img_path=models.CharField(max_length=200,blank=True)  
    is_active=models.BooleanField(default=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'company'], name="Building_Unique"),   
        ]
    def _str_(self):
        return self.name

class BuildingImages(models.Model):
    building= models.ForeignKey(Building, on_delete=models.CASCADE,verbose_name="Building Name")
    floor_building=models.CharField(max_length=5)
    width=models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    height=models.DecimalField(max_digits=10, decimal_places=2,blank=True)    
    date=models.DateField()
    img=models.ImageField(upload_to=floor_path,blank=True,max_length=5000, storage=OverwriteStorage())
    img_path=models.CharField(max_length=50,blank=True)
    def _str_(self):
        return self.building

