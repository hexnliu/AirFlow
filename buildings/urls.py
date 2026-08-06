from django.urls import path
from django.urls.resolvers import URLPattern
from . import views

app_name="Building"

urlpatterns=[
    # path('',views.index,name='index'),
    # handle Country,Province, City requst
    path('building_embeded/<int:id>', views.EmbedBuildingDetailView, name='building_embeded'),
    path('building_detail/<int:id>', views.BuildingDetailView.as_view(), name='building_detail'),
    path('get_country_province_city/',views.get_country_province_city,name='get_country_province_city'),
    path('create_building/',views.create_building,name='create_building'),
    path('update_building/<int:id>',views.update_building,name='update_building'),
    path('delete_building/<int:id>',views.delete_building,name='delete_building'),
    path('upload_floor_plan/<int:id>',views.upload_floor_plan,name='upload_floor_plan'),
    path('edit_floor_plan/<int:id>',views.edit_floor_plan,name='edit_floor_plan'),
    path('delete_floor_plan/<int:id>',views.delete_floor_plan,name='delete_floor_plan'),
    path('upload_floor_plans/<int:id>',views.UploadFloorPlans.as_view(),name='upload_floor_plans'),
#    admin
    path('get-province',views.getProvince, name='get-province'),
    path('get-city',views.getCity, name='get-city'),
]