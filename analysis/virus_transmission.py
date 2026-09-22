import io
from tasks.models import Task
from analysis.common import *
from analysis.air_quality import *
import pandas as pd

#CHANGED
def virus_transmission_summary_(request,id):
    '''
    Make barplots of virus transmission scores for each location.
    Parameters:
        request ():request
        id (int): task id
    Returns:
		Specified figure.
    '''
    buildingId,wk_start,wk_end=get_vars(id)
    floor=request.POST.get('floor',None)
    occupied=request.POST.get('occupied',None)  

    #get data  
    time,data = get_occupied_iaq_data(buildingId,id,occupied)
    data['Date'] = data['TimeStamp'].dt.strftime('%Y-%m-%d')
    df_tph1=get_virus_tph_data(occupied,buildingId,id)

    #get text of data's date range, for hover
    dateRangeText = get_date_range_text(data) 
    if not data.empty:
        #filter by floor
        data=get_floor_iaq(data,floor)

        #get sensors and the location of each sensor 
        sensor_numbers=data['Sensor Number'].unique()   
        sensor_numbers=np.sort(sensor_numbers)
        dloc=data[data['Sensor Number'].isin(sensor_numbers)]
        dloc = dloc.drop_duplicates('Sensor Number')
        dloc = dloc.sort_values(by=['Sensor Number'])
        dloc = dloc['Location'].values  

        #get virus scores by taking avearge of rh and co2 scores  
        RH_scores = get_RH_scores(df_tph1,sensor_numbers)
        co2_scores = get_CO2_scores(data,sensor_numbers)    
        scores=pd.merge(co2_scores, RH_scores, on="Rooms",how='left')
        scores['Score_mean'] =  scores[["Score_x", "Score_y"]].mean(axis=1)    
        virus_scores = scores['Score_mean'].values    
        table = pd.DataFrame(virus_scores,index=None,columns=["scores"])

        #add location info to scores and find average score of each location
        table['Location'] = dloc
        summary=table.groupby('Location').mean()
        summary=pd.concat([summary],axis=1).reset_index()
        summary = np.around(summary,2) 

        #make figure    
        hovertemplate='Building Floor: '+str(floor)+'<br>Location: %{x}<br>'+'Time Period: '+str(time)+dateRangeText+'<br>Virus Transmission Risk Prevention Score: %{y}<extra></extra>'
        fig = general_barplot(summary['Location'].values, summary['scores'].values, 'Location','Virus Transmission Risk Prevention Score', "%{y:.2f} ", [], hovertemplate, [0, 10.5], '', ["0 (More Risk)"," "," "," ","10 (Less Risk)"], [0,2.5,5,7.5,10],time,wk_start,wk_end)
        
        #add target line
        fig.add_trace(go.Scatter(x=summary['Location'].values,y=[10]*len(summary['Location']), mode='lines', line=dict(color='#9BCA3B', width=3), name = 'Target',yaxis='y2'))
        fig.update_layout(legend_traceorder="reversed") 

        config =config_setting('Virus Transmission - Risk of Virus Transmission - Summary')
        div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" data-target="#tahm_3"  >Guide on How to Read This Graph</h5><div id="tahm_3" ><p style="padding:15px;">The locations where measurements were recorded are labeled on the horizontal axis. The average calculated risk of virus transmission for the selected floor during the selected time period is labeled on the vertical axis.</p></div></div>'
        return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'')
    else:
        return render(request, 'partials/render.html', {"error":"data doesn't exist"})
#CHANGED
def virus_transmission_location_(request,id):
    '''
    Make barplots of average virus scores for different days.
    Parameters:
        request (): request
        id (int): task id
    Returns:
		Specified figure.
    '''
    buildingId,wk_start,wk_end=get_vars(id)   
    occupied=request.POST.get('occupied',None)    
    floor,loc,space = get_fl_loc_per_var(request)

    #get data and filter by floor, location, and space
    time,data = get_occupied_iaq_data(buildingId,id,occupied)
    data = check_floor_loc_per(floor,loc,space,data)
    df_tph1=get_virus_tph_data(occupied,buildingId,id)
    if not data.empty:
        sensor_numbers=data['Sensor Number'].unique()   
        sensor_numbers=np.sort(sensor_numbers)
        # data['Dates'] = data['TimeStamp'].dt.strftime("%b %d")
        dates = data.index.unique()
        # data_tph['Dates'] = data_tph.index.strftime("%b %d")
        average_virus_list = []
        dates_used = []
        for date in dates:
            dfi = data[data.index == date]
            dfi_tph = df_tph1[df_tph1['Date']==date]   
            if(len(dfi)==0 or len(dfi_tph)==0):
                continue

             #virus score is average of rh and co2 scores         
            RH_scores = get_RH_scores(dfi_tph,sensor_numbers)
            co2_scores = get_CO2_scores(dfi,sensor_numbers)
            #calculate virus trans score for this sensor
            scores=pd.merge(co2_scores, RH_scores, on="Rooms",how='left')       
            scores['Score_mean'] =  scores[["Score_x", "Score_y"]].mean(axis=1)
            virus_score = scores['Score_mean'].mean()
            average_virus_list.append(virus_score)  
            dates_used.append(date)  
        average_virus_list = np.asarray(average_virus_list)
        average_virus_list = np.around(average_virus_list,2)

        #make figure
        ticktext = ["0 (More Risk)"," "," "," ","10 (Less Risk)"]
        y_label = 'Virus Transmission Risk Prevention Score'
        hovertemplate = hovertemplate_days_barplot(floor,loc,space,time,y_label)
        fig = general_barplot(dates_used, average_virus_list, 'Date', y_label, "%{y:.2f}", [], hovertemplate, [0,10.5], '', ticktext, [0,2.5,5,7.5,10],time,wk_start,wk_end)
    
        #add target line
        fig.add_trace(go.Scatter(x=dates_used,y=[10]*len(dates_used), mode='lines', line=dict(color='#9BCA3B', width=3), name = 'Target',yaxis='y2'))
        fig.update_layout(legend_traceorder="reversed") 

        config =config_setting('Virus Transmission - Risk of Virus Transmission - Location')
        div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" data-target="#tahm_3"  >Guide on How to Read This Graph</h5><div id="tahm_3" ><p style="padding:15px;">The days during which measurements were recorded are labeled on the horizontal axis. The daily average calculated risk of virus transmission for the selected location and time period is labeled on the vertical axis.</p></div></div>'
        return generate_fig_to_div(request,fig,config,div_info,buildingId,id,'')
    else:
       return render(request, 'partials/render.html', {"error":"data doesn't exist"})

def get_virus_tph_data(occupied,buildingId,id):
    '''
    Get IEQ data used for virus transmission modules based on time period.
    Parameters:
        occupied (string): Time period.
        buildingId (int): building id
        id (int): task id
    Returns:
        data (dataframe): IEQ data for the specified time period.
    '''
    if occupied == "Entire Day":
        data = load_df(buildingId,id,"df_tph.csv")     
    elif occupied=="Occupied":
        data = load_df(buildingId,id,"df_tph_occ.csv")  
    else:
        data = load_df(buildingId,id,"df_tph_non_occ.csv")
    data=data.reset_index()
    data['TimeStamp'] =pd.to_datetime(data['TimeStamp'])     
    data['Floor']=data['Floor'].astype(str)
    data['Sensor Number']=data['Sensor Number'].astype(str)
    data=data.set_index('TimeStamp') 
    return data

def get_RH_scores(data_tph,sensor_numbers):
    '''
    Find relative humidity scores.
    Parameters:
        data_tph (dataframe): Data containing relative humidity values.
        sensor_numbers (list): Sensors to get score of.
    Returns:
        df_score_RH (dataframe): Contains sensor numbers and their rh score
    '''        
    rooms_IEQ=[]
    sensors_used = [] 
    for room in sensor_numbers: 
        dfi = data_tph[data_tph['Sensor Number']==room]
         #find mean rh by time
        RH_mean=dfi.groupby(dfi.index)['Humidity'].mean() #group this floor's sensors' humidity, take mean
        RH_mean=pd.concat([RH_mean],axis=1).reset_index()       
        rooms_IEQ.append(RH_mean)
        sensors_used.append(room)
    output_RH = pd.DataFrame()
    for room, dfi in zip(sensors_used, rooms_IEQ):
        if(len(dfi)==0):
         continue
        # dfii = upsample_iterpolate1(dfi, sampling_time_minute)
        sizes = relativehumidity_levels(dfi, "Humidity", room)
        output_RH[room] = sizes 
    #find portion of time rh is in each level and add it to dictionary
    RELATIVEHUMIDITY_WEIGHTS= [x for x, y in zip([0,3,5,8,10], [1,1,1,1,1]) if y == True]
    output_RH=pd.concat([output_RH],axis=1).reset_index()
    df_score_RH = calc_scores(output_RH, RELATIVEHUMIDITY_WEIGHTS)
    return df_score_RH

def relativehumidity_levels(dataframe, column, roomname):
    '''
    Determines the portion of time of each level for CO2 above ambient thresholds 
            Parameters:
                    dataframe (df): main dataframe of CO2 values
                    column (str): column name of interest
                    listofrooms (list): list of rooms for print statements
            Returns:
    '''
  
    LEVEL_0 = 60
    LEVEL_1 = 40
    LEVEL_2 = 30
    LEVEL_3 = 20
    LEVEL_4 = 70
    LEVEL_5 = 75
    LEVEL_6 = 80
    LEVEL_7 = 10
    portion_time_0 = dataframe[(dataframe[column] <= LEVEL_0) & (dataframe[column] >= LEVEL_1) ].shape[0] /dataframe.shape[0]
    portion_time_1 = dataframe[(dataframe[column] >= LEVEL_2) & (dataframe[column] < LEVEL_1)].shape[0] / dataframe.shape[0] + dataframe[((dataframe[column] <= LEVEL_4) & (dataframe[column] > LEVEL_0))].shape[0] / dataframe.shape[0]
    portion_time_2 = dataframe[((dataframe[column] >= LEVEL_3) & (dataframe[column] < LEVEL_2) ) ].shape[0] / dataframe.shape[0] +   dataframe[((dataframe[column] > LEVEL_4) & (dataframe[column] <= LEVEL_5) ) ].shape[0] / dataframe.shape[0]
    portion_time_3 = dataframe[((dataframe[column] >= LEVEL_7) & (dataframe[column] < LEVEL_3) )].shape[0] / dataframe.shape[0]  + dataframe[((dataframe[column] > LEVEL_5) & (dataframe[column] <= LEVEL_6) ) ].shape[0] / dataframe.shape[0]
    portion_time_4 = dataframe[(dataframe[column] < LEVEL_7)].shape[0] / dataframe.shape[0] + dataframe[(dataframe[column] > LEVEL_6)].shape[0] / dataframe.shape[0]
    portions = [portion_time_4, portion_time_3, portion_time_2, portion_time_1, portion_time_0]
    return portions

def relative_humidity_Analysis(Rooms_dict):
    '''
    Finds percentage of time each room spends in each relative humidity levels.
    Paramters:
        Rooms_dict (dict): Contains sensor numbers and their data.
    Returns:
        output (dict): Contains sensor numbers and the portions of time.
    ''' 
    output = pd.DataFrame()
    output['Ranges'] = ["Unacceptable", "Substandard", "Acceptable", "Good", "Excellent"]    
    for room, dfi in Rooms_dict.items():
        sizes = relativehumidity_levels(dfi, "Humidity", room)
        output[room] = sizes
    return output

def calc_scores(df_output, scoring_weights):
    '''
    Calculates the scores based on the portion of time in each threshold range
    and associated weight.
    Parameters
    ----------
    df_output : DataFrame
        Dataframe of the portion of time spent in each range for the
        corresponding rooms.
    scoring_weights : list
        Weights for the thresholds of specific module.
    Returns
    -------
    df_out : DataFrame
        Corresponding scores for each of the rooms.
    '''
    df_out = pd.DataFrame()

    rooms_list = df_output.columns.values.tolist()[1:]
    #Takes the sum product of the weights list and portions from the output file of TVOC for each row
    scores = [sum_product(scoring_weights, list(df_output[room].values)) for room in rooms_list]
    df_out['Rooms'] = rooms_list
    df_out['Score'] = scores
    return df_out

def sum_product(list1, list2):
    '''Return the sum product of two lists'''
    score = sum([x * y for x, y in zip(list1, list2)])
    return score
    
#returns co2 scores for sensors
def get_CO2_scores(df,sensor_numbers):
    '''
    Find co2 scores for the specified sensors.
    Parameters:
        df (dataframe): Data containing co2 values.
        sensor_numbers (list): Sensors to get score of.
    Returns:
        df_score_virusCO2 (dataframe): Contains sensor numbers and their co2 score.
    '''  
    #make a dict of data
    Room_subset=sensor_numbers
    rooms_IEQ=[]
    for room in Room_subset:
        dfi = df[df['Sensor Number']==room]
        rooms_IEQ.append(dfi)
    Rooms_dict_CO2_master = []
    Rooms_dict_CO2_diff = []
    Rooms_dict_CO2_diff_clip = []

     #take rolling mean of co2 difference
    for room, dfi in zip(Room_subset,rooms_IEQ):
            dfi["Outdoor_Air"]=[400]*len(dfi)
            df_return = pd.DataFrame()
            df_return["CO2_diff"] = dfi['CO2'] - dfi['Outdoor_Air']
            Rooms_dict_CO2_master.append(dfi)
            Rooms_dict_CO2_diff.append(df_return)
            Rooms_dict_CO2_diff_clip.append(df_return.clip(lower=0))   
    rolling_num_CO2 = 10
    Rooms_CO2aboveambient = []
    
    for room, dfi in zip(Room_subset, Rooms_dict_CO2_diff_clip):
        dfi=dfi.reset_index()
        dfi['time'] = pd.to_datetime(dfi.index)#.dt.strftime('%H')
        dfi['time'] = dfi['time'].dt.strftime('%H')
        df_add = pd.DataFrame()
        df_add['CO2_Diff'] = dfi['CO2_diff'].rolling(rolling_num_CO2).mean()
        df_add = df_add.iloc[rolling_num_CO2-1:]
        df_add['time'] = dfi["time"]
        Rooms_CO2aboveambient.append(df_add)

    #find percent of time co2 diff is at each level
    output_virusCO2 = Virus_CO2_analysis(Room_subset,Rooms_CO2aboveambient)
    CO2ABOVEAMBIENT_WEIGHTS= [x for x, y in zip([0,3,5,7,10], [1,1,1,1,1]) if y == True]
    df_score_virusCO2 = calc_scores(output_virusCO2, CO2ABOVEAMBIENT_WEIGHTS)    
    return df_score_virusCO2

def Virus_CO2_analysis(rooms,data):
    '''
    Find portion of time above ambient co2 spends in each level.
    Parameters:
        rooms (list): List of sensors.
        data (list): List of dataframe, each corresponding to a sensor in rooms list in the same order.
    Returns:
        output (dict): Contains sensor numbers and the portion they spend in each level.
    '''
    levels = ["Unacceptable", "Substandard", "Acceptable", "Good", "Excellent"]    
    output = pd.DataFrame()
    output['Ranges'] = levels
    for room, dfi in zip(rooms,data):
        if len(dfi)==0:
            continue
        sizes = above_ambient_CO2_levels(dfi, "CO2_Diff", room)
        output[room] = sizes 
    return output

def above_ambient_CO2_levels(dataframe, column, roomname):
    '''
    Determines the portion of time of each level for CO2 above ambient thresholds 
            Parameters:
                    dataframe (df): main dataframe of CO2 values
                    column (str): column name of interest
                    listofrooms (list): list of rooms for print statements
            Returns:
    '''
    
    LEVEL_0 = 200 #0.5% rebreathed air fraction
    LEVEL_1 = 400 #Ref. 5.21
    LEVEL_2 = 700 #Ref.  AHSRAE 6.21
    LEVEL_3 = 1000 #Ref. 5.25, 5.26, 5.27
    #Level 0 is the best case scenario and Level 4 is the worst 
    # if len(dataframe)==0:
    #     return [0,0,0,0,0]
    
    portion_time_0 = dataframe[dataframe[column] <= LEVEL_0].shape[0] / dataframe.shape[0]
    portion_time_1 = dataframe[(dataframe[column] <= LEVEL_1) & (dataframe[column] > LEVEL_0) ].shape[0] / dataframe.shape[0]
    portion_time_2 = dataframe[(dataframe[column] <= LEVEL_2) & (dataframe[column] > LEVEL_1) ].shape[0] / dataframe.shape[0]
    portion_time_3= dataframe[(dataframe[column] <= LEVEL_3) & (dataframe[column] > LEVEL_2) ].shape[0] / dataframe.shape[0]
    portion_time_4 = dataframe[(dataframe[column] >  LEVEL_3) ].shape[0] /dataframe.shape[0]
 
    #Listed from worst to best 
    portions = [portion_time_4, portion_time_3, portion_time_2, portion_time_1, portion_time_0]

    return portions   
