import io
from tasks.models import Task
from analysis.common import *
import pandas as pd
from plotly.subplots import make_subplots

#CHANGED
# Thermal Comfort -- Occupant Comfort - Summary
def occupant_comfort_summary_(request,floor,occ,locations,action,time,wk_start,wk_end,buildingId,versionId):
    '''
    Make barplots showing comfortable percentage for each location.
    Parameters:
        request (): request
        floor (string): Floor number.
        occ (dataframe): Occupied time data.
        locations (list): List of locations.
        action (string): Whether to use the graph for report or in the modules.
        time (string): Time period.
        wk_start (string): Time when occupancy starts.
        wk_end (string): Time when occupancy ends.
        buildingId (int): building id
        versionId (int): task id
    Returns:
        Specified figure.
    '''
    config = config_setting('Thermal Comfort - Occupant Comfort - Summary')  
    
    #find average comfort percent f or each location
    table=get_comf_percent_summary(occ,locations,floor)   
    #get text of data's date range, for hover   
    dateRangeText = get_date_range_text(occ)
    #make figure
    hovertemplate='Building Floor: '+str(floor)+'<br>Location: %{x}<br>Time Period: '+str(time)+dateRangeText+'<br>Percent of Time in Comfortable Range: %{y}<extra></extra>'

    fig = general_barplot(table['Location'], table['comf_percentage'].astype(int), 'Location', 'Percent of Time in Comfortable Range', "%{y}", [], hovertemplate, [0,110], ticksuffix='%',time=time,wk_start=wk_start,wk_end=wk_end)    
    #add target line
    fig.add_trace(go.Scatter(x=table['Location'],y=[100]*len(table), mode='lines', line=dict(color='#9BCA3B', width=3), name = 'Target'))
    fig.update_xaxes(tickangle = 90,showline=True, linewidth=1, linecolor='black')   
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7')
    fig.update_layout(legend_traceorder="reversed") 
    if action == 'report': # if this is called from report section, save the graph to specific place   
        return export_to_png(fig,buildingId,id,'occupant_comfort_summary_'+str(versionId)+'.png')
    else:
        div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3"  data-target="#ptc_1"  >Guide on How to Read This Graph</h5><p style="padding:15px;">The locations where measurements were recorded are labeled on the horizontal axis. The average percentage of the occupied time period that each location was within the comfortable range is labeled on the vertical axis. The occupied time period is defined as the time of day when people typically work or reside within the space and when thermal comfort is most critical. It is building dependent and input by the user prior to performing this analysis. The target value is 100%, which means that the corresponding location was comfortable during the entire occupied time period.</p></div></div>'
        return generate_fig_to_div(request,fig,config,div_info,buildingId,versionId,'occupant_comfort_summary_'+str(versionId)+'.png')

def get_comf_percent_summary(data, locations,floor='Building'):
    '''
    Get comfort percentage of locations within building or specified floor.
    Parameters:
        data (dataframe): Contains sensors and their data.
        locations (list): Locations to use.
        floor (string): use this floor's data only.
    Returns:
        df (dataframe): Contains sensors and their comfort percentage.
    '''
    zone = sorted(locations)
    loc = list()
    comfp = list()
    for z in zone:
        #filter by this location
        f_data = data[data['Location'] == z]
        #filter by floor
        if(floor != 'Building'):
            #find comfort percentage for this location and add them to their lists
            f_data = f_data[f_data['Floor'] == floor]
        if(len(f_data) != 0):
            loc.append(z)
            PT=round(len(f_data[f_data['Comfort']==1])*100/len(f_data),2) #change ==1 to ==True if it doesn't work
            comfp.append(PT)
    dict = {'Location': loc, 'comf_percentage': comfp}
    df = pd.DataFrame(dict)
    return df

# Thermal Comfort -- Occupant Comfort - Location
def occupant_comfort_location_(request,id):
    '''
    Make barplots showing the percent time comfortable for each day.
    Parameters:
        request (): request
        id (int): #task id
    Returns:
        Specified figure.
    '''
    # get all values from post request
    buildingId,wk_start,wk_end=get_vars(id)    

    #get occupied data and filter by floor, location, and space
    occ=load_df(buildingId,id,"occ.csv")
    floor,loc,space = get_fl_loc_per_var(request)# get floor , location and perimeter values from post request
    data = check_floor_loc_per(floor,loc,space,occ) # filter data by floor, location and perimeter
    config = config_setting('Thermal Comfort - Occupant Comfort - Location') # generate the settings
    r=[]    
    days=data['Date'].unique()
    days_used = []#CHANGED
    comfp=list()    
    if len(data)!=0:
        for i in days:#go through each day
            dd=data[data['Date']==i]
            if len(dd)!=0:
                #add comfort percentage of that day to the list
                PT=round(len(dd[dd['Comfort']==True])*100/len(dd),2)
                comfp.append(PT)
                days_used.append(i)#CHANGED
        dict = {'Days': days_used, 'comf_percentage': comfp}  
        df = pd.DataFrame(dict) 
        #make graph
        x=df['Days']
        y=df['comf_percentage'].astype(int)        
        yaxis_label = 'Percent of Time in Comfortable Range'
        hovertemplate = hovertemplate_days_barplot(floor,loc,space,'Occupied Hours',yaxis_label)
        yrange = [0,110]
        fig = general_barplot(x, y, 'Date', yaxis_label, '%{y}', [], hovertemplate, yrange, '%', [], '','Occupied Hours',wk_start,wk_end)
        #add target line
        fig.add_trace(go.Scatter(x=x,y=[100]*len(x), mode='lines', line={'color':'#9BCA3B', 'width':3}, name = 'Target'))
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7')
        fig.update_layout(legend_traceorder="reversed")
         
        div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3">Guide on How to Read This Graph</h5><p style="padding:15px;">The days during which measurements were recorded are labeled on the horizontal axis. The daily average percentage of the occupied time period that each specific location was within the comfortable range is labeled on the vertical axis. The occupied time period is building dependent and the user specifies the occupied time period for both weekdays and weekends upon creating a test version prior to running the data analysis. The target value is 100%, which means that the corresponding location was comfortable during the entire occupied time period. </p></div></div>'    
        return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'occupant_comfort_location_'+str(id)+'.png')
    else:
        if floor=='Building':
            r.append('There are no '+str(loc)+' in '+str(floor))
            return r
        else:
            r.append('There are no '+str(loc)+' in Floor '+str(floor))
            return r

#CHANGED
# Thermal Comfort -- Occupant Comfort - Sensor
def occupant_comfort_sensor_(request,id):
    '''
    Plot specified sensor's temperature and relative humidity and ourside temperature and relative humidity.
    Parameters:
        request (): request
        id (int): task id
    Returns:
        Specified figure.
    '''
    task_entry = Task.objects.get(id=id)
    buildingId = str(task_entry.building.id)
    sensor_id = request.POST.get('sensor')

    #get data and filter by for this sensor
    final_df=load_df(buildingId,id,"final_df.csv")  
    occ=load_df(buildingId,id,"occ.csv")
    s1=final_df[final_df['Sensor Number']==sensor_id]
    s1['Temperature'] = np.round(s1['Temperature'],2)
    s1['Humidity'] = np.round(s1['Humidity'],2)
    so1=occ[occ['Sensor Number']==sensor_id]   

    #find comfort during all time and occupied time
    Full=round(len(s1[s1['Comfort']==True])*100/len(s1),2)
    occupied=round(len(so1[so1['Comfort']==True])*100/len(so1),2)

    #add if sensor's temp is in comfort range 
    occ_start=task_entry.weekday_occupied_start
    occ_end=task_entry.weekday_occupied_end
    #add if sensor's temp is in comfort range 
    s1['Temp Comf'] = 'No'
    s1.loc[(s1['Temperature']>=20) & (s1['Temperature']<=24),'Temp Comf'] = 'Yes'
    #add if sensor's rh is in comfort range
    s1['Humidity Comf'] = 'No'
    s1.loc[(s1['Humidity']>=20) & (s1['Humidity']<=60),'Humidity Comf'] = 'Yes'
    #this sensor's location
    location = s1['Location'].unique()[0] 
    #add column that states the time period of each row, to add to hover
    s1 = add_time_period_col(s1,'',occ_start,occ_end)

    config = config_setting('Thermal Comfort - Occupant Comfort - Sensor')
    #make a figure with two yaxes
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    #add sensor's temperature trace
    hovertemplate = 'Sensor Number: '+str(sensor_id)+'<br>Location: '+str(location)+'<br>Time Period: '+s1['Time Period']+'<br>Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Temperature: %{y}<br>Temperature Comfortable: '+s1['Temp Comf']+'<extra></extra>' 
    fig.add_trace(go.Scatter(x=s1.index, y=s1['Temperature'],text='Temperature', name='Temperature(°C)', hovertemplate=hovertemplate, marker={'color':'red', 'size':3},),secondary_y=False,)       
    #add sensor's rh trace
    hovertemplate = 'Sensor Number: '+str(sensor_id)+'<br>Location: '+str(location)+'<br>Time Period: '+s1['Time Period']+'<br>Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Relative Humidity: %{y}<br>Relative Humidity Comfortable: '+s1['Humidity Comf']+'<extra></extra>'
    fig.add_trace(go.Scatter(x=s1.index,y=s1['Humidity'],name='Relative Humidity (%)',hovertemplate=hovertemplate, marker={'color':'blue','size':3},),secondary_y=True,)
     #add outside temperature and rh if present
    if 'Temperature_Outside' in s1:      
        s1['Temperature_Outside'] = np.round(s1['Temperature_Outside'],2)
        s1['Humidity_Outside'] = np.round(s1['Humidity_Outside'],2)
        fig = plot_add_dotted_line(fig, s1.index, s1['Temperature_Outside'], 'Outside Temperature (°C)', 'Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Outside Temperature: %{y}<extra></extra>', [], '#ff3fff', 2,False)
        fig = plot_add_dotted_line(fig, s1.index, s1['Humidity_Outside'], 'Outside Relative Humidity (%)','Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Outside Relative Humidity: %{y}<extra></extra>', [], '#20b2aa', 2,True)
    # Add shape regions for when there is occupancy
    x00=list()   
    for i in range(len(s1)-1): 
        if (i==0 and s1['Comfort'][i]==True) or (s1['Comfort'][i]==True and s1['Comfort'][i+1] != s1['Comfort'][i]):
            x00.append(s1.index[i])            
        elif (i+2 == len(s1) and s1['Comfort'][i+1]==True) or ((s1['Comfort'][i]==False) and s1['Comfort'][i+1] != s1['Comfort'][i]):
            x00.append(s1.index[i+1])            
        if (len(x00)==2):#if have seen comf to uncomf, add that region as a rectangle showing comfortable period
            fig.add_vrect(x0=x00[0], x1=x00[1],fillcolor="lightgreen", opacity=0.3,layer="below", line_width=0,)
            x00=list()    
    fig.update_xaxes(title_text="Date")
    fig.update_layout({'plot_bgcolor': 'white','paper_bgcolor': 'white',},legend= {'itemsizing': 'constant'})
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7')
    # Set y-axes titles
    fig.update_yaxes(title_text='Temperature',ticksuffix="°C", secondary_y=False)
    fig.update_yaxes(title_text='Humidity',ticksuffix="%", secondary_y=True)
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.7, xanchor="right", x=0.8))
    fig.update_layout(legend= {'itemsizing': 'constant'})
    text = str(occupied)+"% comfortable during occupied hours and "+str(Full)+"% comfortable during the recorded time"   
    
    #add comfort range text
    fig = add_comfort_range_legend(fig)
    fig.update_xaxes(dtick='D',tickformat="%a<br>%b %d") 

    fig.update_layout(title={'text': text,'font':{'size': 14}})
    div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3">Guide on How to Read This Graph</h5><p style="padding:15px;">The time during which measurements were recorded is labeled on the horizontal axis. Temperature and relative humidity measurements recorded by a specific sensor are labeled on the left and right vertical axes, respectively. Time spent within the comfortable range is highlighted in green. Outside air temperature and relative humidity values are also included for reference.</p></div></div>'
    return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'occupant_comfort_sensor_'+str(id)+'.png')
    
#CHANGED
# Thermal Comfort -- Occupant Comfort - Floor Plan    
def occupant_comfort_floor_plan_(request,data,floor,co_df,image,img_width,img_height,scale_factor,action,time,wk_start,wk_end,buildingId,id):
    '''
    Graph floormap showing sensors and their comfortable percentage.
    Parameters:
        request (): request
        data (dataframe): Data.
        floor (string): Floor number.
        co_df (dataframe): Contains sensor numbers and their coordinate on the floorplan image.
        image (String): The floor's image from BuildingImages
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
    if len(co_df):
        #get text of data's date range, for hover
        dateRangeText = get_date_range_text(data)
        #get sensors comfort percent and combine it with coordinate info, keep only sensors common to both
        p_df=get_comf_percent(data,floor)
        p_df['comf_percentage'] = np.round(p_df['comf_percentage'],1)    
        co_df=pd.DataFrame(co_df, columns = ['snsr_num', 'x', 'y'])
        co_df2 = co_df.rename(columns={'snsr_num':'Sensor Number'})
        p_df = p_df[p_df['Sensor Number'].isin(co_df2['Sensor Number'].values)]
        s_df = pd.merge(p_df,co_df2,on='Sensor Number',how='left')

         #add location info to s_df
        l_df = data.copy() 
        l_df = l_df.reset_index(drop=True)
        l_df = l_df.drop_duplicates(subset=['Sensor Number'],keep='first')
        l_df = l_df[['Sensor Number','Location']]
        s_df = pd.merge(s_df,l_df,on='Sensor Number',how='left')

        #make figure
        color_scale = [(0,"#EF5A45"),(0.11,"#EFA243"),(0.22,"#F0E443"),(0.33,"#D1D029"),(0.44,"#9BCA3D"),(0.55,"#5BBA47"),(0.66,"#47B489"),(0.77,"#208B93"),(0.88,"#0E5DA8"),(1.0,"#0E5DA8")] 
        hovertemplate='Time Period: '+str(time)+'<br>Location: '+s_df['Location']+'<br>Time Period: '+str(time)+dateRangeText+'<br>Percent of Time in Comfortable Range: '+s_df['comf_percentage'].astype(str)+'%<extra></extra>'

        config = config_setting('Thermal Comfort - Percent of Time Comfortable - Heatmap')
        fig = general_floormap(s_df, image, img_width, img_height, scale_factor, 'comf_percentage', 'Sensor Number', color_scale, [0,50.0,100.0], ["0%", "50%","100%"], 'Percent of Time in <br>Comfortable Range', 11, 55, [], hovertemplate, 0, 100,400,'','Occupied Hours',wk_start,wk_end)
        #Add descriptive text under the graph
        text = 'Average percent of time comfortable are displayed for '
        fig = add_xlabel_occupancy_text(fig,text,time,wk_start,wk_end)
        if action == 'report':   
            return export_to_png(fig,buildingId,id,'occupant_comfort_floor_plan_'+str(id)+'.png')
        else:
            div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3">Guide on How to Read This Graph</h5><p style="padding:15px;">The locations where measurements were recorded are labeled on the horizontal axis. The average percentage of the occupied time period that each location was within the comfortable range is labeled on the vertical axis. The occupied time period is building dependent and it is inputted by the user prior to performing this analysis. The target value is 100%, which means that the corresponding location was comfortable during the entire occupied time period.</p></div></div>'
            return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'occupant_comfort_floor_plan_'+str(id)+'.png')   
    else:        
        r= "floor"+floor+" floor plan image does not exist or sensor mapping is not done. Please upload image(s) and finish sensor mapping."
        return render(request, 'partials/render.html', {"div": r})

def get_comf_percent(time_data,f):
    '''
    Return comfort percentage of each sensor.
    Parameters:
        time_data (dataframe): Contains sensors' data.
        f (string): Use this floor's data only.
    Returns:
        df (dataframe): Contains sensor numbers and their percentage of time comfortable.
    '''        
    sens=time_data[time_data['Floor']==f]['Sensor Number'].unique().astype('str')
    p=list()
    for i in sens:
        #find comfort percent for this sensor
        s=time_data[time_data['Sensor Number']==i]        
        p.append(round(len(s[s['Comfort']==True])*100/len(s),2))
    dict = {'Sensor Number': sens, 'comf_percentage': p}  
    df = pd.DataFrame(dict)
    return df

#CHANGED
def occupant_comfort_temp_RH_(request,id):
    '''
    Graphs a scatter plot showing temperature, relative humidity, and comfort percentages of each sensor.
    Parameters:
        request (): request
        id (int): task id
    Returns:
        Specified figure. 
    '''
    buildingId,wk_start,wk_end=get_vars(id) # get all values by task id
    floor,loc,space = get_fl_loc_per_var(request) #get all floor, location and perimeter values from post request
    occ=load_df(buildingId,id,"occ.csv") # load data
    data = check_floor_loc_per(floor,loc,space,occ) # filter data by floor, location and perimeter
    dateRangeText = get_date_range_text(data)##get text of data's date range, for hover
    X=building_data(data)
    X=X.dropna()
    p=list()
    config = config_setting('Thermal Comfort - Occupant Comfort - Temperature vs. Relative Humidity')
    a =X['Sensor Number'].unique()    ##find average comfort percent of each sensor
    for i in a:
        s=occ[occ['Sensor Number']==i]
        if len(s) !=0:
            p.append(round(len(s[s['Comfort']==True])*100/len(s),2))
    X['Comfort']=p
    X['Temp']=round(X['Temp'],2)
    X['Hum']=round(X['Hum'],2)   
    # col=list() #don't need?
    # for i in X.Comfort:
    #     if i>=80:
    #         col.append('black')
    #     else:
    #         col.append('white')  
    # 
    # #make figure  
    hovertemplate = "Location: %{customdata[0]}<br>Time Period: Occupied Hours"+dateRangeText+"<br>Temperature: %{x}<br>Relative Humidity: %{y}<br>Percent of Time in Comfortable Range: %{customdata[1]}%<extra></extra>"
    fig = general_threeVar_scatter(X, 'Temp', 'Hum', 'Comfort',20, 5, 70, 'Temperature', 'Relative Humidity', "Percent of Time in <br>Comfortable Range", hovertemplate, ['Location','Comfort'], [0,100], '°C', '%', '%')
   
   
    # comfortText = '<b><span style="font-size: 10px;">Comfortable Range<br>20-24°C, 20-60%RH'+'</span></b>'
    # timeText = get_occupancy_text('Occupied Hours',wk_start,wk_end,10)
    # fig = add_legend_text(fig,comfortText)
    # fig.data[-1]['line']['color']='#f7e76b'
    # fig.data[-1]['line']['dash']='solid'
    # fig = add_legend_text(fig,timeText)   

    #add text for comfortable range
    fig = add_comfort_range_legend(fig)

    #add text for time period
    timeText = get_occupancy_text("Occupied Hours",wk_start,wk_end) 
    fig = add_legend_text(fig,timeText)

    #save axis ranges, so we don't zoom out due to comfort range
    fig_layout_save = fig.full_figure_for_development()
    fig.update_layout(xaxis_range=fig_layout_save.layout.xaxis.range,yaxis_range=fig_layout_save.layout.yaxis.range)
    fig = plot_add_box(fig,20,20,24,60,'lightgreen','lightgreen',opacity=0.3)
    div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3">Guide on How to Read This Graph</h5><p style="padding:15px;">Temperature is labeled on the horizontal axis, and relative humidity is on the vertical axis. This figure shows the average temperature and relative humidity values recorded per sensor, and also illustrates the percentage of time spent within the comfortable range during the occupied time period for that sensor. It can be used to identify outliers and potential problem areas. For example, if a location is plotted within the comfortable range (i.e. 22°C, 50% RH) but also labeled as 20% comfortable, then that location was outside of the comfortable temperature range, relative humidity range, or both for 80% of the occupied time period.</p></div></div>'
    return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'occupant_comfort_temp_RH_'+str(id)+'.png')   

def building_data(data): 
    '''
    Return average temperature, humidity and pressure values for each sensor.
    Parameters:
        data (dataframe): Contains sensors' data.
    Returns:
        mean_d (dataframe): Contains average values of each sensor.
    '''    
    Temp=data['Temperature'].groupby(data['Sensor Number']).mean() #mean group by sensor number
    Temp=pd.concat([Temp],axis=1).reset_index()
    sens=Temp['Sensor Number']
    loc=list()
    temp=list()
    hum=list()
    pre=list()
    for i in sens:
        d=data[data['Sensor Number']==i]
        loc.append(d['Location'].unique())#add location
        temp.append(d['Temperature'].mean())#add mean temp
        hum.append(d['Humidity'].mean())#add mean rh
        pre.append(d['Pressure'].mean())    #add mean pressure 
    dict = {'Sensor Number': sens, 'Location':loc, 'Temp':temp, 'Hum':hum, 'Pres':pre}  
    mean_d = pd.DataFrame(dict)    
    return mean_d