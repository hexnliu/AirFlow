from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from django.views.generic import TemplateView,ListView,DetailView
from django.contrib.auth.mixins import LoginRequiredMixin #require password to login lib
from companies.dynamic import *
from django.contrib.auth.decorators import login_required
from groups.models import *
# group in sensor placement


def get_group_vars(request):
    """
    Get the post request information to handle the group
    Parameters:
        request: post request (name, description,notes,company)
    Rerturns:
        name(string): name of the group
        description(String): description of the group
        notes(string): notes for the group
        company_entry(Company): company object
    """
    name=request.POST.get("name",None)
    description=request.POST.get("description",None)  
    notes=request.POST.get("notes",None) 
    #note the company information is hidden in template-> this get the company information for the task 
    company = request.POST.get("company",None)    
    company_entry = Company.objects.get(id=int(company))
    return name,description,notes,company_entry


@login_required(login_url='login')
def add_group(request):
    """
    Add group definition to the database
    URL: /groups/add_group
    Post request parameters:
        name(string): name of the group
        description (String): description of the group
        notes(string): notes for the group
        company(string): company name
    Returns:
	    Page Redirect

    """
    name,description,notes,company_entry = get_group_vars(request)  #get the post request data
    # get all current group placement data  
    value_list = GroupPlacement.objects.filter(company=company_entry).values_list('name',flat=True)
    #check if the data exits or not, if not add it, otherwise update it
    if name !='' and name not in value_list:
        grp_entry = GroupPlacement(name=name,description=description,notes=notes,company=company_entry)
        grp_entry.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='login')
def edit_group(request,id):
    """
    Edit group definition from the database
    URL: /groups/edit_group/<int:id>
    Parameters:
        Id: group placement id
    Post request parameters:
    name(string): name of the group
    description (String): description of the group
    notes(string): notes for the group
    company(string): company name
    Returns:
        Page Redirect

    """

    name,description,notes,company_entry = get_group_vars(request) #get the request data   
    current_obj=GroupPlacement.objects.filter(id=id)#get the object that need to be updated
    if name !='':
        current_obj.update(name=name,description=description,notes=notes,company=company_entry)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='login')
def delete_group(request,id):
    """
    Delete groups from the database
    URL:/delete_group/<int:id>
    Parameters:
        Id: group placement id
    Returns:
        Page Redirect

    """
    GroupPlacement.objects.filter(id=id).delete() #remove the value from database
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))