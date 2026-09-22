import io
from tasks.models import Task
from analysis.common import *
import pandas as pd

#CHANGED
def air_quality_tvoc_summary_(request,id):
    '''
    Make barplots of mean TVOC values of each location.
    Parameters:
        request ():request
        id (int): task id
    Returns:
        Specified figure.
    '''
    floor,occupied=get_fl_occupied(request)
    buildingId,wk_start,wk_end=get_vars(id)

    #get data
    time,data = get_occupied_iaq_data(buildingId,id,occupied)
    data['Date'] = data['TimeStamp'].dt.strftime('%Y-%m-%d')

    if not data.empty:

        #get text of data's date range, for hover
        dateRangeText = get_date_range_text(data)

        #filter by floor
        data=get_floor_iaq(data,floor)

        #find mean tvoc value of each location
        table=data['TVOC'].groupby(data['Location']).mean() #mean group by sensor number
        table=pd.concat([table],axis=1).reset_index()  

        #make figure      
        hovertemplate='Building Floor: '+str(floor)+'<br>Location: %{x}<br>Time Period: '+str(time)+dateRangeText+'<br>TVOCs Concentration: %{y} '+'<extra></extra>'
        fig = general_barplot(table['Location'], table['TVOC'].astype(int)  , 'Location', 'Total Volatile Organic Compounds Concentration', "%{y} ", [], hovertemplate,[],'ppb',[],[],time,wk_start,wk_end)
        
        #add target line
        fig.add_hline(y=50,line_width=3,line_color='#9BCA3B') 
        fig = add_legend_text(fig,'Ideal Level')
        fig.data[-1]['line']['color']='#9BCA3B'
        fig.data[-1]['line']['dash']='solid'
        fig.update_layout(legend_traceorder="reversed")
        
        fig.update_yaxes(rangemode="tozero")
        fig.update_layout(margin={'t':100, 'b':25})
        config =config_setting('Air Quality - TVOC - Summary')
        div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" data-target="#tahm_3"  >Guide on How to Read This Graph</h5><div id="tahm_3" ><p style="padding:15px;">The locations where measurements were recorded are labeled on the horizontal axis. The average TVOC equivalent value for the selected floor during the selected time period is labeled on the vertical axis.</p></div></div>'
        return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'')
    else:
        return "no data exist"

def get_occupied_iaq_data(buildingId,id,occupied):
    '''
    Get data of specified time period.
    Parameters:
        buildingId(int)): Id of the building. 
        id (int): Id of the test version.
        occupied (string): Time period.
    Returns:
        time (string): Time period text.
        data (dataframe): Data of the specified period.
    '''
    time=''
    if occupied == "Entire Day":
        data = load_df(buildingId,id,"iaq_df.csv")
        time='All Hours'  
    elif occupied=="Occupied":
        data = load_df(buildingId,id,"iaq_occ.csv")
        time='Occupied Hours'
    else:
        data = load_df(buildingId,id,"iaq_non_occ.csv")
        time = 'Unoccupied Hours'
    data=data.reset_index()
    data['TimeStamp'] =pd.to_datetime(data['TimeStamp'])     
    data['Floor']=data['Floor'].astype(str)
    data['Sensor Number']=data['Sensor Number'].astype(str)
    data=data.set_index('Date') 
   
    return time,data

#CHANGED
def air_quality_tvoc_location_(request,id):
    '''
    Show barplot for mean TVOC values of different days.
    Parameters:
        request (): request
        id (int): task id
    Returns:
        figure: HTML division containing figure. 
    '''
    floor,occupied=get_fl_occupied(request)
    buildingId,wk_start,wk_end=get_vars(id)
    data=load_df(buildingId,id,"iaq_df.csv")
    floor,loc,space = get_fl_loc_per_var(request)    
    time,data = get_occupied_iaq_data(buildingId,id,occupied)
    data = check_floor_loc_per(floor,loc,space,data)

     #get data and filter by floor, location, and perimeter
    tb=data['TVOC'].groupby(data.index).mean() #mean group by sensor number    
    tb=pd.concat([tb],axis=1).reset_index() 

    #make figure
    hovertemplate =hovertemplate_days_barplot(floor,loc,space,time,'TVOCs Concentration')
    fig = general_barplot(tb['Date'], tb['TVOC'].astype(int), 'Date', 'Total Volatile Organic Compounds Concentration ', "%{y} " + '' , [], hovertemplate,[],'ppb',[],[],time,wk_start,wk_end)
    
    #add target line
    fig.add_hline(y=50,line_width=3,line_color='#9BCA3B') 
    fig = add_legend_text(fig,'Ideal Level')
    fig.data[-1]['line']['color']='#9BCA3B'
    fig.data[-1]['line']['dash']='solid'
    fig.update_layout(legend_traceorder="reversed")
    
    fig.update_yaxes(rangemode="tozero")
    fig.update_layout(margin={'t':100, 'b':25})
    config =config_setting('Air Quality - TVOC - Location')
    div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" data-target="#tahm_3"  >Guide on How to Read This Graph</h5><div id="tahm_3" ><p style="padding:15px;">The days during which measurements were recorded are labeled on the horizontal axis. The daily average TVOC equivalents for the selected location and time period is labeled on the vertical axis.</p></div></div>'
    return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'')

#CHANGED
def air_quality_tvoc_sensor_(request,id):
    '''
    Show graph of TVOC values overtime for specified sensor.
    Parameters:
        request (): request
        id (int): task id 
        occ_start (string): Time of start of occupancy.
        occ_end (string): Time of end of occupancy.
    Returns:
        figure: HTML division containing figure. 
    '''
    task_entry = Task.objects.get(id=id)
    occ_start=task_entry.weekday_occupied_start
    occ_end =task_entry.weekday_occupied_end
    buildingId = str(task_entry.building.id)

    #get data of entire day
    time,data = get_occupied_iaq_data(buildingId,id,"Entire Day")


    sens = request.POST.get("sensor",None)
    floor = request.POST.get("floor",None)

    #get data of the sensor
    new=get_floor_sens_iaq(data,sens)
    new=new.set_index('TimeStamp')

    #add column that states the time period of each row, to add to hover
    new = add_time_period_col(new,'',occ_start,occ_end)

    #get sensor's location, to add to hover
    sensor_loc = new['Location'].unique()[0]

    #make figure
    hovertemplate='Building Floor: '+str(floor)+'<br>Sensor Number: '+str(sens)+'<br>Location: '+sensor_loc+'<br>Time Period: '+new['Time Period']+'<br>Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>TVOCs Concentration: %{y}<extra></extra>'
    fig = general_graph_overtime(new.index, new['TVOC'].astype(int), 'Date', 'Total Volatile Organic Compounds Concentration', [], hovertemplate=hovertemplate,ticksuffix='ppb')
    
    #add target line
    fig.add_hline(y=50,line_width=3,line_color='#9BCA3B') 
    fig = add_legend_text(fig,'Ideal Level')
    fig.data[-1]['line']['color']='#9BCA3B'
    fig.data[-1]['line']['dash']='solid'
    fig.update_layout(legend_traceorder="reversed")
    
    fig.update_yaxes(rangemode="tozero")
    fig.update_layout(margin={'t':100, 'b':25})
    config =config_setting('Air Quality - TVOC - Sensor')
    div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" data-target="#tahm_3"  >Guide on How to Read This Graph</h5><div id="tahm_3" ><p style="padding:15px;">Time is labeled on the horizontal axis, and the measured total volatile organic compounds (TVOC) value is on the vertical axis. This figure represents the measured TVOC values over time for the selected sensor.</p></div></div>'
    return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'')

#CHANGED
def air_quality_tvoc_floor_plan_(request,id):
    '''
    Make floor plan containing sensors and their mean TVOC values.
    Parameters:
        request (): request
        id (int): task id
    Returns:
        Specified figure.
    '''
    cur_width=int(request.POST.get("width",None)) # user screen width
    buildingId,wk_start,wk_end=get_vars(id)
    floor,occupied=get_fl_occupied(request)

     #get data for the time period
    time,data = get_occupied_iaq_data(buildingId,id,occupied)
    dataframe=data[data['Floor']==floor]
    dataframe['Date'] = dataframe['TimeStamp'].dt.strftime('%Y-%m-%d')

    #get image and variables needed for floorplan
    co_df,img,img_width,img_height,scale_factor,wk_start,wk_end=get_sensors_images(buildingId,id,floor,cur_width)

    #get text of data's date range, for hover
    dateRangeText = get_date_range_text(dataframe) 
    if not co_df.empty:

        #get data needed for tvoc floorplan (mean tvoc values, tvoc level)
        s_df=map_data_tvoc(dataframe,floor,co_df)   
        s_df['TVOC'] = np.rint(s_df['TVOC']).astype(int)  

        #color bar properties   
        factor = 0.85       
        color_scale = [(0, '#2B68F1'),(0.1*factor, '#25CE27'), (1/3*factor, '#E7F43E'), (factor, '#FC2107'), (1, '#2F1543')]
        tickvals = [0,50,100,200,600,800]
        ticktext = ["0ppb","50ppb (Excellent)","100ppb (Good)", "200ppb (Acceptable)","600ppb (Substandard)", "800ppb (Unacceptable)"]

        #make figure
        legend_title = 'Mean TVOCs <br>Concentration' 
        hovertemplate = "Location: "+s_df['Location'].astype(str)+"<br>Time Period: "+str(time)+dateRangeText+"<br>TVOCs Concentration: "+ s_df['TVOC'].astype(str)+" ppb <br>Level: "+s_df['Type'].astype(str)+"<extra></extra>"   
        fig = general_floormap(s_df,img,img_width,img_height,scale_factor, 'TVOC', 'Sensor Number', color_scale, tickvals, ticktext, legend_title, 50, 600, [], hovertemplate, 0, 800/factor,400,'',time,wk_start,wk_end)
        text = 'Average total volatile organic compound concentrations are displayed for '
        fig = add_xlabel_occupancy_text(fig,text,time,wk_start,wk_end)
        config =config_setting('Air Quality - TVOC - Floormap')
        div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" data-target="#tahm_3"  >Guide on How to Read This Graph</h5><div id="tahm_3" ><p style="padding:15px;">The average total volatile organic compounds (TVOC) that each sensor measured is overlaid on a floor plan. Green values represent lower TVOC values, while red values represent higher TVOC values. </p></div></div>'
        return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'')
    else:
        return "floor"+floor+" floor plan image does not exist or sensor mapping is not done. Please upload image(s) and finish sensor mapping."

#CHANGED
def map_data_tvoc(dataframe,fl,co_df):
    '''
    Get data needed to make tvoc floorplan (tvoc values, sensor locations, and their coordinate on floormap).
    Parameters:
        dataframe (dataframe): Contains sensors' data.
        fl (string): Get data for this floor.
        co_df (dataframe): Contains sensor numbers and the coordinates on the floormap.
    Returns:
        co_df (dataframe): Data needed for tvoc floorplan.
    '''
    #get sensor numbers that are in the dataset and in this floor
    s_num=dataframe[dataframe['Floor']==fl]['Sensor Number'].unique()
    dd=dataframe['TVOC'].groupby(dataframe['Sensor Number']).mean()

    #find mean tvoc values of each sensor
    dd=pd.concat([dd],axis=1).reset_index()
    dd['Sensor Number']=dd['Sensor Number']

     #keep only sensors that are in this floor
    dd=dd[dd['Sensor Number'].isin(s_num)]    
    dd=dd.sort_values('Sensor Number')
    co_df=co_df[co_df['snsr_num'].isin(s_num)]
    co_df.rename(columns={'snsr_num':'Sensor Number'},inplace=True)

    #combine mean tvoc and sensor coordinate info
    co_df=pd.merge(left=co_df,right=dd,on="Sensor Number", how='left')   
    co_df['Type']=[0]*len(co_df) 

    #add location info 
    sens_loc=dataframe[['Sensor Number','Location']].drop_duplicates().sort_values('Sensor Number')   
    sens_loc=sens_loc[sens_loc['Sensor Number'].isin(s_num)]
    co_df=pd.merge(left=co_df,right=sens_loc,on="Sensor Number", how='left')
    # co_df['Location']=sens_loc['Location'].tolist()

    #Find within which threshold tvoc values fit for each sensor
    for i in range(len(co_df)):
        if co_df['TVOC'][i] <= 50:
            co_df['Type'][i]='Excellent'
        elif co_df['TVOC'][i] <= 100:
            co_df['Type'][i]='Good'
        elif co_df['TVOC'][i] <= 200:
            co_df['Type'][i]='Acceptable'
        elif co_df['TVOC'][i] <= 600:
            co_df['Type'][i]='Substandard'
        else:
            co_df['Type'][i]='Unacceptable' 
    return co_df

#CHANGED
def air_quality_co2_summary_(request,id):
    '''
    Make barplot taht shows mean co2 value for each location.
    Parameters:
        request ():request
        id (int): task id
    Returns:
        Specified figure.
    '''
    buildingId,wk_start,wk_end=get_vars(id)
    floor,occupied=get_fl_occupied(request)

    #get data and time period text
    time,data = get_occupied_iaq_data(buildingId,id,occupied)
    data['Date'] = data['TimeStamp'].dt.strftime('%Y-%m-%d')
    if not data.empty:

        #get text of data's date range, for hover
        dateRangeText = get_date_range_text(data)

        #filter by floor
        data=get_floor_iaq(data,floor)

        #find mean co2 values for each location
        co2_location = data['CO2'].groupby(data['Location']).mean()
        co2_location=pd.concat([co2_location],axis=1).reset_index()  

        #make figure
        hoverVarComb = []
        hovertemplate='Building Floor: '+str(floor)+'<br>Location: %{x}<br>Time Period: '+str(time)+dateRangeText+'<br>CO2 Concentration: %{y}<extra></extra>'
        fig = general_barplot(co2_location['Location'], np.rint(co2_location['CO2']).astype(int), 'Location', 'Carbon Dioxide Concentration', "%{y} ", hoverVarComb, hovertemplate,[], 'ppm',[],[],time,wk_start,wk_end)
        
        #add target line
        fig.add_hline(y=600,line_width=3,line_color='#9BCA3B') 
        fig = add_legend_text(fig,'Ideal Level')
        fig.data[-1]['line']['color']='#9BCA3B'
        fig.data[-1]['line']['dash']='solid'
        fig.update_layout(legend_traceorder="reversed")

        fig.update_yaxes(rangemode="tozero")
        config =config_setting('Air Quality - Carbon Dioxide - Summary')
        div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" data-target="#tahm_3"  >Guide on How to Read This Graph</h5><div id="tahm_3" ><p style="padding:15px;">The locations where measurements were recorded are labeled on the horizontal axis. The average carbon dioxide (CO2) concentration value for the selected location during the selected time period is labeled on the vertical axis.</p></div></div>'
        return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'')
    else:
        return "data doesn't exist"

#CHANGED
def air_quality_co2_location_(request,id):
    '''
    Make barplot that displays mean CO2 values for different days.
    Parameters:
        request (): request 
        id (int): #task id
    Returns:
        Specified figure.
    '''
    buildingId,wk_start,wk_end=get_vars(id)
    occupied=request.POST.get('occupied',None)
    floor,loc,space = get_fl_loc_per_var(request)

    #get data and time period text
    time,data = get_occupied_iaq_data(buildingId,id,occupied)
    data = check_floor_loc_per(floor,loc,space,data)

    #find mean co2 value for each date
    co2_date = data['CO2'].groupby(data.index).mean() #mean group by sensor number
    co2_date = pd.concat([co2_date],axis=1).reset_index()   
    hovertemplate = hovertemplate_days_barplot(floor,loc,space,time,'CO2 Concentration')   
    fig = general_barplot(co2_date['Date'], np.rint(co2_date['CO2']).astype(int), 'Date', 'Carbon Dioxide Concentration', "%{y} ", [], hovertemplate,[],'ppm',[],[],time,wk_start,wk_end)
    fig.update_yaxes(rangemode="tozero")
    
    #add target line
    fig.add_hline(y=600,line_width=3,line_color='#9BCA3B') 
    fig = add_legend_text(fig,'Ideal Level')
    fig.data[-1]['line']['color']='#9BCA3B'
    fig.data[-1]['line']['dash']='solid'
    fig.update_layout(legend_traceorder="reversed")
    
    config =config_setting('Air Quality - Carbon Dioxide - Location')
    div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" data-target="#tahm_3"  >Guide on How to Read This Graph</h5><div id="tahm_3" ><p style="padding:15px;">The locations where measurements were recorded are labeled on the horizontal axis. The average carbon dioxide (CO2) concentration value for the selected location during the selected time period is labeled on the vertical axis.</p></div></div>'
    return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'')

#CHANGED
def air_quality_co2_sensor_(request,id):
    '''
    Display over time CO2 values for specified sensor.
    Parameters:
        request ():request 
        id (int): task id
        occ_start (string): Time when occupancy starts.
        occ_end (string): Time when occupancy ends.
    Returns:
        Specified figure.
    '''
    task_entry = Task.objects.get(id=id)  
    occ_start=task_entry.weekday_occupied_start
    occ_end=task_entry.weekday_occupied_end
    buildingId = str(task_entry.building.id)
    sensor=request.POST.get('sensor',None)
    floor=request.POST.get('floor',None)

    #get data
    time,data = get_occupied_iaq_data(buildingId,id,"Entire Day")

    #get data of this sensor
    new=get_floor_sens_iaq(data,sensor)
    dataframe = new[new['Sensor Number']==sensor]

    #add column that states the time period of each row, to add to hover
    dataframe = add_time_period_col(dataframe,'',occ_start,occ_end)

    #this sensor's location
    sensor_loc = dataframe['Location'].unique()[0]

   #make figure
    hovertemplate='Building Floor: '+str(floor)+'<br>Sensor Number: '+str(sensor)+'<br>Location: '+sensor_loc+'<br>Time Period: '+dataframe['Time Period']+'<br>Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>CO2 Concentration: %{y}<extra></extra>'
    fig = general_graph_overtime(dataframe['TimeStamp'], np.around(dataframe['CO2'],0), 'Date', 'Carbon Dioxide Concentration', [], hovertemplate,ticksuffix='ppm')
    
    #add target line
    fig.add_hline(y=600,line_width=3,line_color='#9BCA3B') 
    fig = add_legend_text(fig,'Ideal Level')
    fig.data[-1]['line']['color']='#9BCA3B'
    fig.data[-1]['line']['dash']='solid'
    fig.update_layout(legend_traceorder="reversed")
    
    fig.update_yaxes(rangemode="tozero")
    config =config_setting('Air Quality - Carbon Dioxide - Sensor')
    div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" data-target="#tahm_3"  >Guide on How to Read This Graph</h5><div id="tahm_3" ><p style="padding:15px;">Time is labeled on the horizontal axis, and carbon dioxide (CO2) concentration are on the vertical axis. This figure represents the CO2 concentrations over time for the selected sensor.</p></div></div>'
    return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'')

#CHANGED
def air_quality_co2_floor_plan_(request,id):
    '''
    Graph floorplan containing sensors and their mean CO2 values.
    Parameters:
        request (): reques
        id (int): #task id
    Returns:
        Specified figure.
    '''
    cur_width=int(request.POST.get("width",None)) # user cur width
    buildingId,wk_start,wk_end=get_vars(id)
    floor,occupied=get_fl_occupied(request)

     #get data of the time period
    time,data = get_occupied_iaq_data(buildingId,id,occupied)

    #filter by floor
    dataframe=data[data['Floor']==floor]
    dataframe['Date'] = dataframe['TimeStamp'].dt.strftime('%Y-%m-%d')

    #get text of data's date range, for hover
    dateRangeText = get_date_range_text(dataframe) 

    #get image and variables needed for floorplan
    co_df,img,img_width,img_height,scale_factor,wk_start,wk_end=get_sensors_images(buildingId,id,floor,cur_width)
    if not co_df.empty:

         #find mean co2 values for each sensor
        co2_sensor_table =dataframe['CO2'].groupby(dataframe['Sensor Number']).mean()
        co2_sensor_table =pd.concat([co2_sensor_table],axis=1).reset_index()    
        co2_sensor_table['CO2'] = np.rint(co2_sensor_table['CO2']).astype(int)    

        #merge sensor coordinate data and co2 values, and keep only the ones common to both
        co_df2 = co_df.rename(columns={'snsr_num':'Sensor Number'})
        co_df2 = co_df2[co_df2['Sensor Number'].isin(co2_sensor_table['Sensor Number'].values)]
        s_df = pd.merge(co2_sensor_table,co_df2,on='Sensor Number',how='right') 

        #Find within which threshold co2 values fit for each sensor
        s_df['Level'] = [0]*len(s_df)
        for i in range(len(s_df)):
            if s_df['CO2'][i] <= 600:
                s_df['Level'][i]='Excellent'
            elif s_df['CO2'][i] <= 800:
                s_df['Level'][i]='Good'
            elif s_df['CO2'][i] <= 1100:
                s_df['Level'][i]='Acceptable'
            elif s_df['CO2'][i] <= 1400:
                s_df['Level'][i]='Substandard'
            else:
                s_df['Level'][i]='Unacceptable'

        #Add location info
        l_df = dataframe.copy()
        l_df = l_df.drop_duplicates('Sensor Number')
        l_df = l_df[['Sensor Number','Location']]
        s_df = pd.merge(s_df,l_df,on='Sensor Number',how='left')

        #make graph
        colorScale = [(0,'#2B68F1'),(.406,'#25CE27'),(.531,'#E7F43E'),(.719,'#FC2107'),(1,'#2F1543')]
        hovertemplate='Building Floor: '+str(floor)+'<br>Location: '+s_df['Location']+'<br>Time Period: '+time+dateRangeText+'<br>CO2 Concentration: '+s_df['CO2'].astype(str)+'ppm<br>Level: '+s_df['Level']+'<extra></extra>'
        ticktext = ['0ppm','600ppm (Excellent)','800ppm (Good)','1100ppm (Acceptable)','1400ppm (Substandard)','1600ppm (Unacceptable)']
        config =config_setting('Air Quality - Carbon Dioxide - Floormap')
        fig = general_floormap(s_df, img, img_width, img_height, scale_factor, 'CO2', 'Sensor Number', colorScale, [0,600,800,1100,1400,1600], ticktext, 'Mean CO2<br>Concentration', 600, 1300, [], hovertemplate, 0, 1700,400,'',time,wk_start,wk_end)
         
        #Add descriptive text under the graph
        text = 'Average CO2 values are displayed for '
        fig = add_xlabel_occupancy_text(fig,text,time,wk_start,wk_end)
        div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" data-target="#tahm_3"  >Guide on How to Read This Graph</h5><div id="tahm_3" ><p style="padding:15px;">The average carbon dioxide (CO2) concentration values that each sensor measured is overlaid on a floor plan. Green values represent lower average CO2 concentration values, while red values represent higher average CO2 concentration values. </p></div></div>'
        return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'')
    else:
        return "floor"+floor+" floor plan image does not exist or sensor mapping is not done. Please upload image(s) and finish sensor mapping."