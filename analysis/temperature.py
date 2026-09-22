import io
from tasks.models import Task
from analysis.common import *
import pandas as pd


#CHANGED
def temperature_cluster_analysis_summary_(request,floor,final_df,co_df,image,img_width,img_height,scale_factor,action,time,wk_start,wk_end,buildingId,id):
    '''
    Makes a floormap that shows sensors colored by their cluster (clustered based on temperature values overtime).
    Parameters:
        request (): request
        floor (string): Floor number.
        final_df (dataframe): Data.
        co_df (dataframe): Contains sensor numbers and their coordinate on the floorplan image.
        image (string): The floor's image path from BuildingImages
        img_width (float): The floor's width. 
        img_height (float): The floor's height. 
        scale_factor (float): For scaling the size of the graph.
        action (string): Whether to use the graph for report or in the modules.
        time (string): Time period.
        wk_start (string): Time when occupancy starts.
        wk_end (string): Time when occupancy ends.
        buildingId (int): building id
        id (int): task id
    Returns:
		Specified figure.
    '''
    #get text of data's date range, for hover
    dateRangeText = get_date_range_text(final_df)
    #add cluster info 
    s_df=clustmap_data(floor,'Temperature',final_df,co_df)    

    #add location info 
    l_df = final_df.copy()
    l_df = l_df.drop_duplicates('Sensor Number')
    l_df = l_df[['Sensor Number','Location']]
    s_df = pd.merge(s_df,l_df,on='Sensor Number',how='left')

    config = config_setting('Temperature - Cluster Analysis - Summary')

    #get colorbar properties based on the number of clusters
    num_clusters = len(s_df['clust'].unique())
    
    color_scale,tickvals,ticktext = get_cluster_colorbar(num_clusters)
     #make figure
    hovertemplate = "Location: "+s_df['Location']+"<br>Time Period: All Hours"+dateRangeText+"<br>Temperature: "+round(s_df['Temperature'],2).astype(str)+"°C<br>Cluster: "+s_df['clust'].astype(str)+"<extra></extra>" 
    fig = general_floormap(s_df,image, img_width, img_height, scale_factor, 'Temperature', 'Sensor Number',color_scale , tickvals,ticktext, 'Temperature', 6, 13, [], hovertemplate, 1, num_clusters+1, 100+50*num_clusters,'clust','All Hours','','')
    #Add descriptive text under the graph
    text = 'Temperature clusters are displayed based on sensor values during '
    fig = add_xlabel_occupancy_text(fig,text,time,wk_start,wk_end)

    if action == 'report':
        return export_to_png(fig,buildingId,id,'temperature_cluster_'+str(id)+'.png')
    else:
        div_info = '<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3">Guide on How to Read This Graph</h5><p style="padding:15px;">Locations that share a colour followed statistically similar temperature trends over time. Similar clusters are a result of similarly conditioned air flow and ventilation, occupancy or space use, weather, as well as solar loading.</p></div></div>'
        r1 =[]
        div = opy.plot(fig, auto_open=False, output_type='div',include_plotlyjs=False,config=config)
        # dic=export_to_png(fig,buildingId,versionId,filename)  
        r1.append(div)    
        # r.append(dic)
        r1.append(div_info)
        r2 =graph_clusters_overtime(request,floor,final_df,s_df,"Temperature",buildingId,id,'temperature_cluster_analysis_'+str(id)+'.png',wk_start,wk_end)
        return render(request, 'partials/render.html', {"div": r1+r2})
    
#CHANGED
def temperature_floor_plan_summary_(request,data,floor,co_df,img,img_width,img_height,scale_factor,time,wk_start,wk_end,buildingId,id):
    '''
    Makes floormap containing sensors and their mean temperature values.
    Parameters:
        request (): request
        data (dataframe): Data.
        floor (string): Floor number.
        co_df (dataframe): Contains sensor numbers and their coordinate on the floorplan image.
        image (string): The floor's image path from BuildingImages
        img_width (float): The floor's width. 
        img_height (float): The floor's height. 
        scale_factor (float): For scaling the size of the graph.
        time (string): Time period.
        wk_start (string): Time when occupancy starts.
        wk_end (string): Time when occupancy ends.
        buildingId (int): building id
        id (int): #task id
    Returns:
		Specified figure.
    '''    
    if not co_df.empty:
        #get text of data's date range, for hover
        dateRangeText = get_date_range_text(data) 
        #add mean temperature info
        dd,s_df,a,s_num=map_data(data,floor,co_df,'Temperature')  
        #add location info 
        l_df = data.copy()
        l_df = l_df.drop_duplicates('Sensor Number')
        l_df = l_df[['Sensor Number','Location']]
        s_df = pd.merge(s_df,l_df,on='Sensor Number',how='left') 
        s_df['Temperature'] = np.round(s_df['Temperature'],2)
        #make graph
        color_scale = [(0,"#0E5DA8"),(0.11,"#208B93"),(0.22,"#208B93"),(0.33,"#47B489"),(0.44,"#5BBA47"),(0.55,"#9BCA3D"),(0.66,"#D1D029"),(0.77,"#F0E443"),(0.88,"#EFA243"),(1.0,"#EF5A45")]
        hovertemplate="Location: "+s_df['Location']+"<br>Time Period: "+str(time)+dateRangeText+"<br>Temperature: "+ s_df['Temperature'].astype(str)+"°C<extra></extra>" 
        config =config_setting('Temperature - Heatmap - Summary')   
        # Add trace
        fig = general_floormap(s_df, img, img_width, img_height, scale_factor,'Temperature', 'Sensor Number', color_scale, [12,14.9,17.9,20.8,23.8,26.9,30], ["12°C","15°C","18°C", "21°C","24°C" ,"27°C","30°C"], 'Temperature', 19.92, 27.84, [], hovertemplate, 12, 30, 400,'',time,wk_start,wk_end)
          #Add descriptive text under the graph
        text = 'Average temperature values are displayed for '
        fig = add_xlabel_occupancy_text(fig,text,time,wk_start,wk_end)        
        div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" >Guide on How to Read This Graph</h5><p style="padding:15px;">This figure quickly and easily represents the range of average temperatures on a building floor plan based on a specific time period.</p></div></div>'
        return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'temperature_floor_plan_'+str(id)+'.png')
    else:
        r="floor"+floor+" floor plan image does not exist or sensor mapping is not done. Please upload image(s) and finish sensor mapping."
        return render(request, 'partials/render.html', {"div": r})    

#CHANGED
def temperature_temp_vs_time_location_(request,id):
    '''
    Makes graph that shows sensors, setpoint, and mean temperature values over time for the specified locations.
    Parameters:
        request ():request
        id (int): #Task id
    Returns:
        Specified figure.
    '''
    buildingId,wk_start,wk_end=get_vars(id)
    #get data and filter by floor, location, and space
    final_df=load_df(buildingId,id,"final_df.csv")
    floor,loc,space = get_fl_loc_per_var(request)
    data = check_floor_loc_per(floor,loc,space,final_df)
    data['Temperature'] = np.round(data['Temperature'],2)
    locations=data['Location'].unique()
    locations = [x for x in locations if str(x) != 'nan']
    config = config_setting('Temperature - Temperature vs. Time - Location')  

    #Add time period to overtime graph
    data = add_time_period_col(data,'',wk_start,wk_end)

    #get data of a single sensor to use to graph setpoint
    sens=data['Sensor Number'].unique() 
    datas1=data[data['Sensor Number']==sens[0]]  
    #group data by time and get its mean temperature       
    d1=data['Temperature'].groupby(data.index).mean()    
    d1=pd.concat([d1],axis=1).reset_index() 
    d1['Temperature'] = np.round(d1['Temperature'],2)
    #make graph
    hovertemplate = 'Sensor Number: %{customdata[0]}<br>Location: %{customdata[1]}<br>Time Period: %{customdata[2]}<br>Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Temperature: %{y}<br><extra></extra>'
    fig = general_graph_overtime_group_legend(data,'','Temperature',locations,'Location','Sensor Number','Date','Temperature','°C',hovertemplate,customdata = ['Sensor Number','Location','Time Period'])
     #add setpoint line if present
    if 'Set_point' in datas1:
        fallback= float(str(Task.objects.get(id=id).weekday_unoccupied_temperature))    
        datas1.loc[datas1["Set_point"] <1, "Set_point"] = fallback        
        fig = plot_add_dotted_line(fig,  datas1.index, datas1['Set_point'], 'Setpoint',  'Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Setpoint Temperature: %{y}<br><extra></extra>', [], 'blue')
     #add mean temperature line
    fig = plot_add_dotted_line(fig, d1['TimeStamp'], d1['Temperature'], 'Mean Temperature', 'Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Mean Temperature: %{y}<br><extra></extra>', [], 'red')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7')
    fig.update_layout(legend_title_text='Sensor Number')

    #add comfort range
    fig = add_comfort_range_legend(fig,compact=True) 
    fig.add_hrect(y0=20,y1=24,fillcolor='lightgreen',line_color='lightgreen',opacity=.3)
    div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" >Guide on How to Read This Graph</h5><p style="padding:15px;">Time is labeled on the horizontal axis, and temperature is on the vertical axis. This figure represents the temperature over time for the selected location, with all of the individual sensors categorized by that location, as well as temperature setpoint illustrated for reference.</p></div></div>'
    return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'temperature_vs_time_location_'+str(id)+'.png')

#CHANGED
def temperature_temp_vs_time_sensor_(request,id):
    '''
    Plot temperature vs time graph for specified sensor and outside.
    Parameters:
        request ():request
        id (int): #task id
    Returns:
		Specified figure.
    '''
    sensor_id = request.POST.get('sensor')
    task_entry = Task.objects.get(id=id) 
    occ_start=task_entry.weekday_occupied_start
    occ_end=task_entry.weekday_occupied_end
    buildingId = str(task_entry.building.id)
    #get data
    final_df=load_df(buildingId,id,"final_df.csv")

    config = config_setting('Temperature - Temperature vs. Time - Sensor')    
    #filter data for this sensor
    data=final_df[final_df['Sensor Number']==sensor_id]
    #sensor's location
    sens_loc = data['Location'].unique()[0]
    data['Temperature'] = np.round(data['Temperature'],2)
    #add column that states the time period of each row, to add to hover
    data = add_time_period_col(data,'',occ_start,occ_end)
     #make graph
    hovertemplate = 'Location: '+sens_loc+'<br>Time Period: '+data['Time Period']+'<br>Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Temperature: %{y}<extra></extra>'
    fig = general_graph_overtime(data.index, data['Temperature'], 'Date', 'Temperature', [], hovertemplate, '#ff1505', 'Sensor '+str(sensor_id), ticksuffix='°C')    
    #add outside temp line if present
    if 'Temperature_Outside' in data:
        fig = plot_add_dotted_line(fig,data.index,data['Temperature_Outside'],'Outside Temperature', 'Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Outside Temperature: %{y}<extra></extra>',[],'Magenta')     
    
    #add setpoint temp line if present
    if 'Set_point' in data:
         fallback= float(str(Task.objects.get(id=id).weekday_unoccupied_temperature))    
         data.loc[data["Set_point"] <1, "Set_point"] = fallback
         fig = plot_add_dotted_line(fig,data.index,data['Set_point'],'Setpoint','Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Setpoint Temperature: %{y}<extra></extra>',[],"blue") 
    
    #add comfort range
    fig = add_comfort_range_legend(fig,compact=True)
    fig.add_hrect(y0=20,y1=24,fillcolor='lightgreen',line_color='lightgreen',opacity=.3)
    fig.update_layout(legend= {'itemsizing': 'constant'})
    
    
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7')
    # Set y-axes titles
    fig.update_yaxes(title_text='Temperature',ticksuffix="°C")
    div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" data-target="#tahm_3"  >Guide on How to Read This Graph</h5><div id="tahm_3" ><p style="padding:15px;">Time is labeled on the horizontal axis, and temperature is on the vertical axis. This figure represents the temperature over time for the selected sensor as well as external temperature and setpoint temperature for reference.</p></div></div>'
    return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'temperature_vs_time_sensor_'+str(id)+'.png')

#CHANGED
def temperature_differential_summary_(request,fl,final_df,baseon='average',action='real',buildingId='1',id='1'):  
    '''
    Show barplots that show percentage of time within given deadband from setpoint or average.
    Parameters:
        request (): request
        fl (string): Floor number.
        final_df (dataframe): Data.
        baseon (string): Whether to use average or setpoint as the point of reference.
        action (string): 
        buildingId (int): building id
        id (int): task id
    Returns:
		Specified figure.
    '''
    #filter by floor  
    if fl !="Building":
        final_df=final_df[final_df['Floor']==fl]

    #get text of data's date range, for hover     
    dateRangeText = get_date_range_text(final_df)

    #get data for each deadband
    frames = [get_time_near_temp_range(fl,0.5,final_df,baseon)[['Location','Percentage of Time',"Floor","within"]],get_time_near_temp_range(fl,1,final_df,baseon)[['Location','Percentage of Time',"Floor","within"]],get_time_near_temp_range(fl,2,final_df,baseon)[['Location','Percentage of Time',"Floor","within"]]]
    result = pd.concat(frames)    
    config = config_setting('Temperature - Temperature Differential - Summary')    
     #make figure
    hovertemplate="Location: %{x}<br>Time Period: All Hours"+dateRangeText+"<br>ASHRAE Standard: %{customdata[0]}<br>Percentage of Time: %{y}<br><extra></extra>"
    fig = get_temp_differential_figure(result, 'Location', 'Percentage of Time', hovertemplate, {"within": [" 0.5", " 1", "2"]}, 1, '%',[],[0,119])
    
    #add target line
    fig.add_hline(y=100,line_width=3,line_color='#9BCA3B') 
    fig = add_legend_text(fig,'Target')
    fig.data[-1]['line']['color']='#9BCA3B'
    fig.data[-1]['line']['dash']='solid'
    fig.update_layout(legend_traceorder="reversed")

    if baseon=='average':
        fig.update_layout(title= "Floor Average",title_x=0.5)
    else:
        fig.update_layout(title= "Setpoint")
    div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3">Guide on How to Read This Graph</h5><p style="padding:15px;">Locations are indicated on the horizontal axis, and percentage of time within the temperature differential value is on the vertical axis. The figure is divided into three sections based on the three temperature differential values, 0.5°C, 1°C, and 2°C (~1°F, ~2°F, ~3°F).</p></div></div>'
    return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'temperature_differential_summary_'+str(id)+'.png')

def get_time_near_temp_range(f,db,final_df,based): 
    '''
    Return percentage of time within given deadband from setpoint or average as a table.
    Parameters: 
        f (string): floor to use.
        db (float): Temp differential target
        final_df (dataframe): Contains sensors' data.
        based (string): Within setpoint or average.
    Returns:
        df (dataframe): Percent of time within the specified range.
    ''' 
    peri=final_df[final_df['Perimeter']=='Yes']
    inte=final_df[final_df['Perimeter']=='No']

     #filter by floor    
    if f=='Building':        
        new=[final_df,peri,inte]
    else:                
        new=[final_df[final_df['Floor']==f],peri[peri['Floor']==f],inte[inte['Floor']==f]]
    loc=['Whole Floor','Perimeter','Interior']
    p=list()    
    l=list()   
    for i in range(len(new)):
        degree=list()        
        if based=='setpoint':
            for j in range(len(new[i])):   #Go through readings 
                 #temperature difference between each temperature data point and setpoint           
                diff=abs(new[i]['Temperature'][j]-new[i]['Set_point'][j])
                #check whether different is less than deadband               
                if(diff<db):
                    degree.append('FALSE')
                else:
                    degree.append('TRUE')
        #if there are no setpoint is given use average temperature                               
        elif based=='average':
            dd=new[i]
            #store average temperature in each time point (considering all sensors)
            d1=dd['Temperature'].groupby(dd.index).mean()
            d1=pd.concat([d1],axis=1).reset_index()
            sens=dd['Sensor Number'].unique()
            for k in sens:
                d=dd[dd['Sensor Number']==k]
                for j in range(len(d)): 
                     #difference between average temperature and actual temperature on each time point              
                    diff=abs(d['Temperature'][j]-d1['Temperature'][j])
                    if(diff<db):
                        degree.append('FALSE')
                    else:
                        degree.append('TRUE')
        new[i]['degree']=degree
        #find time percentage which the values are within the dead band.
        if len(new[i])!=0:
            p.append(round(len(new[i][new[i]['degree']=='FALSE'])*100/len(new[i]),2))
            l.append(loc[i])  
    floor=['floor '+str(f)]*len(l)  
    within=[str(db)+"°C"]*len(l)
    dict = {'Location': l, 'Percentage of Time':p,"Floor":floor,"within":within}  
    df = pd.DataFrame(dict)  
   
    #take weighted average of interior and perimeter
    num_peri = final_df[final_df['Perimeter'] == 'Yes']['Sensor Number'].unique()
    num_inter = final_df[final_df['Perimeter'] == 'No']['Sensor Number'].unique()      
    if(len(num_peri)!=0 and len(num_inter)!= 0):      
        weight_peri = len(num_peri)/len(final_df['Sensor Number'].unique())    
        weight_inter = 1-weight_peri 
        df['Percentage of Time'][0] = df['Percentage of Time'][1]*weight_peri + df['Percentage of Time'][2]*weight_inter
    return df

#CHANGED
def temperature_differential_location_(request,id):
    '''
    Plots temperature vs time graph of sensors and a box showing area near the setpoint.
    Parameters:
        request (): request
        id (int): #Task id
    Returns:
		Specified figure.
    '''
    task_entry = Task.objects.get(id=id)
    tempature=request.POST.get("tempature",None)
    try:#if we know setpoint
        s=float(task_entry.weekday_occupied_temperature)
    except:#else use default value
        s=23
    buildingId,wk_start,wk_end=get_vars(id)
     #get data and filter by floor, location, and space
    final_df=load_df(buildingId,id,"final_df.csv")
    floor,loc,space = get_fl_loc_per_var(request)
    data = check_floor_loc_per(floor,loc,space,final_df)
    data['Temperature'] = np.round(data['Temperature'],2)
    #add column that states the time period of each row, to add to hover
    data = add_time_period_col(data,'',wk_start,wk_end)

    locations=data['Location'].unique()
    locations = [x for x in locations if str(x) != 'nan']
    config = config_setting('Temperature - Temperature Differential - Location')   
    #make graph
    hovertemplate = 'Sensor Number: %{customdata[0]}<br>Location: %{customdata[1]}<br>Time Period: %{customdata[2]}<br>Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Temperature: %{y}<br><extra></extra>'
    fig = general_graph_overtime_group_legend(data,'',"Temperature",locations,'Location','Sensor Number', 'Date','Temperature', '°C',hovertemplate,customdata = ['Sensor Number','Location','Time Period'])
    sens=data['Sensor Number'].unique()
    #add comfort box
    n_df=data[data['Sensor Number']==sens[0]]
    fig = plot_add_box(fig, n_df.index[0], s-float(tempature), n_df.index[len(n_df.index)-1], s+float(tempature), "lightgreen", "lightgreen",opacity=0.4)
    fig = add_legend_text(fig,'Temperature within <br>'+str(tempature)+'°C of Setpoint')
    fig.data[-1]['line']['color']='lightgreen'
    fig.data[-1]['line']['dash']='solid'

    fig.update_layout(legend_title_text='Sensor Number')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7')
    fig.update_layout(legend= {'itemsizing': 'constant'})
    div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" >Guide on How to Read This Graph</h5><p style="padding:15px;">Time is labeled on the horizontal axis, and temperature is on the vertical axis. The temperature differential range is highlighted to illustrate which sensor values within a specific location deviate from this range and when that deviation occurs.</p></div></div>'
    return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'temperature_differential_location_'+str(id)+'.png')

#CHANGED
def temperature_differential_sensor_(request,id):
    '''
    Graphs specified sensor's temperature values over time and highlights which areas of the graph are near setpoint.
    Parameters:
        request (): request
        id (int): #Task id
    Returns:
		Specified figure.
    '''
    buildingId,wk_start,wk_end=get_vars(id)
    #get data
    final_df=load_df(buildingId,id,"final_df.csv")
    sens=request.POST.get('sensor')
    task_entry = Task.objects.get(id=id)
    tempature=request.POST.get("tempature",None)
    try:#if we know setpoint
        s=float(task_entry.weekday_occupied_temperature)
    except:#else use a default value
        s=23
    tempature=float(request.POST.get("tempature"))
     #get this sensor's data
    data=final_df[final_df['Sensor Number']==sens]
    data['Temperature'] = np.round(data['Temperature'],2)
    #sensor's location
    sensor_loc = data['Location'].unique()[0]
    #add column that states the time period of each row, to add to hover
    data = add_time_period_col(data,'',wk_start,wk_end)
     #make figure
    hovertemplate = "Location: "+sensor_loc+"<br>Time Period: "+data['Time Period']+"<br>Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Temperature: %{y}<extra></extra>"
    config = config_setting('Temperature - Temperature Differential - Sensor')   
    fig = general_graph_overtime(data.index, data['Temperature'], "Date", 'Temperature', [], hovertemplate, '#ff1505', 'Sensor '+str(sens)+'<br>Temperature', [], ticksuffix='°C')
    # fig.add_trace(go.Scatter(x=data.index, y=[s-tempature]*len(data), name='Temperature within <br>'+str(tempature)+'°C of Setpoint', line={'color':'#cbf3f3', 'width':0.5, }))   
    #add rectangle 
    x0=data.index[0]
    y0=s-tempature
    x1=data.index[len(data.index)-1]
    y1=s+tempature

    #add comfort box
    fig = plot_add_box(fig, x0, y0, x1, y1, opacity=0.4) 
    fig = add_legend_text(fig,'Temperature within <br>'+str(tempature)+'°C of Setpoint')
    fig.data[-1]['line']['color']='lightgreen'
    fig.data[-1]['line']['dash']='solid'

    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7')
    fig.update_layout(hoverlabel={'bgcolor':'white'},legend= {'itemsizing': 'constant'}) 
    div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" >Guide on How to Read This Graph</h5><p style="padding:15px;">Time is labeled on the horizontal axis, and temperature is on the vertical axis. The temperature differential range is highlighted to illustrate when values deviate from this range and by how much.</p></div></div>'
    return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'temperature_differential_sensor_'+str(id)+'.png')

#CHANGED
def temperature_variations_summary_(request,id):
    '''
    Graphs barplots showing percent of time ashrae standards were exceeded for each location.
    Parameters:
        request (): request
        id (int): task id
    Returns:
		Specified figure.
    '''
    buildingId,wk_start,wk_end=get_vars(id)
    config = config_setting('Temperature - Temperature Variations - Summary')
    data = load_df(buildingId,id,"occ.csv")
     #get text of data's date range, for hover
    dateRangeText = get_date_range_text(data) 
    hours=request.POST.get('hour',None)
    floor=request.POST.get('floor',None)
     #get sensors and their not exceeded percentage
    yy,xx,time_interval=ashrae(float(hours),floor,data)
     #take mean not exceeded percentage of each location
    new = yy['not_exceeded'].groupby(yy['Location']).mean()
    new=pd.concat([new],axis=1).reset_index()
    new['not_exceeded'] = np.round(new['not_exceeded'],1)
    #make figure
    hovertemplate = 'Location: %{x}<br>Time Period: Occupied Hours'+dateRangeText+'<br>Percentage of Time: %{y}<extra></extra>'
    fig=general_barplot(x=new['Location'],y=new["not_exceeded"], xaxis_label=' ', yaxis_label='Percentage of Time that Comply with <br>ASHRAE Standards within '+str(time_interval), texttemplate='%{y:.1f}'+'%', hoverVarComb=[], hovertemplate=hovertemplate, yrange=[0,110], ticksuffix='%', ticktext='%', tickvals=[],time="Occupied Hours",wk_start=wk_start,wk_end=wk_end)
    #add target line
    fig.add_trace(go.Scatter(x=new['Location'], y=[100]*len(new), name='Target',mode='lines',line={'color': '#9BCA3B', 'width': 3}))
    fig.update_layout(legend_traceorder="reversed")
    div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3">Guide on How to Read This Graph</h5><div id="tvwt_1" ><p style="padding:15px;">Locations are indicated on the horizontal axis and the percentage of time that the locations comply with the allowable temperature variation is on the vertical axis. Selecting a time interval will show results regarding location temperature variation compliance relevant to that specific time interval. The target percentage is 100, indicating that the measured temperature variations within a location always comply with ASHRAE 55 during the building’s occupied hours.</p></div></div>'
    return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'')

def temperature_variations_location_(request,id):
    '''
    Graphs barplots showing percent of time ashrae standards were exceeded for each date.
    Parameters
        request (): request
        id (int): #Task id
    Returns:
		Specified figure.
    '''
    buildingId,wk_start,wk_end=get_vars(id)
    config = config_setting('Temperature - Temperature Variations - Location')
     #get data
    data = load_df(buildingId,id,"occ.csv")
    floor,loc,space = get_fl_loc_per_var(request)  
    hour = request.POST.get('hour',None) 
    #get not exceeded percent
    x,df,time_interval=ashrae(hour,floor,data)
     #filter by location and perimeter
    time ="Occupied Hours"
    if loc!='All Locations':
        data=data[data['Location']==loc]
    if space=='Perimeter':
        data=data[data['Perimeter']=='Yes']
    if space=='Interior':
        data=data[data['Perimeter']=='No']
    #keep only the values for sensors in the data
    sens=data['Sensor Number'].unique()
    new=df[df['sensor'].isin(sens)]
     #find average value of each date
    t = new['not_exceeded'].groupby(new['Date']).mean()
    t=pd.concat([t],axis=1).reset_index()
    t['not_exceeded'] = np.around(t['not_exceeded'],1)
    #make figure
    fig=general_barplot(t['Date'],t['not_exceeded'], 'Date', 'Percentage of Time that Comply with <br>ASHRAE Standards within '+str(time_interval), '%{y:.1f}'+'%', [],hovertemplate_days_barplot(floor,loc,space,time,'Percentage of Time'), [0,110], '%', '%', [],time,wk_start,wk_end)
    fig.add_trace(go.Scatter(x=t['Date'], y=[100]*len(t), name='Target',mode='lines',line={'color': '#9BCA3B', 'width': 3}))
    fig.update_layout(
    xaxis = dict(
        tickvals = t['Date'].tolist() 
    ),
    legend_traceorder="reversed")
    div_info ='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" >Guide on How to Read This Graph</h5><p style="padding:15px;">Tested dates are labeled on the horizontal axis, and the percentage of time specific locations comply with allowable temperature variations is on the vertical axis. The location selection can range from the entire building, to a specific floor, to a location within that floor based on interior or perimeter. Selecting a time interval will show results regarding location temperature variation compliance relevant to that specific time interval. The target percentage is 100, indicating that the measured temperature variations within a location always comply with ASHRAE 55 during the building’s occupied hours.</p></div></div>'
    return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'')

def temperature_variations_sensor_(request,id):
    '''
    Plots overtime graph of given sensor and shows if it was exceeded for given interval(s).
    Parameters:
        request (): request
        id (int): task id
    Returns:
		Specified figure.
    '''
    buildingId,wk_start,wk_end=get_vars(id)
    final_df = load_df(buildingId,id,"final_df.csv")
    r=[] 
    sens=request.POST.get('sensor')
    inter=request.POST.get('hour')
    config = config_setting('Temperature - Temperature Variations - Sensor')
     #get this sensor's data
    s1=final_df[final_df['Sensor Number']==sens]
    lines=list()
    shapes=list()
    w=[15,30,60,120,240] #store window sizes
    ash=[1.1,1.7,2.2,2.8,3.3] #store ashrae standards
    y0=[0.8,0.6,0.4,0.2,0]#store starting point of vertical lines
    y1=[1,0.8,0.6,0.4,0.2]#store ending points of vertical lines
    col=['pink',"yellow",'orange','#9BCA3B','#56B4E9'] #store colors for lines based on time difference
    if inter=='All': #shouldn't have All as an option on the website anymore
        for j in range(len(w)):
            for i in range(len(s1['Temperature'])-w[j]):
                  #absolute temperature difference between two time windows
                d=abs(s1['Temperature'][i]-s1['Temperature'][i+w[j]])
                d=round(d,2)
                 #check time difference with ashrae standards and store points which exceeded the standards
                if(d >ash[j]):
                    lines.append(s1.index[i])
                    lines.append(s1.index[i+w[j]])
             #add rectangle for each exceeded interval
            for i in range(0,len(lines),2):
                shapes.append({'type': 'rect','xref': 'x','yref': 'paper','x0': lines[i],'y0': y0[j], 'x1': lines[i+1],'y1': y1[j],'fillcolor':col[j],'line': {'color': col[j], 'width': 0.8},'name':col[j],'layer':'below','opacity':0.3 })
        if(len(lines)!=0):
             #make graph for the sensor overtime values
            fig= go.Figure([go.Scatter(x=s1.index, y=np.round(s1['Temperature'],2),line={'color':'black','width':1.5},name='Sensor '+str(sens))])
            #add the shapes (exceeded interval rectangles)
            fig.update_layout(shapes=shapes, showlegend=True)       
            #add annotations describing each interval
            fig.add_annotation(x=1.025,y=0.9,xref='paper',yref='paper',text="Time Interval",font={'color':'black'},align='right',showarrow=False)
            fig.add_annotation(x=1.01,y=0.83,xref='paper',yref='paper',text="15 Minutes",font={'color':'black'},align='right',showarrow=False,bgcolor=col[0])
            fig.add_annotation(x=1.01,y=0.75,xref='paper',yref='paper',text="30 Minutes",font={'color':'black'},align='right',showarrow=False,bgcolor=col[1])
            fig.add_annotation(x=1,y=0.63,xref='paper',yref='paper',text="1 Hour",font={'color':'black'},align='right',showarrow=False,bgcolor=col[2])
            fig.add_annotation(x=1,y=0.55,xref='paper',yref='paper',text="2 Hours",font={'color':'black'},align='right',showarrow=False,bgcolor=col[3])
            fig.add_annotation(x=1,y=0.46,xref='paper',yref='paper',text="4 Hours",font={'color':'black'},align='right',showarrow=False,bgcolor=col[4])
            fig.update_xaxes(title_text='Date',showgrid=False)
            fig.update_yaxes(title_text='Temperature')
            fig.update_layout({'plot_bgcolor': 'white', 'paper_bgcolor': 'white', })
            fig.update_traces(hovertemplate='Sensor Number: '+str(sens)+'<br>Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Temperature: %{y}')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7',ticksuffix='°C')            
            div = opy.plot(fig, auto_open=False, output_type='div',include_plotlyjs=False,config=config)
            r.append(div)
            r.append('<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3"  >Guide on How to Read This Graph</h5><div id="tvwt_3" ><p style="padding:15px;">Time is labeled on the horizontal axis, and temperature is on the vertical axis. If any temperature variations exceed the ASHRAE 55 allowable thresholds, they are highlighted to illustrate when the event occurred.</p></div></div>')
            
        else:
              #don't add shapes if sensor has not exceeded any interval
            r.append('Sensor '+str(sens)+' has not exceeded ASHRAE 55 threshold')
            fig= go.Figure([go.Scatter(x=s1.index, y=np.round(s1['Temperature'],2),line={'color':'black','width':1.5},name='Sensor Number'+str(sens))])
            fig.update_xaxes(title_text='Date',showgrid=False)
            fig.update_yaxes(title='Temperature')
            fig.update_layout({'plot_bgcolor': 'white','paper_bgcolor': 'white',})
            fig.update_traces(hovertemplate='Sensor Number: '+str(sens)+'<br>Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Temperature: %{y}')
            fig.update_yaxes(title='Temperature',showgrid=True, gridwidth=1, gridcolor='#d7d7d7',ticksuffix='°C')
            div = opy.plot(fig, auto_open=False, output_type='div',include_plotlyjs=False,config=config)
            r.append(div)
    else:   #graph for a single interval      
        r = time_interval(sens,inter,w,ash,col,s1,r,wk_start,wk_end)
    return render(request, 'partials/render.html', {"div": r})

#CHANGED
def time_interval(s,interval,win,ash1,colo,s1,r,wk_start,wk_end): 
    '''
    Plots overtime graph of given sensor and shows portions where ashrae was exceeded for given interval.
    Parameters:
        s (string): sensor number
        interval (string): time interval
        win (int): time window
        ash1 (float): ashrae standards list
        colo (list): line colors list (not used).
        s1 (dataframe): This sensor's data.
        r (array list): contains graph div 
    Returns:
        Specified figure.
    '''      
    exceeded_color = '#ff0000'
    k=0
    lines=list()
    shapes=list() 
    #find the text, window size, and ashrae standard associated with the given interval   
    if interval=='0.25':
        k=0
        interval='15 Minutes'
    elif interval=='0.5':
        k=1
        interval='30 Minutes'
    elif interval=='1':
        k=2
        interval='1 Hour'
    elif interval=='2':
        k=3
        interval='2 Hours'
    elif interval=='4':
        k=4
        interval='4 Hours'
        
    for i in range(len(s1['Temperature'])-win[k]):
        d=abs(s1['Temperature'][i]-s1['Temperature'][i+win[k]])#absolute temperature difference between two time windows
        d=round(d,2)
        #check time difference with ashrae standards and store points which exceeded the standards
        if(d >ash1[k]):
            lines.append(s1.index[i])
            lines.append(s1.index[i+win[k]])
    #add rectangles if standard was exceeded
    for i in range(0,len(lines),2):
        shapes.append({'type': 'rect','xref': 'x','yref': 'paper','x0': lines[i],'y0': 0,'x1': lines[i+1],'y1': 1,'fillcolor':exceeded_color,'line': {'color': exceeded_color, 'width': 0.8},'layer':'below','opacity':0.2 })
    #add column that states the time period of each row, to add to hover
    s1 = add_time_period_col(s1,'',wk_start,wk_end)
    #this sensor's location
    sensor_loc = s1['Location'].unique()[0]
    #make graph
    hovertemplate = 'Sensor Number: '+str(s)+'<br>Location: '+sensor_loc+'<br>Time Period: '+s1['Time Period']+'<br>Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Temperature: %{y}<extra></extra>'
    config = config_setting('Temperature - Temperature Variations - Sensor')  
    
    fig= go.Figure([go.Scatter(x=s1.index, y=np.round(s1['Temperature'],2),line={'color':'black','width':1.5},name='Sensor '+str(s))])
    fig.update_layout(shapes=shapes, showlegend=True)       
    fig.update_xaxes(title_text='Date',showgrid=False)
    fig.update_yaxes(title_text='Temperature')
    fig.update_layout({'plot_bgcolor': 'white','paper_bgcolor': 'white',})
    fig.update_traces(hovertemplate = hovertemplate)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7',ticksuffix='°C')
     #add exceeded interval to the legend   
    fig = add_legend_text(fig, 'Exceeded Interval')
    fig.data[-1]['line']['color']=exceeded_color
    fig.data[-1]['line']['dash']='solid'
    fig.update_layout(legend_itemsizing='constant')

    div = opy.plot(fig, auto_open=False, output_type='div',include_plotlyjs=False,config=config)

    if(len(lines)!=0):
        r.append(div)
        r.append('<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" >Guide on How to Read This Graph</h5><p style="padding:15px;">Time is labeled on the horizontal axis, and temperature is on the vertical axis. If any temperature variations exceed the ASHRAE 55 allowable thresholds, they are highlighted to illustrate when the event occurred. </p></div></div>')
    else:
        r.append("Sensor "+str(s)+" has not exceeded ASHRAE 55 threshold within "+str(interval)+' interval')
        div = opy.plot(fig, auto_open=False, output_type='div',include_plotlyjs=False,config=config)
        r.append(div)
    return r