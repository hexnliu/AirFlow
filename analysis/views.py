from analysis.common import *
from analysis.occupant_comfort  import *
from analysis.temperature import *
from analysis.humidity import *
from analysis.pressure import *
from analysis.air_quality import *
from analysis.virus_transmission import *
# from analysis.report_updated_functions import *
from buildings.views import *
from placements.models import *
from tasks.models import *
from tasks.views import *
import ast,json
from analysis.data_analysis import *
from buildings.models import *
from reports.report import *

class AnalysisView(LoginRequiredMixin,TemplateView):
     """
        Data analysis index page
        Parameters:
            id(int): task id  from get request
        Returns:
            context object for this page
     """     
     template_name ="analysis/index.html"
     def get_context_data(self,**kwargs): 
      context = super(AnalysisView, self).get_context_data(**kwargs)
      current_task=Task.objects.get(id=kwargs['id']) #get current task
      current_building=current_task.building
      context=navigation_context(current_building,current_task,False,context)
      #floors --- the floors used in sensor placement
      context["floors"]=list(set(SensorPlacement.objects.filter(task=current_task).values_list("floor",flat=True)))
      #floor_plan_floors - the floors have been used in sensor mapping
      context["floor_plan_floors"]=list(set(SensorMapping.objects.filter(task=current_task).values_list("floor",flat=True)))
      #floor_list- the floors they used for  the tasl
      context['floor_list']= ast.literal_eval(current_task.floor_list)
      context["menu"]=readMenu()
      context["sensors_copy_list"]=ast.literal_eval(current_task.sensors_copy_list)
      context["status"]=current_task.status
      return context


def view_floor_plan(request,id):
    """
    View floor plan with markers
    URL: /analysis/view_floor_plan/<int:id>
    Parameters:
        id(int): task id
    Post request parameters:
        floor(int): floor value
    Returns:
        Necessary js for completing part of the marker’s functions
 
    """
    current_task=Task.objects.get(id=id)
    current_floor=request.POST.get("floor",None)
    # note that can't be entire building
    context={}
    context["markers"] =json.dumps(list(SensorMapping.objects.filter(task=current_task,floor=current_floor).values()), default=str)
    context["image"]=BuildingImages.objects.get(building=current_task.building,floor_building=current_floor)
    return render(request, 'partials/render.html',context)


def readMenu():
  """
  Read file from menu.json and generate the html template with all moudles
  Parameters:
  Returns:
    menu content in json format
  """
  current_file = os.path.abspath(os.path.dirname(__file__))
  f= open(os.path.join(current_file, 'files/menu.json'),encoding="utf-8")
  menu = json.load(f)["menu"]
  f.close()
  return menu


def get_sensors_by_floor(request,id):
    """
    Get available sensors that are under the selected floor value
    URL:/analysis/get_sensors_by_floor/<int:id>
    Parameters:
            id(int): task id
    Post request parameters:
        floor(int) floor value
    Returns:
            HTML Elements with a list of sensors that are used by selected floor

    """
    current_task=Task.objects.get(id=id)
    floor=request.POST.get("floor",None)
    objs=filter_sensors(request,current_task)
    if floor == "Building":
        sensor_placements=list(set(objs.values_list("snsr_num","snsr_type")))
    else:
        sensor_placements=list(set(objs.filter(floor=floor).values_list("snsr_num","snsr_type")))
    return render(request, 'partials/render.html', {"list_sensors":dict(sensor_placements).items()})


def filter_sensors(request,current_task):
    """
    Filter out ieq sensor by request, or it could be any type sensor, from the post request
    Parameters:
        request: request
        current_task(Task): task object
    Returns:
        a list of filtered sensors(SensorPlacement) 
    """
    filter_sensor=request.POST.get("filter_sensor",None)
    objs=SensorPlacement.objects.filter(task=current_task)
    if filter_sensor is not None:
        objs= objs.exclude(snsr_type=filter_sensor)
    return objs


def get_locations_by_floor(request,id):
    """
    Get available locations that are under the selected floor value
    URL:/analysis/get_locations_by_floor/<int:id>
    Parameters:
            id(int): task id
    Post request parameters:
        floor(int) floor value
    Returns:
            HTML Elements with a list of locations that are used by selected floor

    """
    current_task=Task.objects.get(id=id)
    floor=request.POST.get("floor",None)
    objs=filter_sensors(request,current_task)
    if floor == "Building":
        sensor_placements=list(set(objs.values_list("location",flat=True)))
    else:
        sensor_placements=list(set(objs.filter(floor=floor).values_list("location",flat=True)))
    return render(request, 'partials/render.html', {"list": {"key":"All Locations","values":sensor_placements}})

def get_perimeters_by_location(request,id):
    """
    Get available perimeters that are under the selected location and floor value
    URL:/analysis/get_perimeters_by_location/<int:id>
    Parameters:
            id(int): task id
    Post request parameters:
        floor(int): floor value
        location(string): location value
    Returns:
            HTML Elements with a list of perimeters that are used by selected floor and location

    """
    current_task=Task.objects.get(id=id)
    floor=request.POST.get("floor",None)
    location=request.POST.get("location",None)
    objs=filter_sensors(request,current_task)
    if floor == "Building":
        if location == "All Locations":
            sensor_placements=list(set(objs.values_list("perimeter",flat=True)))
        else:
            sensor_placements=list(set(objs.filter(location=location).values_list("perimeter",flat=True)))
    else:
        if location == "All Locations":
            sensor_placements=list(set(objs.filter(floor=floor).values_list("perimeter",flat=True)))
        else:
            sensor_placements=list(set(objs.filter(floor=floor,location=location).values_list("perimeter",flat=True)))
    return render(request, 'partials/render.html', {"list": {"key":"Entire Space","values":sensor_placements}})


def run_data_analysis(request,id):
    """
    Run data analysis
    Parameters:
        request: request
        id(int): task id
    Returns:
        current page
    """
    tb_id=Task.objects.get(id=id).building.id    
    AnalyzeData(tb_id,id)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


"""
  ********************Note that: the following function are called from frontend and redirect the call to other place. It is not efficient which could be modify later ******************
"""
  
# Thermal Comfort -- Occupant Comfort - Summary
def occupant_comfort_summary(request,id):  
    buildingId,wk_start,wk_end=get_vars(id)
    floor = request.POST.get('floor',None)
    final_df=load_df(buildingId,id,"final_df.csv")  
    occ=load_df(buildingId,id,"occ.csv")
    loc_full,locations=get_loc_dic(final_df)    
  
    return occupant_comfort_summary_(request,floor,occ,locations,'one','Occupied Hours',wk_start,wk_end,buildingId,id)
    
# Thermal Comfort -- Occupant Comfort - Location
def occupant_comfort_location(request,id):
    return occupant_comfort_location_(request,id)

# Thermal Comfort -- Occupant Comfort - Sensor
def occupant_comfort_sensor(request,id):
    return occupant_comfort_sensor_(request,id)
    
# Thermal Comfort -- Occupant Comfort - Floor Plan    
def occupant_comfort_floor_plan(request,id):
     # cur_width=int(request.POST.get("width",None))  
    cur_width=900
    floor = request.POST.get('floor',None)  
    buildingId,wk_start,wk_end=get_vars(id)  
    co_df,img,img_width,img_height,scale_factor,wk_start,wk_end=get_sensors_images(buildingId,id,floor,cur_width) 
    occ=load_df(buildingId,id,"occ.csv")    
    occ=occ[occ['Floor']==floor] 
    return occupant_comfort_floor_plan_(request,occ,floor,co_df,img,img_width,img_height,scale_factor,'one','Occupied Hours',wk_start,wk_end,buildingId,id)

# Thermal Comfort -- Occupant Comfort - Temperature vs. Relative Humidity
def occupant_comfort_temp_RH(request,id):
   return occupant_comfort_temp_RH_(request,id)

# Temperature - Cluster Analysis- Summary
def temperature_cluster_analysis_summary(request,id):
    cur_width=int(request.POST.get("width",None))  
    # cur_width=900
    floor = request.POST.get('floor',None)  
    buildingId,wk_start,wk_end=get_vars(id)  
    co_df,img,img_width,img_height,scale_factor,wk_start,wk_end=get_sensors_images(buildingId,id,floor,cur_width) 
    final_df=load_df(buildingId,id,"final_df.csv") 
    data=final_df[final_df['Floor']==floor]
    return temperature_cluster_analysis_summary_(request,floor,data,co_df,img,img_width,img_height,scale_factor,'one','All Hours','','',buildingId,id)

# Temperature -Floor Plan - Summary
def temperature_floor_plan_summary(request,id):
    # cur_width=int(request.POST.get("width",None))
    cur_width=900
    buildingId,wk_start,wk_end=get_vars(id)
    floor,occupied=get_fl_occupied(request)
    data,time = check_occupied_df(buildingId,id,occupied)
    co_df,img,img_width,img_height,scale_factor,wk_start,wk_end=get_sensors_images(buildingId,id,floor,cur_width)
    return temperature_floor_plan_summary_(request,data,floor,co_df,img,img_width,img_height,scale_factor,time,wk_start,wk_end,buildingId,id)

def temperature_vs_time_location(request,id):
    return temperature_temp_vs_time_location_(request,id)

def temperature_vs_time_sensor(request,id):
    return temperature_temp_vs_time_sensor_(request,id)

def temperature_differential_summary(request,id):
    baseon = request.POST.get('baseOn',None)     
    floor = request.POST.get('floor')
    buildingId,wk_start,wk_end=get_vars(id)
    final_df=load_df(buildingId,id,"final_df.csv") 
    return temperature_differential_summary_(request,floor,final_df,baseon,'one',buildingId,id)

def temperature_differential_location(request,id):
    return temperature_differential_location_(request,id)

def temperature_differential_sensor(request,id):
    return  temperature_differential_sensor_(request,id)

def temperature_variations_summary(request,id):
    return temperature_variations_summary_(request,id)

def temperature_variations_location(request,id):
    return temperature_variations_location_(request,id)

def temperature_variations_sensor(request,id):
    return temperature_variations_sensor_(request,id)

def rh_cluster_analysis_summary(request,id):
    return rh_cluster_analysis_summary_(request,id)

def rh_floor_plan_summary(request,id):
    return rh_floor_plan_summary_(request,id)

def rh_vs_time_location(request,id):
    return rh_vs_time_location_(request,id)

def rh_vs_time_sensor(request,id):
    return rh_vs_time_sensor_(request,id)

def pressure_vs_time_summary(request,id):
    return pressure_vs_time_summary_(request,id)

def pressure_differential_floor_plan(request,id):
    return pressure_differential_floor_plan_(request,id)

def pressure_differential_sensor_pair(request,id):
    return pressure_differential_sensor_pair_(request,id)

def air_quality_tvoc_summary(request,id):
    return air_quality_tvoc_summary_(request,id)

def air_quality_tvoc_location(request,id):
    return air_quality_tvoc_location_(request,id)

def air_quality_tvoc_sensor(request,id):
    return air_quality_tvoc_sensor_(request,id)

def air_quality_tvoc_floor_plan(request,id):
    return air_quality_tvoc_floor_plan_(request,id)

def air_quality_co2_summary(request,id):
    return air_quality_co2_summary_(request,id)

def air_quality_co2_location(request,id):
    return air_quality_co2_location_(request,id)

def air_quality_co2_sensor(request,id):
    return air_quality_co2_sensor_(request,id)

def air_quality_co2_floor_plan(request,id):
    return air_quality_co2_floor_plan_(request,id)

def virus_transmission_summary(request,id):
    return virus_transmission_summary_(request,id)

def virus_transmission_location(request,id):
    return virus_transmission_location_(request,id)