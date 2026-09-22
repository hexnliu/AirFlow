import io
from tasks.models import Task
from analysis.common import *
import pandas as pd


#CHANGED
def rh_cluster_analysis_summary_(request,id):
    '''
    Plot relative humidity vs time graph for specified sensor and outside.
    Parameters:
        request (): request
        id (): task id
    Returns:
        figure: HTML division containing figure. 
    '''
    r=[]
    floor = request.POST.get('floor')    
    cur_width=int(request.POST.get("width",None))
    task_entry = Task.objects.get(id=id) 
    buildingId = str(task_entry.building.id) 
    #get data and filter by floor
    final_df=load_df(buildingId,id,"final_df.csv") 
    #get text of data's date range, for hover
    data=final_df[final_df['Floor']==floor]
    dateRangeText = get_date_range_text(data)
    #get image and variables needed for floorplan
    co_df,img,img_width,img_height,scale_factor,wk_start,wk_end=get_sensors_images(buildingId,id,floor,cur_width)
    if not co_df.empty:
        #get data needed for this floorplan
        s_df=clustmap_data(floor,'Humidity',final_df,co_df) 

        #add location info
        l_df = final_df.copy()
        l_df = l_df.drop_duplicates('Sensor Number')
        l_df = l_df[['Sensor Number','Location']]
        s_df = pd.merge(s_df,l_df,on='Sensor Number',how='left') 
        #get colorbar properties based on the number of clusters
        num_clusters = len(s_df['clust'].unique())
        color_scale,tickvals,ticktext = get_cluster_colorbar(num_clusters)
        #make fgireu
        config =config_setting('Relative Humidity - Cluster Analysis - Summary')        
        hovertemplate = "Location: "+s_df['Location']+"<br>Time Period: All Hours "+dateRangeText+"<br>Relative Humidity: "+round(s_df['Humidity'],2).astype(str)+"%<br>Cluster: "+s_df['clust'].astype(str)+"<extra></extra>"
        #Add descriptive text under the graph
        fig = general_floormap(s_df, img, img_width, img_height, scale_factor, 'Humidity', 'Sensor Number', color_scale, tickvals, ticktext, 'Relative Humidity', 6, 12, [], hovertemplate, 1, num_clusters+1, 100+50*num_clusters, 'clust','All Hours','','')
        fig = add_xlabel_occupancy_text(fig,'Relative humidity clusters are displayed based on sensor values during ','All Hours','','')
        div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3">Guide on How to Read This Graph</h5><p style="padding:15px;">Locations that share a colour followed statistically similar relative humidity (RH) trends over time. Similar clusters are a result of similarly conditioned air flow and ventilation, occupancy or space use, weather, as well as solar loading.</p></div></div>'
        r1 =[]
        div = opy.plot(fig, auto_open=False, output_type='div',include_plotlyjs=False,config=config)
        # dic=export_to_png(fig,buildingId,versionId,filename)  
        r1.append(div)    
        # r.append(dic)
        r1.append(div_info)
        #get overtime graph for cluster to display below the floorplan graph
        r2 = graph_clusters_overtime(request,floor,data,s_df,"Humidity",buildingId,id,'rh_cluster_analysis_summary_overtime'+str(floor)+'.png',wk_start,wk_end)
        return render(request, 'partials/render.html', {"div": r1+r2})
    else:
        div= "floor"+floor+" floor plan image does not exist or sensor mapping is not done. Please upload image(s) and finish sensor mapping."
        return render(request, 'partials/render.html', {"div": div})

#CHANGED
def rh_floor_plan_summary_(request,id):
    '''
    Graphs floormap containing sensors and their mean relative humidity values.
    Parameters:
       request (): request
       id (int): task id
    Returns:
        figure: HTML division containing figure. 
    '''
    
    floor = request.POST.get('floor')    
    cur_width=int(request.POST.get("width",None))
    buildingId,wk_start,wk_end=get_vars(id)
    floor,occupied=get_fl_occupied(request)
    #get data and time period
    data,time = check_occupied_df(buildingId,id,occupied)
    #get image and variables needed for floorplan
    co_df,img,img_width,img_height,scale_factor,wk_start,wk_end=get_sensors_images(buildingId,id,floor,cur_width)
    #get text of data's date range, for hover
    dateRangeText = get_date_range_text(data) 
    #get data needed for this floorplan
    dd,s_df,a,s_num=map_data(data,floor,co_df,'Humidity')    

    #add location info
    l_df = data.copy()
    l_df = l_df.drop_duplicates('Sensor Number')
    l_df = l_df[['Sensor Number','Location']]
    s_df = pd.merge(s_df,l_df,on='Sensor Number',how='left')
    #make graph
    config = config_setting('Relative Humidity - Floor Plan - Summary')
    color_scale= [(0,"#c7fcff"),(1,'#0021a7')] 
    hovertemplate = "Location: "+s_df['Location']+"<br>Time Period: "+time+dateRangeText+"<br>Relative Humidity: "+ round(s_df['Humidity'],2).astype(str)+"%<extra></extra>"
    #Add descriptive text under the graph
    fig = general_floormap(s_df, img, img_width, img_height, scale_factor, 'Humidity', 'Sensor Number', color_scale, [0,20,40,60,80,100], ["0%","20%", "40%","60%" ,"80%", "100%"], 'Relative Humidity', 0, 50, [], hovertemplate, 0, 100, 400,'',time,wk_start,wk_end)   
    text = 'Average relative humidity values are displayed for '
    fig = add_xlabel_occupancy_text(fig,text,time,wk_start,wk_end)
    div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3">Guide on How to Read This Graph</h5><p style="padding:15px;">This figure quickly and easily represents the range of average relative humidity (RH) values on a building floor plan based on a specific time period. Darker blue indicates higher RH while lighter blue indicates lower RH.</p></div></div>'
    return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'rh_floor_plan_summary_'+str(floor)+'.png')

#CHANGED
def rh_vs_time_location_(request,id):
    '''
    Graphs relative humidity values over time for all sensors.
    Parameters:
        request (): request
        id (int): #task id
    Returns:
        figure: HTML division containing figure. 
    '''
    buildingId,wk_start,wk_end=get_vars(id)
    #get data 
    final_df=load_df(buildingId,id,"final_df.csv")
    #filter by floor, location, and space
    floor,loc,space = get_fl_loc_per_var(request)
    data = check_floor_loc_per(floor,loc,space,final_df)
    #add column that states the time period of each row, to add to hover
    data = add_time_period_col(data,'',wk_start,wk_end)
     #make graph
    data['Humidity'] = np.round(data['Humidity'],2)
    hovertemplate = 'Sensor Number: %{customdata[0]}<br>Location: %{customdata[1]}<br>Time Period: %{customdata[2]}<br>Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Relative Humidity: %{y}<br><extra></extra>'
    locations =data['Location'].unique()
    config = config_setting('Relative Humidity - Relative Humidity vs. Time - Location')     
    fig = general_graph_overtime_group_legend(data,'','Humidity',locations,'Location','Sensor Number','Date', 'Relative Humidity','%',hovertemplate,['Sensor Number','Location','Time Period'])
    
     #add comfort range box
    fig = add_comfort_range_legend(fig,compact=True) 
    fig.add_hrect(y0=20,y1=60,fillcolor='lightgreen',line_color='lightgreen',opacity=.3)
    fig.update_layout(legend_title_text='Sensor Number')

    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7')  
    div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3">Guide on How to Read This Graph</h5><p style="padding:15px;">Time is labeled on the horizontal axis, and relative humidity (RH) is on the vertical axis. This figure represents the RH over time for the selected location, with all of the individual sensors categorized by that location.</p></div></div>'
    return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'')

#CHANGED
def rh_vs_time_sensor_(request,id):
    '''
    Plot relative humidity vs time graph for specified sensor and outside.
    Parameters:
        request (): request
        id (int): task id
    Returns:
        figure: HTML division containing figure. 
    '''
    sensor_id = request.POST.get('sensor')
    task_entry = Task.objects.get(id=id) 
    occ_start=task_entry.weekday_occupied_start
    occ_end=task_entry.weekday_occupied_end
    buildingId = str(task_entry.building.id)
    #get data and filter for this sensor
    final_df=load_df(buildingId,id,"final_df.csv")
    data=final_df[final_df['Sensor Number']==sensor_id]
    data['Humidity'] = np.round(data['Humidity'],2)
    #add column that states the time period of each row, to add to hover
    data = add_time_period_col(data,'',occ_start,occ_end)
    #this sensor's location
    sensor_loc = data['Location'].unique()[0]
     #make figure
    hovertemplate = "Location: "+sensor_loc+"<br>Time Period: "+data['Time Period']+"<br>Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Relative Humidty: %{y}<extra></extra>"

    fig = general_graph_overtime(data.index, data['Humidity'], "Date", 'Relative Humidity', [], hovertemplate, '#0000FF', 'Sensor ' + str(sensor_id) + ' Relative Humidity', ticksuffix='%')
    config = config_setting('Relative Humidity - Relative Humidity vs. Time - Sensor')
    
    #add outside humidity to graph if present
    if 'Humidity_Outside' in data:        
        fig = plot_add_dotted_line(fig, data.index, data['Humidity_Outside'], 'Outside Relative Humidity', "Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Outside Relative Humidty: %{y}<extra></extra>", [],'#20b2aa', 3)
    
    #add comfort range
    fig = add_comfort_range_legend(fig,compact=True) 
    fig.add_hrect(y0=20,y1=60,fillcolor='lightgreen',line_color='lightgreen',opacity=.3)

    fig.update_layout(legend= {'itemsizing': 'constant'})
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7')
    div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3">Guide on How to Read This Graph</h5><p style="padding:15px;">Time is labeled on the horizontal axis, and relative humidity (RH) is on the vertical axis. This figure represents the RH over time for the selected sensor as well as the external RH illustrated for reference.</p></div></div>'
    return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'')