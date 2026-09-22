from tasks.models import Task
from analysis.common import *
import pandas as pd

#CHANGED
def pressure_vs_time_summary_(request,id):
    '''
    Plots average pressure of each floor and outside pressure.
    Parameters:
        request (): request
        id (int): task id
    Returns:
        Specified figure.
    '''
    task_entry = Task.objects.get(id=id) 
    occupied_time_start=task_entry.weekday_occupied_start
    occupied_time_end =task_entry.weekday_occupied_end
    buildingId = str(task_entry.building.id)

    #get data
    data=load_df(buildingId,id,"final_df.csv")
    config = config_setting('Air Pressure - Air Pressure vs. Time - Summary')
     #get data of a single sensor to plot outside pressure
    test = data['Sensor Number'].unique()
    ss1=data[data['Sensor Number']==test[0]]  
    floors=data['Floor'].unique()
    floors = [x for x in floors if str(x) != 'nan']
    #make graph
    hovertemplate = "<br>".join(["Time Period: %{customdata[0]}","Date: %{x|%b %d, %Y}","Time: %{x|%H:%M}","Air Pressure: %{y}<extra></extra>"])
    customdata = [occupied_time_start,occupied_time_end] 
    fig = general_graph_overtime_multiline(data, 'Floor', floors, 'TimeStampGrouped', 'Pressure', hovertemplate, '', 'Date', 'Air Pressure', lineWidth=1,ticksuffix='kPa',customdata=customdata)
     #format legend name for Ground (1) and negative floors
    for i in range(1,len(fig.data)+1):
        name_i = fig.data[-i].name
        if(name_i=='1'):
             #change name to proper one for Ground (1)
            fig.data[-i].name = 'Air Pressure Floor Ground (1)'
        elif(name_i.startswith('-')):
            #replace negative sign of floor with B
            name_i = name_i.replace('-', 'B', 1)
            fig.data[-i].name = 'Air Pressure Floor '+name_i
        else:
             #else only add Air Pressure Floor
            fig.data[-i].name = 'Air Pressure Floor '+name_i
    #add outside pressure if present
    if 'Pressure_Outside' in ss1:
        out=ss1['Pressure_Outside'].groupby(ss1.index).mean()
        out=pd.concat([out],axis=1).reset_index()        
        fig = plot_add_dotted_line(fig,out['TimeStamp'],round(out['Pressure_Outside'],2),'Outside Air Pressure',"<br>".join(["Date: %{x|%b %d, %Y}","Time: %{x|%H:%M}","Outside Air Pressure: %{y}<extra></extra>"]),[],'#20b2aa')
    fig.update_layout(legend= {'itemsizing': 'constant'})
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7')
    div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3">Guide on How to Read This Graph</h5><p style="padding:15px;">Time is labeled on the horizontal axis, and the absolute air pressure is on the vertical axis. This figure illustrates the average air pressure over time per building floor, with outside air pressure for reference.</p></div></div>'
    return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'')

#CHANGED
def pressure_differential_floor_plan_(request,id):
    '''
    Plots floormap showing sensors and their pressure for chosen statistic.
    Parameters:
        request (): request
        id (int): task id
    Returns:
		Specified figure.
    '''

    #get data
    task_entry = Task.objects.get(id=id) 
    buildingId = str(task_entry.building.id)
    data=load_df(buildingId,id,"final_df.csv")
    occ=load_df(buildingId,id,"occ.csv")
    cur_width=int(request.POST.get("width",None))
    floor,occupied=get_fl_occupied(request)
    statistic=request.POST.get("statistic",None)
    data,time = check_occupied_df(buildingId,id,'Occupied')
    #get text of data's date range, for hover
    dateRangeText = get_date_range_text(occ)
    
    #get image and variables needed for floorplan
    co_df,img,img_width,img_height,scale_factor,wk_start,wk_end=get_sensors_images(buildingId,id,floor,cur_width)
    if not co_df.empty:
        #get data needed for pressure floormap based on given statistic
        s_df,st_val=map_dataP(floor,statistic,occ,co_df)

        #add location info 
        l_df = data.copy()
        l_df = l_df.drop_duplicates('Sensor Number')
        l_df = l_df[['Sensor Number','Location']]
        s_df = pd.merge(s_df,l_df,on='Sensor Number',how='left')

        config = config_setting('Pressure - Pressure Differential - Heatmap')  
        #make graph
        color_scale = [(0,"#0E5DA8"),(0.11,"#208B93"),(0.22,"#47B489"),(0.33,"#5BBA47"),(0.44,"#9BCA3D"),(0.55,"#D1D029"),(0.66,"#F0E443"),(0.77,"#EFA243"),(0.88,"#EF5A45"),(1.0,"#EF5A45")]
        tickvals = [-0.075,-0.06,-0.043,-0.027,-0.01,0.007,0.023,0.041,0.057,0.075]
        ticktext = ["-0.075kPa","-0.06kPa","-0.045kPa","-0.03kPa", "-0.015kPa","+0.015kPa","+0.03kPa","+0.045kPa","+0.06kPa","+0.075kPa"]  
        hovertemplate = "Location: "+s_df['Location']+"<br>Time Period: "+time+dateRangeText+"<br>Sensor Number: "+s_df['Sensor Number'].astype(str)+"<br>Air Pressure: "+ round(s_df['Pressure'],2).astype(str)+"kPa<br>"+statistic+" Air Pressure: "+str(round(st_val,2))+"kPa<br>Air Pressure Differential: "+round(s_df['P_diff'],3).astype(str)+"kPa<extra></extra>"
        fig = general_floormap(s_df, img, img_width, img_height, scale_factor, 'P_diff', 'Sensor Number', color_scale, tickvals, ticktext, 'Air Pressure', -0.05, 0.05, [], hovertemplate, -0.075, 0.075, 400,'','Occupied Hours',wk_start,wk_end)
        text = 'Pressure differentials are displayed for '
        fig = add_xlabel_occupancy_text(fig,text,time,wk_start,wk_end)
        div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3">Guide on How to Read This Graph</h5><p style="padding:15px;">This figure provides a simple representation of the average differential pressure values on a building floor plan based on the mean, median, minimum, or maximum pressure measurement within that space. For example, if “minimum” is selected as the reference, all values represented other than the minimum value will be positive (or greater than) the sensor that measured the minimum value.</p></div></div>'
        return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'')
    else:        
        return "floor"+floor+" floor plan image does not exist or sensor mapping is not done. Please upload image(s) and finish sensor mapping."

def pressure_differential_sensor_pair_(request,id):
    '''
    Plot overtime graph of pressure difference between two specified sensors.
    Parameters:
        request (): request
        id (int): #task id
    Returns:
		Specified figure.
    '''
    sensor1 = request.POST.get('sensor1',None)
    sensor2 = request.POST.get('sensor2',None)
    task_entry = Task.objects.get(id=id) 
    buildingId = str(task_entry.building.id)
    final_df=load_df(buildingId,id,"final_df.csv")
    config = config_setting('Air Pressure - Air Pressure Differential - Sensor Pair')
     #get data of each sensor, and find the difference
    s1=final_df[final_df['Sensor Number']==sensor1]
    s2=final_df[final_df['Sensor Number']==sensor2]   
    diff=s1['Pressure']-s2['Pressure']   
    diff = np.round(diff,4) 
     #make graph
    fig = general_graph_overtime(s1.index,diff, 'Date', 'Air Pressure Difference', [], 'Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Air Pressure Difference: %{y}', "#065BA7",ticksuffix='kPa')
    #add a dotted line at 0 point
    fig = plot_add_dotted_line(fig,s1.index,[0]*len(s1.index),'','',[],'black',2)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7')
    fig.update_layout(showlegend=False)
    fig.update_traces(hoverinfo='none')
    div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3">Guide on How to Read This Graph</h5><p style="padding:15px;">Time is labeled on the horizontal axis, and the air pressure differential is on the vertical axis. This figure illustrates the air pressure differences between the two selected sensors on the same floor over time. Positive pressure differential values suggest that the direction of airflow is from the first sensor selected to the second sensor selected, assuming they are in close proximity and not acted on by other sources (for example, an open window). Negative pressure differential values suggest that the direction of airflow is from the second sensor selected to the first sensor selected.</p></div></div>'
    return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'')

def map_dataP(f,compare,occ,co_df):
    '''
    Find pressure data based on specified statistic for pressure floormap.
    Parameters:
        f (string): Floor number.
        compare (string): statistics that we are going to compare with (Min,Max,Mean, or Median).
        occ (dataframe): Sensors' data for occupied time.
        co_df (dataframe): Contains sensor numbers and their coordinate on the floorplan.
    Returns:
        df (dataframe): Contains sensor numbers, their coordinates, and pressure data.
        val (float): Value of the specified statistics accross all sensors.
    '''    
    dd,df,a,s_num=map_data(occ,f,co_df,'Pressure') 
    if compare=='Minimum':
        df['P_diff']=df['Pressure']-df['Pressure'].min()
        val=df['Pressure'].min()
    elif compare=='Maximum':
        df['P_diff']=df['Pressure'].max()-df['Pressure']
        val=df['Pressure'].max()
    elif compare=='Mean':
        df['P_diff']=df['Pressure'].mean()-df['Pressure']
        val=df['Pressure'].mean()
    elif compare=='Median':
        df['P_diff']=df['Pressure'].median()-df['Pressure']
        val=df['Pressure'].median()
    return df,val