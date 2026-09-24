from django.urls import path
from django.urls.resolvers import URLPattern
from . import views

urlpatterns=[
    path('add_group/',views.add_group,name='add_group'),
    path('edit_group/<int:id>',views.edit_group,name='edit_group'),
    path('delete_group/<int:id>',views.delete_group,name='delete_group'),
   
]