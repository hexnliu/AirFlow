from asyncio import current_task
# from distutils.command.build import build
from genericpath import exists
from json.encoder import INFINITY
from django.shortcuts import render,get_object_or_404
from django.http import HttpResponse,HttpResponseRedirect
import os,json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from buildings.models import Building
from companies.dynamic import *
from tasks.models import *
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView,ListView,DetailView
from inventory.views import *
import datetime
from tasks.views import navigation_context, get_task_links
import buildings.forms as admin_js
from django.views.decorators.clickjacking import xframe_options_exempt

class BuildingDetailView(LoginRequiredMixin,DetailView):
  """
    Display the selected building information and associated tasks in html 
    URL:  /buildings/building_detail/<int:id> 
    Parameters:
      id(int): building id
    Returns:
      HTML page that contains building information and associated tasks
  """
  model = Building #get the building model
  template_name = 'buildings/index.html'
  def get(self, request, *args, **kwargs):
    context={}
    building =Building.objects.get(id=kwargs['id'])
    context=navigation_context(request,building,None,True,context)
    # maker sure the building exists
    # if building:
      # get country data
    data= read_json("files/countries.json")
    states =None #get the states 
    cities = None
    for d in data:
      if d["name"] == building.country:
        states=d["states"] 
    
    for s in states:
      if s["name"] == building.province:
        cities=s["cities"]
    context["states"] = states # states lisst
    context["cities"] = cities # cities list
    context["breadcrumbs"]="Building"
    return render(request, self.template_name, context)

@xframe_options_exempt
def EmbedBuildingDetailView(request, id):
      """
        Display the selected building information for embeded purpose
        URL:  /buildings/building_embeded/<int:id> 
        Parameters:
          id(int): building id
        Returns:
          HTML page that contains building information 
      """
      context={}
      building =Building.objects.get(id=id)
      # maker sure the building exists
      # if building:
        # get country data
      data= read_json("files/countries.json")
      states =None #get the states 
      cities = None
      for d in data:
        if d["name"] == building.country:
          states=d["states"] 
      
      for s in states:
        if s["name"] == building.province:
          cities=s["cities"]
      context["states"] = states # states lisst
      context["cities"] = cities # cities list
      context["breadcrumbs"]="Building"
      context["building"]=building# get building
      tasks=Task.objects.filter(building=building)
      if tasks.count()>0: # if there is more than one task, get notification
          latest,context["notification_task"] =get_task_links(tasks,building.id,True)
          context["tasks_list"]=json.dumps(list(latest), default=str)
          context["tasks"]=latest
          current_task=tasks.last()
          context["task_id"]=current_task.id
          context["task"]=current_task
          context["status"]=current_task.status
          completed_tasks=Task.objects.filter(building=building,status_id=5)
          if completed_tasks.count()>0:
                context["status_task_id"]=completed_tasks.last().id
      return render(request, 'buildings/embed.html',context)


class UploadFloorPlans(LoginRequiredMixin,TemplateView):
     """
     Upload floor plan page for a building
     Paramters
      id(int): building id from the url
     """     
     template_name ="tasks/uploadFloorPlans.html"
     def get_context_data(self,**kwargs): 
      context = super(UploadFloorPlans, self).get_context_data(**kwargs)
      current_building=Building.objects.get(id=kwargs['id'])
      task=self.request.GET.get('task',None)
      current_task =None
      if task is not None:
          current_task =Task.objects.get(id=task)
          intersection,missing= get_floor_from_floor_plan(current_task) #prompt to add floor modal
          if len(missing)>0: #if missing exits
              context["missing"]=missing
      context=navigation_context(self.request,current_building,current_task,False,context)
      floor_plans = BuildingImages.objects.filter(building_id=kwargs['id'])
      context["floor_plans"]=floor_plans
      # filter out the floors selection
      a_list = get_floors_selections()
      existing_floors=list(floor_plans.values_list('floor_building', flat=True))
      for s in existing_floors:
        a_list.remove(int(s))
      context["floors"]=a_list
      # a list of the floors
      return context
      
def prompt_building_notification(request):
  """
    Prompt user notification if there is no buildings
    Parameters:
      request: request
    Returns:
      number: that indicate the notification number, none when there is no need to prompt
  """
  count_buildings=get_buildings_from_user(request) # get current building list based on user company
  if count_buildings.count()==0: # if there is no building, propmt the notification
    return 1
  else:
    return None

def get_floor_from_floor_plan(current_task):
   """
   Filter out the missing floor plans
   Parameters:
      current_task(Task): current task object
   Returns:
      intersection(list): a list of finished floors value
      missing(list): a list of missing floors value
   """
   floor_plans=BuildingImages.objects.filter(building=current_task.building)
   a_list= list(floor_plans.values_list('floor_building', flat=True)) # floor plans floors
   missing =[ value for value in ast.literal_eval(current_task.floor_list) if value not in set(a_list)]
   intersection=  [value for value in a_list if value in ast.literal_eval(current_task.floor_list)]
   return intersection,missing

def get_floors_selections():
  """
  Generate a list of numbers for floors selection from -2 - 20
  Returns:
    [-2,20]
  """
  a_list =list(range(-2, 21))
  a_list.remove(0)
  return a_list

def read_json(fileName):
  """
  Read json file
  Parameters:
    fileName(string): file name that is json format
  Returns:
    data(json): content of the data
  """
  current_path = os.path.abspath(os.path.dirname(__file__))  
  f= open(os.path.join(current_path,fileName),encoding="utf-8")
  data = json.load(f)
  f.close()
  return data

# for admin
def getProvince(request):
    """
    Get provinces data by selected country
    Parameters
    Returns:
      an object list of the provinces 
    """
    country = request.POST.get('country')
    provinces = admin_js.return_state_by_country(country)
    return JsonResponse({'provinces': provinces})

# for admin
def getCity(request):
    """
    Get city data from file
    Returns:
      an object list of the provinces 
    """
    country = request.POST.get('country')
    province = request.POST.get('province')
    cities = admin_js.return_city_by_country_state(country,province)
    return JsonResponse({'cities': cities})

@login_required(login_url='login')
def get_country_province_city(request):
  """
  Get a selection of country, province, and city (dependent dropdown)
  URL: buildings/get_country_province_city/
  Post request parameters:
    country(str): country'sname e.g., Canada 
    province(str): province'sname e.g., Manitoba 
  Note that, if both country and province are present, a list of cities will be returned. If only country value is present, a list of provinces will be returned.
  Returns:
    HTML select element will be returned with province'soptions or city'soptions.

  """
  templates="partials/render.html"
  #handle request
  countryId = request.POST.get("country",None) # counrty name
  print(countryId)
  provinceId = request.POST.get("province",None) # this is province id in the file
  # read json file
  data= read_json("files/countries.json")
  states=None # get current states list based on country
  cities =None
  current_province =None # get province by request province id
  options={} # conext object contains key and value ... key as select text
  # for loop the json file, finding the country
  for d in data:
    if d["name"] == countryId:
      print(d["name"])
      states=d["states"] # obtains states
      options={"key":"Select Province/ State","values":states}
  # this means requesting cities
  if provinceId is not None:
      #casting province since it should be number
      for s in states:
        if s["name"] == provinceId:
          current_province = s # obtain current province
          cities = current_province["cities"]
          options={"key":"Select City","values":cities}
  return  render(request, templates,{"options":options})


@login_required(login_url='login')
def create_building(request): 
  """
    Add a building into database
    URL: /buildings/create_building/
    Post request parameters:
      name(str): name of the building
      address(str): name of the address
      country(str): name of the country
      province(str): name of the province
      city(str): name of the city
      postalCode(str): postal code of the address
      phone(str) optional: phone number 
      email(str) optional: email address
      contact(str) optional: contact person'sname
      img (file) optional: image file 
    Returns:
      None
  """   
  name,address,postalCode,country,state,city,phone,email,contact,img_type,company_entry,img=get_building_vars(request)  
  b=Building(name=name,address=address,postal=postalCode,city=city,province=state,country=country,contact=contact,phone=phone,email=email,company=company_entry)
  b.save()
  if img !='':
    updateImages(b,img,b.id)
  return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='login')
def update_building(request,id): 
  """
    Update the building information
    URL: /buildings/update_building/<int:id>
    Parameters:
      id(int):building id
    Post request parameters:
      name(str): name of the building
      address(str): name of the address
      country(str): name of the country
      province(str): name of the province
      city(str): name of the city
      postalCode(str): postal code of the address
      phone(str) optional: phone number 
      email(str) optional: email address
      contact(str) optional: contact person'sname
      img (file) optional: image file 
      img_type(string) optional:[“change”,”current”,”delete”] note: change means update
    Returns:
      None
  """  
  name,address,postalCode,country,state,city,phone,email,contact,img_type,company_entry,img=get_building_vars(request)   
  Building.objects.filter(id=id).update(name=name,address=address,postal=postalCode,city=city,province=state,country=country,contact=contact,phone=phone,email=email)
  current_obj=Building.objects.get(id=id)
  if img_type !='current':    
    updateImages(current_obj,img,current_obj.id)
  return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def get_building_vars(request):
  """
  Get all building info from post request
  Parameters:
    request:request
  Returns:
     name(string): name of the building
     address(string):address of the building
     postalCode(string)
     country(string)
     state(string)
     city(string)
     postalCode(string)
     phone(string)
     email(string)
     contact(string)
     img_type(string): option either "change","current" and"delete"
     company_entry(Company)
     img(File)
     img_type(string): options from ["change","current"," delete"]
  """  
  name = request.POST.get('name', None)
  address = request.POST.get('address',None)
  postalCode = request.POST.get('postalCode',None)
  country = request.POST.get('country',None)
  state = request.POST.get('province',None)
  city = request.POST.get('city',None)
  phone = request.POST.get('phone',"")
  email = request.POST.get('email',"")
  contact = request.POST.get('contact',"")   
  img_type = request.POST.get('img_type',"") 
  company_entry = get_company_entry_from_request_user(request)
  img = request.FILES.get("img","")  
  return name,address,postalCode,country,state,city,phone,email,contact,img_type,company_entry,img



@login_required(login_url='login')
def delete_building(request):
  """ 
  Delete building by using buildingId
  check delete building folder exists, folder path "/media/buildingId/"
  URL: /buildings/delete_building/<int:id>
  Parameters:
    id(int): building id
  Returns:
    None

  """ 
  buildingId = request.POST.get('building',None)
  current_location=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  file_path = current_location+"/media/"+buildingId
  if os.path.exists(file_path):
    os.remove(file_path)
  Building.objects.get(id=buildingId).delete()
  return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def updateImages(current_obj,img,id,building=True, width=0,height=0):
  """
    Update the Image to selected building
    Parameters:
      current_obj(Building): selected Building
      img(File): image file
      id(int): building id
      building(boolean): incidiate whether is called for update building
      width(int): imge width (only works when building = Fasle)
      height(int): image height (only works when building = Fasle)
    Rerturns:
      None
  """
  current_obj.img=img  
  if not img:
    current_obj.img_path=''    
  else:    
    if building:    
      current_obj.img_path='/media/'+str(id)+'/building.png' 
    else:      
      invalid = '()<>:"/\|?*'#replace possible characters that django will opt out
      filename=img.name
      for char in invalid:
        filename = filename.replace(char, '').replace(" ","_")
      current_obj.img_path='/media/'+str(id)+'/'+filename  
  if building == False:
    print(current_obj.width)
    if current_obj.width is not None and current_obj.width != '':
      current_obj.width=float(str(width))
      current_obj.height=float(str(height))
  current_obj.save()
  return None


def get_buildings_from_user(request):
  """
  Rertuns a list of buildings that are belong to user's company
  Parameters:
    request:request
  Returns:
    a list of building objects that are belong to the user's company
  """
  building_entry=None
  if request.user.is_superuser:
    building_entry=Building.objects.all()
  else:
    company_entry = get_company_entry_from_request_user(request)
    building_entry = Building.objects.filter(company = company_entry)
  return building_entry

@login_required(login_url='login')
def upload_floor_plan(request,id):
  """
  Upload floor plans for a building
  URL: /buildings/upload_floor_plan/<int:id>
  Parameters:
    Id(int): building id
  Post request parameters:
    floors(int): indicate the building'sfloor [-2,20]
    data(file): image file
    width(int): image'swidth
    height(int): image'sheight 
  Returns:
    None
  """  
  floor,files,width,height=get_floor_plan_var(request)
  building=Building.objects.get(id=id)  
  building_img_entry = BuildingImages(building=building,floor_building=floor,width=width,height=height,date=datetime.datetime.now())  
  building_img_entry.save()
  updateImages(building_img_entry,files,id,False,width,height)
  Task.objects.filter(building=building).update(floor_plan_update_time=datetime.datetime.now())
  return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def get_floor_plan_var(request):
  """
  General function to obtain post requst and file for uploading floor plan
  Parameters:
    request:request
  Post request parameters:
    floor(string): floor value
    files(File): image file
    width(string): image width
    height(string):image height
  Returns:
    floor(string): floor value
    files(File): image file
    width(string): image width
    height(string):image height
  """
  floor = request.POST.get('floors')
  files=request.FILES.get('data',None)
  width=request.POST.get('width',None)
  height=request.POST.get('height',None)
  return floor,files,width,height

@login_required(login_url='login')
def edit_floor_plan(request,id):
  """
  Edit a floor plans for a building
  URL: /buildings/edit_floor_plan/<int:id>
  Parameters:
    Id(int): Id for the floor plan in BuildingImages model
  Post request parameters:
    floors(int): indicate the building'sfloor [-2,20]
    data(file): image file
    width(int): image'swidth
    height(int): image'sheight 
  Returns:
    None
  """  
  buildingId = str(BuildingImages.objects.get(id=id).building.id)
  floor,files,width,height=get_floor_plan_var(request)
  building_img_entry = BuildingImages.objects.get(id=id)
  # when file is not none, update the file and all other fields
  if files is not None:
    BuildingImages.objects.filter(id=id).update(floor_building=floor,width=width,height=height,date=datetime.datetime.now())
    updateImages(building_img_entry,files,buildingId,False,width,height)
  else:
    # when file is none, which means only update floor building
    BuildingImages.objects.filter(id=id).update(floor_building=floor,date=datetime.datetime.now())
  Task.objects.filter(building_id=buildingId).update(floor_plan_update_time=datetime.datetime.now())
  return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='login')
def delete_floor_plan(request,id):
  """
  Delete floor plans from database
  URL: /buildings/delete_floor_plan/<int:id>
  Parameters:
    id(int): id for a floor plan in BuildingImages model
  Returns:
    None
  """  
  try:    
    current_location=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = current_location+"/media/"+BuildingImages.objects.get(id=id).img_path
    if os.path.exists(file_path):
      os.remove(file_path)
    BuildingImages.objects.filter(id=id).delete() 
    Task.objects.filter(building=BuildingImages.objects.filter(id=id).building).update(floor_plan_update_time=datetime.datetime.now())
  except:
    pass
  return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
