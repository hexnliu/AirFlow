from django.contrib import admin
from . models import Building
from django.contrib.auth.models import User
import os
from companies.forms import *
from .forms import *
from os.path import dirname
@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):  
  
  list_display =("name","address","postal","city","province","country","phone","email","contact","building_company")
  list_filter =("name","city","province","country","contact","company_id__name")
  search_fields = ['name',"address","postal",'city',"province","country","phone","email","contact","company_id__name"]
  fields = ("company","name","country","province","city","address","postal","phone","email","contact","img","img_path")
  def building_company(self,obj):
        return obj.company.name
  def formfield_for_foreignkey(self, db_field, request, **kwargs):
      if db_field.name == 'company':
        return CompanyChoiceField(queryset=Company.objects.all())
      elif db_field.name == 'user':
        return UserChoiceField(queryset=User.objects.all())
  def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        form.base_fields['country'] = forms.ChoiceField(
                    choices = get_country(),
                    required = False,
                    label='Country',
                    widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_country'}),
                    )
        country=None
        province =None
        if obj is not None:
          country=obj.country
          province=obj.province
        #note that in order to pass the validation, this need to include all possible options
        form.base_fields['province'] = forms.ChoiceField(
                choices = return_state_by_country(country,True),
                required = False,
                label='Province',
                widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_province'}),
                )
        form.base_fields['city'] = forms.ChoiceField( 
                choices = return_city_by_country_state(country,province,True),
                required = False,
                label='City',
                widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_city'}),
            )

        return form
  def save_model(self, request, obj, form, change):
    current_location=r"{}/{}/{}".format(dirname(os.path.dirname(__file__)),'media',obj.id)
    if not os.path.exists(current_location):
      os.makedirs(current_location)
    if obj.img !="":
      name=obj.img.name
      obj.save()
      file_path = "/media/"+str(obj.id)+"/building.png"
      obj.img_path=file_path
    else:
      obj.img_path=""
    super(BuildingAdmin, self).save_model(request, obj, form, change) 
    # add js script to get ajax response
  class Media:
        js = (
            '//ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js', # jquery
            'js/admin.js',       # project static folder
        )   