from pickle import NONE
from tasks.models import Task
from analysis.common import *
from analysis.data_analysis_library import *
from placements.models import SensorPlacement
import pandas as pd

import matplotlib.pyplot as plt
import datetime
from datetime import timedelta  
import numpy as np
import json
import plotly.graph_objects as go
from io import StringIO
from sklearn.metrics import mean_squared_error
# import keras
from scipy.optimize import curve_fit
from analysis.pythermalcomfort_needed import *





# gobal variable
default_stable_rise = 70
max_setpoint_change = 10

# graphic function ########################################################################


def get_color(i):
    '''
    Associate a     color with i and return it.
    Parameters:
        i (int): Number based on which a color is returned.
    Returns:
        A color
    '''
    BRAND_PALLET = ['#065BA7', '#9BCA3B', '#56B4E9','#C11771', '#000000','#beabea',
                '#8E2100' , '#F0E442','#E288A0', '#A51E55', "#47B489", "#EF5A45","#bc7b48","#7a34d7", "#504713", "#7b6381"]
    i = i%(len(BRAND_PALLET)-1)    
    return BRAND_PALLET[i]

def get_color_black_white(i):
    '''
    If i is even, return the color black, otherwise return white.
    Parameters:
        i (int): Number based on which the color is returned.
    Returns:
        Black or white color.
    '''
    colors = ['#000000', '#ffffff']
    return colors[i%2]



# ###################################################################################
# other function

def get_between_dates(data,start_date,end_date):
    '''
    Gets portion of data that's between the given date and time.
    Parameters:
        data (dataframe): Data.
        start_date (string): Filter data to start from this date and time. Format: 2021-01-01 08:00
        end_date (string): Filter data to end at this date and time. Format: 2021-01-01 08:00
    Returns:
        data (dataframe): Filtered data.
    '''
    data = data[(data['TimeStamp']<=pd.to_datetime(end_date)) & (data['TimeStamp']>=pd.to_datetime(start_date))]
    return data




def get_time_difference(start,end):
    '''
    Find time difference between the two given times.
    Parameters:
        start (string): Start time, format: 08:00
        end (string): End time, format: 17:00
    Returns:
        diff (float): Time difference in hours.
    '''
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    diff = end-start
    diff = diff.seconds/3600
    return diff



def get_data_between_time(data,start,end,include=True):
    '''
    Get portion of data that's between the given times.
    Parameters:
        data (dataframe): Data.
        start (string): The smallest time the data should have, format: 08:00
        end (string): The largest time the data should have, format: 20:00
        include (boolean): Whether to be inclusive of the start and end.
    Returns:
        data (dataframe): Filtered data
    '''
    data.index = data['TimeStamp']
    if(include==True):
        data = data.between_time(start,end,include_start=True,include_end=True)
    else:
        data = data.between_time(start,end)
    return data 


def reject_outliers(data, m=2):
    '''
    Rejects outliers and removes their corresponding time in the time list.
    Parameters:
        data (array): List of values to reject outliers of.
        m (float): How different values can be before they are classified as outliers.
    Returns: 
        Data with outliers removed.
    '''
    if(len(data)<=2):
        return data
    data = np.array(data)
    return data[abs(data - np.mean(data)) < m * np.std(data)]

def get_data_days(data,days=['Mon','Tue','Wed','Thu','Fri']):
    '''
    Get portion of data that correspond to given week days.
    Parameters:
        data (dataframe): Data.
        days (list): Contains days to include in the data.
    Returns:
        data (dataframe): Filtered data.
        removed_dates (list): List of dates that were removed.
    '''
    dates_before = data['Date'].unique()
    data['Day'] = data['TimeStamp'].dt.strftime("%a")
    removed_dates=None
    data = data[data['Day'].isin(days)]
    dates_after = data['Date'].unique()
    removed_dates = [str(d) for d in dates_before if d not in dates_after]
    return data,removed_dates

def get_poly_y(x,popt):
    '''
    Compute y values based on given x and polynomial coefficients.
    Parameters:
        x (list): List of values to feed into polynomial function.
        popt (list): List of polynomial coefficient (order is auto determined based on popt's size).
    Returns:
        y (list): Computed y values.
    '''
    popt = list(reversed(popt))
    y = [0]*len(x)
    for i in range(len(popt)): #add each polynomial component one at a time
        y = y + np.multiply(np.power(x,i),popt[i])
    return y

#------------------------------------------------------------------------------

def get_stable_temp_data(data,sp_start,sp_end):
        '''
        Gets portion of data of that starts from when temperature has changed enough 
        after setpoint started, until the end of setpoint time.
        Parameters: 
            data (dataframe): Data of one sensor.
            sp_start (string): Time when the setpoint is turned on (format 09:00).
            sp_end (string): Time when the setpoint is turned off (format 17:00).
        Returns:
            df_stable (dataframe): Stable portion of data
        '''
        data = get_data_between_time(data,sp_start,sp_end)

        #get stable data of each date
        dates = data['Date'].unique()
        df_stable = pd.DataFrame()
        for date in dates: 
            start_row,end_row,time_taken,dfi = get_start_stable_rows(data,date,sp_start,sp_end)
            if(len(dfi)==0):
                continue
            df_stable = df_stable.append(dfi)

        return df_stable


def get_stable_temp(data,sensor,sp_start,sp_end):
    '''
    Gets average temperature of a sensor after temp has changed enough, until occupied end.
    Parameters:
        data (dataframe): Data.
        sensor (string): Use this sensor.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
    Returns:
        avg_list (list): Contains average stable temperature for each date in dates_used.
        dates_used (list): Dates for which average stable temperature was found.
    '''

    data = data[data['Sensor Number']==sensor]
    
    #get average stable temp for each day
    dates = data['Date'].unique()
    avg_list = []
    dates_used = []
    for date in dates:
        start_row,stable_row,time_taken,df_stable = get_start_stable_rows(data,date,sp_start,sp_end)
        if(len(df_stable)==0):
            continue
        avg_temp = df_stable['Temperature'].mean()
        avg_list.append(avg_temp)
        dates_used.append(date)
    return avg_list,dates_used


def remove_partial_dates(data,sp_start,sp_end):
    '''
    Removes the start and/or end date if they don't contain data of the entire setpoint duration.
    Parameters:
        data (dataframe): Data.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
    Returns:
        data (dataframe): Filtered data.
    '''

    if(len(data)==0):
        return data
    data.index = data['TimeStamp']
    data= data.sort_index()
    
    #find the time data starts at
    first_row = data.iloc[0]
    first_date = first_row['Date']
    time_start = first_row['TimeStamp'].strftime('%H:%M')

    #remove this date if data starts later than setpoint start time
    if(time_start>sp_start):
        data = data[data['Date']!=first_date]

    if(len(data)==0):
        return data

    #find the time data ends at
    last_row = data.iloc[-1]
    last_date = last_row['Date']
    time_end = last_row['TimeStamp'].strftime('%H:%M')

    #remove this date if data ends sooner than setpoint start time
    if(time_end<sp_end):
        data = data[data['Date']!=last_date]
    
    return data

def get_start_stable_rows_mode(data,date,sp_start,sp_end,mode='Heating'):
    '''
    Get row when the temperature has changed enough and related data for the specified mode.
    Parameters:
        data (dataframe): Data of one sensor.
        date (string): Get data of this date.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
        mode (string): Which mode to get data for (Heating or Cooling).
    Returns:
        start_row (series): The first row of data after setpoint starts.
        stable_row (series): The first row of data after temp has changed enough.
        time_taken (float): Time taken for temp to change enough (in hours).
        df_stable (dataframe): Data starting from when temp has changed enough until end of setpoint time.
    '''
    df = data[data['Date']==date]
    df = get_data_between_time(df,sp_start,sp_end)
    if(len(df)<=1):
        return [],[],0,[]
    df.index = df['TimeStamp']
    df = df.sort_index()
    start_row = df.iloc[0]
    df2 = df[1:] #so we don't get the start row as stable row

    if(mode=='Heating'):
        perc = default_stable_rise #For heating, temp has to rise to 70% of max
    else:
        perc = 100-default_stable_rise #For cooling, temp has to drop to 30% of max

    #high (or low) enough temperature based on temperature values
    stable_temp1 = df2['Temperature'].min() + (df2['Temperature'].max()-df2['Temperature'].min())*perc/100

    #high (or low) enough temperature based on percentile
    stable_temp2 = np.percentile(df2['Temperature'],perc)
    
    if(mode=='Heating'):
        stable_row1 = df2[df2['Temperature']>=stable_temp1].iloc[0]#first high enough temp
        stable_row2 = df2[df2['Temperature']>=stable_temp2].iloc[0]#first high enough temp
    else:
        stable_row1 = df2[df2['Temperature']<=stable_temp1].iloc[0]#first low enough temp
        stable_row2 = df2[df2['Temperature']<=stable_temp2].iloc[0]#first low enough temp

    if(stable_row1['TimeStamp']<=stable_row2['TimeStamp']):#choose the sooner one
        stable_row = stable_row1
    else:
        stable_row = stable_row2

    time_taken = stable_row['TimeStamp']-start_row['TimeStamp']
    time_taken = time_taken.seconds/3600

    if(time_taken==0):
        return [],[],0,[]

    df_stable = df[df['TimeStamp']>=stable_row['TimeStamp']]

    return start_row,stable_row,time_taken,df_stable
def get_start_stable_rows(data,date,sp_start,sp_end):
    '''
    Get row when the temperature has changed enough and related data (heating or cooling mode auto determined).
    Parameters:
        data (dataframe): Data of one sensor.
        date (string): Get data of this date.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
    Returns:
        start_row (series): The first row of data after setpoint starts.
        stable_row (series): The first row of data after temp has changed enough.
        time_taken (float): Time taken for temp to change enough (in hours).
        df_stable (dataframe): Data starting from when temp has changed enough until end of setpoint time.
    '''

    df = data[data['Date']==date]
    df = get_data_between_time(df,sp_start,sp_end)
    if(len(df)<=1):
        return [],[],0,[]
    df.index = df['TimeStamp']
    df = df.sort_index()
    start_row = df.iloc[0]
    df2 = df[1:]


    #find warm temp
    warm_temp1 = df2['Temperature'].min() + (df2['Temperature'].max()-df2['Temperature'].min())*default_stable_rise/100
    warm_temp2 = np.percentile(df2['Temperature'],default_stable_rise)

    warm_row1 = df2[df2['Temperature']>=warm_temp1].iloc[0]#first high enough temp
    warm_row2 = df2[df2['Temperature']>=warm_temp2].iloc[0]#first high enough temp


    if(warm_row1['TimeStamp']<=warm_row2['TimeStamp']):#choose the sooner one
        warm_row = warm_row1
    else:
        warm_row = warm_row2


    #find cool temp
    cool_temp1 = df2['Temperature'].min() + (df2['Temperature'].max()-df2['Temperature'].min())*(100-default_stable_rise)/100
    cool_temp2 = np.percentile(df2['Temperature'],100-default_stable_rise)

    cool_row1 = df2[df2['Temperature']<=cool_temp1].iloc[0]#first low enough temp
    cool_row2 = df2[df2['Temperature']<=cool_temp2].iloc[0]#first low enough temp

    if(cool_row1['TimeStamp']<=cool_row2['TimeStamp']):#choose the sooner one
        cool_row = cool_row1
    else:
        cool_row = cool_row2


    #detect if warming up or cooling down (whichever's percentile is reached later)
    if(warm_row2['TimeStamp']>cool_row2['TimeStamp']): #warming up
        stable_row = warm_row
    else: #cooling down
        stable_row = cool_row

    time_taken = stable_row['TimeStamp']-start_row['TimeStamp']
    time_taken = time_taken.seconds/3600

    if(time_taken==0):
        return [],[],0,[]
    df_stable = df[df['TimeStamp']>=stable_row['TimeStamp']]
    return start_row,stable_row,time_taken,df_stable
#pmv --------------------------------------------------
##cloth level calculated based on outside temperature at 6:00 am
def clo_level(T):
    #T : outside temperature at 6:00 a.m.
    
    if T<=-5:
        clo=1.0
    elif (T>-5 and T<=5):
        clo = round((-0.0375*T) + 0.8125,2)
    elif (T>5 and T<=26):    
        clo = round((-0.0083*T) + 0.666,2)
    else:
        clo=0.45
    return clo


def opt_temp_pmv(data,p1,p2,v=0.1,act='Typing'):
    if 'Temperature_Outside' not in data:
        print('Need outside temperature to find comfort range using PMV, using default values of 20-24°C.')
        return 20,24
    #data=Whole building or location data frame that we are checking the comfort level
    #p1=lowest pmv value considered as comfortable
    #p2=highest pmv value considered as comfortable
    #v = 0.1 air speed
    #act = primary act of the place. print(met_typical_tasks) shows all the different type of act that we can use
    
    rh = data['Humidity'].mean()
    met=met_typical_tasks[act]#metabolic rate based on act
    ####outside temperature at 6:00 am #####
    o_t=data[data['Time_of_day']=='06:00:00']['Temperature_Outside'].mean()
    icl=clo_level(o_t)###cloth level
    vr=v_relative(v=v, met=met)##relative air speed
    
    results=[]
    temp=np.arange(15,35,0.1) #temperature from 15-35C
    ##pmv values for eavh temperature
    for i in temp :
        tdb=round(i,2)
        
        out=pmv_ppd(tdb=tdb,tr=tdb,vr=vr, rh=rh, met=met, clo=icl, standard='ASHRAE')
        results.append(out['pmv'])

    low=round(temp[min(range(len(results)), key=lambda i: abs(results[i]-p1))],2) #minimum comfortable temperature
    high=round(temp[min(range(len(results)), key=lambda i: abs(results[i]-p2))],2) #maximum comfortable temperature
    #warnings.filterwarnings("ignore")
    #warnings.simplefilter("ignore")
    return low,high


#to check pmv values for these temperature we can use this function
def check_pmv(data,t,v=0.1,act='Typing'):
    #data: data frame
	#t: temperature
	
    rh = data['Humidity'].mean()
    met=met_typical_tasks[act]#metabolic rate based on act
    
    ####outside temperature at 6:00 am #####
    o_t=data[data['Time_of_day']=='06:00:00']['Temperature_Outside'].mean()
    icl=clo_level(o_t)###cloth level
    vr=v_relative(v=v, met=met)##relative air speed
    result=pmv_ppd(tdb=t,tr=t,vr=vr, rh=rh, met=met, clo=icl, standard='ASHRAE')
    return result

#setpoint main ###############################################################################
def find_best_setpoint(df,df_full,sp_curr,sp_start,sp_end,comf_temp_min,comf_temp_max):
    '''
    Finds the setpoint change amount that results in the highest comfort percentage.
    Parameters:
        df (dataframe): Contains controllable sensors' data.
        sp_curr (float): Current setpoint temperature.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
        comf_temp_min (float): Min temperature considered comfortable.
        comf_temp_max (float): Max temperature considered comfortable.
    Returns:
        setpoint_change (float): How much (in °C) the setpoint should be changed.
    '''
    setpoint_range = np.arange(-max_setpoint_change,max_setpoint_change,.25) #setpoint range to test and compare
    score_list = find_scores(df, df_full,sp_curr,sp_start,sp_end,comf_temp_min,comf_temp_max,setpoint_range) #score setpoints
    setpoint_index = np.argmax(score_list)
    #setpoint_index = evaluate_setpoints(score_list) #find index of best one
    setpoint_change = setpoint_range[setpoint_index]
    return setpoint_change


def get_setpoint_data(data,sp_start,sp_end):
    '''
    Gets portion of data that needs to be optimized (starting from when 
    temperature has changed enough until end of setpoint time).
    Parameters:
        data (dataframe): Data.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
    Returns:
        df_new (dataframe): Relevant portion of the data.
    '''
    sensors = data['Sensor Number'].unique()
    df_new = pd.DataFrame()
    for sensor in sensors: 
        dfi = data[data['Sensor Number']==sensor]
        dfi = get_stable_temp_data(dfi,sp_start,sp_end)
        df_new = df_new.append(dfi)

    return df_new

# sepoint loss method
def find_scores(df, df_full,sp_curr,sp_start,sp_end,comf_temp_min,comf_temp_max,loopRange, extra_shift=0):
    '''
    Find scores for setpoint change values in the given list.
    Parameters:
        df (dataframe): Contains sensors' data.
        sp_curr (float): Current setpoint temperature.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
        comf_temp_min (float): Min temperature considered comfortable.
        comf_temp_max (float): Max temperature considered comfortable.
        loopRange (list): Contains the setpoint change values to evaluate.
        extra_shift (float): Value to add to loopRange when shifting temperatures.
    Returns:
        score_list (list): List of scores for each value in loopRange.
    '''
    score_list = []
    
    for i in loopRange: #go through setpoints
        dfi = shift(df,df_full,sp_curr,sp_start,sp_end,i+extra_shift) #change temperatures based on this setpoint
        score_i = score_values_outside(dfi,comf_temp_min,comf_temp_max) #find score
        score_list.append(score_i) #add the score for this setpoint to the list
    return score_list

def score_values_outside(df,comf_temp_min,comf_temp_max):
    '''
    Gives a score to this data based on the number of temperatures outside the comfort range.
    Parameters:
        df (dataframe): Data.
        comf_temp_min (float): Min temperature considered comfortable.
        comf_temp_max (float): Max temperature considered comfortable.
    '''
    uncomfortable_data = df[(df['Temperature_shifted'] < comf_temp_min) | (df['Temperature_shifted'] >comf_temp_max)]
    #score_i = -uncomfortable_data.count()[0]
    score_i = -len(uncomfortable_data)

    return score_i

#this method was made after the alg's code was finished, and is not tested yet.
def score_closeness(df,comf_temp_min,comf_temp_max):
    '''
    Finds a score based on how many values are inside the comfort range, and how close the values outside
    the comfort range are to it.
    '''
    score = 0
    for row in df.iterrows():
        if(row['Temperature']>= comf_temp_min and row['Temperature'] <= comf_temp_max):#in comfort range
            score = score+1
        elif(row['Temperature']==0):
            score = 0
        elif(row['Temperature']>comf_temp_max): #based on how close it is, when above max comf temp
            score = (comf_temp_max)/(row['Temperature']+.001) #.001 to avoid 0 division
        elif(row['Temperature']<comf_temp_min): #based on how close it is, when below min comf temp
            score = (row['Temperature'])/(comf_temp_min+.001)

#sepoint change effect ###########################################
def shift(df,df_full,sp_curr,sp_start,sp_end,change):
    '''
    Changes temperatures based on the amount setpoint is changed and its estimated effect.
    Parameters: 
        df (dataframe): Data.
        sp_curr (float): Current setpoint temperature.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
        change (float): How much setpoint is changed by.
    Returns:
        df_new (dataframe): Data with shifted temperatures.
    '''
    sensors = df['Sensor Number'].unique()
    df_new = pd.DataFrame()
    for sensor in sensors:
        dfi = df[df['Sensor Number']==sensor]
        dfi_full = df_full[df_full['Sensor Number']==sensor] 
        conformance = sensor_conformance(dfi_full,sensor,sp_curr,sp_start,sp_end)
        if(conformance==-1): #if not found, set it to a default
            conformance = 1
        dfi['Temperature_shifted'] = dfi['Temperature']+change*conformance #change temp based on conformance
        dfi['Temperature_shifted'] = np.round(dfi['Temperature_shifted'],2)
        df_new = df_new.append(dfi)
    return df_new


# combine controllability ########################################################################################
def fit_poly_date_compare(data,date,sp_start,sp_end):
    '''
    Finds the fit error difference of line and parabola fit.
    Parameters:
        data (dataframe): A sensor's data.
        date (string): Date to use.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
    Returns:
        error (float): Fit error difference.
    '''
    data = data[data['Date']==date]
    data = get_data_between_time(data,sp_start,sp_end)
    if(len(data)<=1):
        return -1
    
    data.index = data['TimeStamp']
    data = data.sort_index()
    data = data.reset_index(drop=True)

    #error from fitting to line
    popt = np.polyfit(data.index,data['Temperature'],1)
    temp_pred = get_poly_y(data.index,popt)
    error_1 = mean_squared_error(data['Temperature'],temp_pred,squared=False)
    #graph_quick3(data.index,data['Temperature'],data.index,temp_pred)

    #error from fitting to parabola
    popt = np.polyfit(data.index,data['Temperature'],2)
    temp_pred = get_poly_y(data.index,popt)
    error_2 = mean_squared_error(data['Temperature'],temp_pred,squared=False)
    #graph_quick3(data.index,data['Temperature'],data.index,temp_pred)
    return error_1-error_2 #higher is better for controllability

def sensor_conformance(data,sensor,sp_curr,sp_start,sp_end):
    '''
    How close sensor gets to setpoint after stabilizing (avg temperature after rise up until occupied end, over setpoint).
    Parameters:
        data (dataframe): A sensor's data.
        sensor (string): Sensor number.
        sp_curr (float): Current setpoint temperature.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
    Returns:
        conformance (float): How close sensors gets to setpoint (percentage).
    '''
    avg_list,_ = get_stable_temp(data,sensor,sp_start,sp_end)
    if(len(avg_list)==0):
        return -1
    avg = np.mean(avg_list)
    return avg/sp_curr


def comb_control_sensor(data,sensor,sp_curr,sp_start,sp_end):
    '''
    Finds controllability mertics and the state of sensor's controllability.
    Parameters:
        data (dataframe): Data.
        sensor (string): Sensor number.
        sp_curr (float): Current setpoint temperature.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
    Returns:
        df_ctrl_sensor (dataframe): Contains sensor's controllability info.
    '''
    actual_action=""
    should_action=""
    stable_row=""
    df = data[data['Sensor Number']==sensor]
    df = remove_partial_dates(df,sp_start,sp_end)

    dates = data['Date'].unique()
    df_ctrl_sensor = pd.DataFrame(columns=['Date','Resp','Resp Val','Self Resp Val','Conf','Fit Error','Actual Action','Should Action','Action'])
    for date in dates:
        dfi = df[df['Date']==date]

        #find start and stable rows
        start_row,cool_row, time_taken1,df_stable1 = get_start_stable_rows_mode(dfi,date,sp_start,sp_end,'Cooling')
        start_row,warm_row, time_taken2,df_stable2 = get_start_stable_rows_mode(dfi,date,sp_start,sp_end,'Heating')
        if(len(start_row)>0):
        
             #start_row["Temperature"] =start_row["Temperature"].astype(float)
            if(time_taken1==0 or time_taken2==0):
                continue
            if((sp_curr-start_row['Temperature'])>.2): #need to warmup
                should_action = 'warmup'
            elif((sp_curr-start_row['Temperature'])<-.2): #need to cooldown
                should_action = 'cooldown'
            else:
                should_action = 'neutral'
       
            if(warm_row['TimeStamp']>cool_row['TimeStamp']): #actually warming up
                stable_row = warm_row #row where stable temperature starts
                actual_action = 'warmup'
                time_taken = stable_row['TimeStamp']-start_row['TimeStamp']

            else: #actually cooling down
                stable_row = cool_row
                actual_action = 'cooldown'
                time_taken = stable_row['TimeStamp']-start_row['TimeStamp']

        #compare the should and actual actions
            if(actual_action==should_action):
                action = 'correct'
            elif(should_action=='neutral'):
                action = 'neutral'
            else:
                action = 'wrong'

            temp_change_actual = stable_row['Temperature']-start_row['Temperature']
            temp_change_expected = sp_curr - start_row['Temperature']
            
            #find responsiveness metrics
            resp = temp_change_actual/temp_change_expected #positive=>needed to cool and did, or needed to heat and did. negative=>did opposite to what was supposed to do
            resp_val = temp_change_expected - temp_change_actual  #near zero is good. positive=>actual smaller than expected. negative=>actual larger than expected
            self_resp_val = stable_row['Temperature'] - start_row['Temperature'] #positive=>heating,negative=>cooling
            
            #find conformance value
            dfi_sp = get_data_between_time(dfi,sp_start,sp_end)
            df_stable = dfi_sp[dfi_sp['TimeStamp']>=stable_row['TimeStamp']]
            avg_temp = df_stable['Temperature'].mean()
            #conf = avg_temp/sp_curr
            conf = avg_temp-sp_curr #positive: above setpoint, negative: below setpoint

            #find lline and parabola fit error difference
            fit_error = fit_poly_date_compare(dfi,date,sp_start,sp_end)

            #add the metrics to the dataframe
            df_ctrl_sensor.loc[len(df_ctrl_sensor)] = [date,resp,resp_val,self_resp_val,conf,fit_error,actual_action,should_action,action]
    

    #determine which days have heating control 
    df_ctrl_sensor['Heating Control'] = 0 #unknown
    df_ctrl_sensor.loc[(df_ctrl_sensor['Self Resp Val']>.8) | ((df_ctrl_sensor['Self Resp Val']>0.6) & (-1<df_ctrl_sensor['Conf'])),'Heating Control'] = 1 #good
    df_ctrl_sensor.loc[(df_ctrl_sensor['Self Resp Val']<0.4) & (df_ctrl_sensor['Conf']<-1) & (df_ctrl_sensor['Should Action']=='warmup'),'Heating Control'] =-1

    #determine which days have cooling control 
    df_ctrl_sensor['Cooling Control'] = 0 #unknown
    df_ctrl_sensor.loc[(df_ctrl_sensor['Self Resp Val']<-.8) | ((df_ctrl_sensor['Self Resp Val']<-0.6) & (1>df_ctrl_sensor['Conf'])),'Cooling Control'] = 1 #good
    df_ctrl_sensor.loc[(df_ctrl_sensor['Self Resp Val']>-0.4) & (df_ctrl_sensor['Conf']>1) & (df_ctrl_sensor['Should Action']=='cooldown'),'Cooling Control'] = -1

    #combined control (does what it's supposed to do and well enough)
    df_ctrl_sensor['Temp Control'] = 0 #unknown
    df_ctrl_sensor.loc[((df_ctrl_sensor['Heating Control']==1) & (df_ctrl_sensor['Actual Action']=='warmup') & (df_ctrl_sensor['Should Action']=='warmup')) | ((df_ctrl_sensor['Cooling Control']==1) & (df_ctrl_sensor['Actual Action']=='cooldown') & (df_ctrl_sensor['Should Action']=='cooldown')),'Temp Control'] = 1 #good
    df_ctrl_sensor.loc[((df_ctrl_sensor['Heating Control']==-1) & (df_ctrl_sensor['Should Action']=='warmup')) | ((df_ctrl_sensor['Cooling Control']==-1) & (df_ctrl_sensor['Should Action']=='cooldown')),'Temp Control'] = -1 #bad

    #TODO? if fit error is very low, make it unknown? (seems good without this so far)
    return df_ctrl_sensor

def find_temp_control_type(data,sp_curr,sp_start,sp_end):
    '''
    Determine whether building has heating, cooling or both systems.
    Parameters:
        data (dataframe): Data.
        sp_curr (float): Current setpoint temperature.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
    Returns:
        control type (string): Type of controllability the building likely has.
    '''
    sensors = np.sort(data['Sensor Number'].unique())

    num_heating = 0
    num_cooling = 0
    total = 0
    for sensor in sensors:
        df_ctrl_sensor = comb_control_sensor(data,sensor,sp_curr,sp_start,sp_end)

        #find number of days there is heating controllability
        warm_control = df_ctrl_sensor['Heating Control'].value_counts()
        num_good = warm_control.loc[warm_control.index==1]
        if(len(num_good)!=0):
            num_good = num_good.values[0]
        else:
            num_good = 0
        num_heating = num_heating + num_good
        
        #find number of days there is cooling controllability
        cool_control = df_ctrl_sensor['Cooling Control'].value_counts()
        num_good = cool_control.loc[cool_control.index==1]
        if(len(num_good)!=0):
            num_good = num_good.values[0]
        else:
            num_good = 0
        num_cooling = num_cooling + num_good

        total = total + 6
    
    prob_cooling = num_cooling/total
    prob_heating = num_heating/total

    if(prob_cooling > .05 or num_cooling > 5): #have cooling system (enough cooling occurances)
        cooling = True
    else:
        cooling = False
    
    if(prob_heating > .05 or num_heating > 5): #have heating system (enough heating occurances)
        heating = True
    else:
        heating = False
    
    if(cooling==True and heating==True):#both heating and cooling
        print('System has both heating and cooling capability.')
        return 'Temp Control'
    elif(heating==True):#heating
        print('System has only heating capability')
        return 'Heating Control'
    elif(cooling==True):#cooling
        print('System has only cooling capability.')
        return 'Cooling Control'
    else: #default value
        print('Controllability type not found')
        return 'Temp Control'


def comb_control(data,sp_curr,sp_start,sp_end,control_type='Auto'):
    '''
    Find controllability of each sensor based on the specified mode.
    Parameters:
        data (dataframe): Data.
        sp_curr (float): Current setpoint temperature.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
        control_type (string): Type of controllability to assess (Auto, Cooling, or Heating).
    Returns:
        df_ctrl (dataframe): Contains sensor numbers and their controllability status.
    '''
    print(data)
    sensors = np.sort(data['Sensor Number'].unique())
   
    if(control_type=='Auto'):#if manual control type is not specified, auto determine
        control_type = find_temp_control_type(data,sp_curr,sp_start,sp_end)
    elif(control_type=='Cooling'):
        control_type = 'Cooling Control'
    else:
        control_type = 'Heating Control'

    control_list = []
    sensors_used = []
    for sensor in sensors: 
        #find how many days of each of good, bad, and unknown controllability there are
        df_ctrl_sensor = comb_control_sensor(data,sensor,sp_curr,sp_start,sp_end)
        control_count = df_ctrl_sensor[control_type].value_counts()

        #number of days with bad controllability
        num_bad = control_count.loc[control_count.index==-1]
        if(len(num_bad)!=0):
            num_bad = num_bad.values[0]
        else:
            num_bad = 0

        #number of days with good controllability
        num_good = control_count.loc[control_count.index==1]
        if(len(num_good)!=0):
            num_good = num_good.values[0]
        else:
            num_good = 0

        
        if(num_good==num_bad) or (num_good==0 and num_bad==0): #unknown
            control_list.append(0)
        elif(num_good>num_bad):#controllable
            control_list.append(1)
        else:#uncontrollable
            control_list.append(-1)

        sensors_used.append(sensor)

    #put result in a dataframe
    df_ctrl = pd.DataFrame({'Sensor Number':sensors_used,'Temp Control':control_list})
    df_ctrl.loc[df_ctrl['Temp Control']==-1,'Temp Control Status'] = 'Poor'
    df_ctrl.loc[df_ctrl['Temp Control']==0,'Temp Control Status'] = 'Unknown'
    df_ctrl.loc[df_ctrl['Temp Control']==1,'Temp Control Status'] = 'Good'
    return df_ctrl

def avg_temp_change_time(data,sensor,sp_curr,sp_start,sp_end):
    '''
    Finds average time it takes for specified sensor's temperature to change enough.
    Parameters:
        data (dataframe): Data.
        sensor (string): Sensor number.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
    Returns:
        avg_time_taken (float): Average time taken in hours.
    '''
    data = data[data['Sensor Number']==sensor]

    df_ctrl = comb_control_sensor(data,sensor,sp_curr,sp_start,sp_end) 

    #days with good heating, and days with good cooling controllability
    good_dates_heating = df_ctrl[df_ctrl['Heating Control']==1]
    good_dates_cooling = df_ctrl[df_ctrl['Cooling Control']==1]

    #no controllable days found
    if(len(good_dates_heating)==0 and len(good_dates_cooling)==0):
        print('Cannot use non-controllable sensor.')
        return 0

    #find warmup rates
    dates = good_dates_heating['Date'].unique()
    time_taken_list = []
    for date in dates:
        start_row,stable_row,time_taken,_ = get_start_stable_rows_mode(data,date,sp_start,sp_end,'Heating')
        if(time_taken==0):
            continue
        time_taken_list.append(time_taken) #TODO drop outliers?

    #find cooldown rates
    dates = good_dates_cooling['Date'].unique()
    for date in dates:
        start_row,stable_row,time_taken,_ = get_start_stable_rows_mode(data,date,sp_start,sp_end,'Cooling')
        if(time_taken==0):
            continue
        time_taken_list.append(time_taken) #TODO drop outliers?

    #average temp change time between cooldown and warmup times
    avg_time_taken = np.mean(time_taken_list)
    return avg_time_taken


def func_warmup_sim_fit(t,a,b,c):
    '''
    Function used to fit wamrup times.
    Parameters:
        t (float): Independant value(s).
        a (float): Coefficient.
        b (float): Coefficient.
        c (float): Coefficient.
    Returns:
        value (float): Calculated output.
    '''
    return a * (1 - np.exp(np.multiply(-b, t))) + c

def temp_change_time_sim(data,sensor,fb,sp,fb_curr,sp_curr,sp_start,sp_end):
    '''
    Estimates the time it takes for the given sensor to go from fb temp to sp temp, based on 
    its average temp change time and results from simulations run in OpenStudio.
    Parameters:
        data (dataframe): Data.
        sensor (string): Sensor number.
        fb (float): New fallback temperature.
        sp (float): New setpoint temperature.
        fb_curr (float): Current fallback temp.
        sp_curr (float): Current setpoint temp.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
    '''
    #values found from OpenStudio simulations
    temp_diff = [1,2,3,4,5,6]
    warmup_times = [1.03,1.63,2.26,2.66,3.21,3.68]
    df_sim = pd.DataFrame({'diff':temp_diff,'warmup_time':warmup_times})

    #from simulation results, find setpoint and fallback difference that's closest to this building's
    diff_baseline = abs(sp_curr-fb_curr)
    closest_baseline = df_sim.iloc[(df_sim['diff']-diff_baseline).abs().argsort()[:1]]['warmup_time'].values[0]#closest baseline
    
    #fit a curve to simulation results
    popt,pcov = curve_fit(func_warmup_sim_fit,temp_diff,warmup_times,maxfev=10000)

    diff = abs(sp-fb)
    if(diff==0):
        return 0

    #predict a temp change time based on the fitted cruve
    change_time_pred = func_warmup_sim_fit(diff,*popt)

    #current average change time
    curr_avg_change_time = avg_temp_change_time(data,sensor,sp_curr,sp_start,sp_end)

    #compute temp change time
    change_time_actual = change_time_pred*curr_avg_change_time/closest_baseline#*.9
    #change_time_actual = change_time_pred * 0.5 + curr_avg_change_time * 0.5
    #change_time_actual2 = change_time_actual*0.5 + change_time_pred*0.5
    #change_time = min(change_time_actual,change_time_actual2)
    return change_time_actual

#setpoint schedule

def get_temp_change_cost(t_w,mode):
    '''
    Find cost of temp change.
    Parameters:
        t_w (float): Time for temp to change enough.
        mode (string): Whether to get cost for heating or cooling.
    Returns:
        cost (float): Cost of this temp change time.
    '''
    if(mode=='Heating'):#heating
        cost = 1.3**t_w
    else:#cooling
        cost = 1.3**t_w
    return cost

#cost function based on warmup time, for both heating and cooling mode
def get_schedule_cost(data,T_fb,T_sp,t_sp,t_warmup,mode): 
    '''
    Find cost of this setpoint schedule.
    Parameters:
        data (dataframe): data.
        T_fb (float): New fallback temp.
        T_sp (float): New setpoint temp.
        t_sp (float): Setpoint duration.
        t_warmup (float): Time taken for temp to change enough.
        mode (string): Heating or Cooling mode.
    Returns:
        cost (float): Cost of this schedule.
    '''
    if(mode=='Heating'):
        cost_warmup = get_temp_change_cost(t_warmup,mode)
        cost_fb = T_fb #if heating means system needs to rise temp, so higher temp has higher cost

    else: #cooling
        cost_warmup = get_temp_change_cost(t_warmup,mode)
        cost_fb = -T_fb #if cooling means system needs to drop temp, so lower temp has higher cost
        
    cost = cost_fb + cost_warmup
    return cost

def find_setpoint_schedule(data,sensor,fb_curr,sp_curr,T_sp,sp_start,sp_end,occ_start,occ_end,mode):
    '''
    Find optimal setpoint schedule.
    Parameters:
        data (dataframe): Data.
        sensor (string): Sensor number.
        fb_curr (float): Current fallback temperature.
        sp_curr (float): Current setpoint temperature.
        T_sp (float): New setpoint.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
        occ_start (string): Occupied time start (format 09:00).
        occ_end (string): Occupied time end (format 17:00).
    Returns:
        sp_start_new (string): Time the setpoint should start.
        sp_end_new (string): Time the setpoint should end.
        best_fb (float): Best fallback temperature.
        t_warmup (float): Temp change time.
    '''

    data = data[data['Sensor Number']==sensor]
    #occupied time duration
    t_sp = get_time_difference(sp_start,sp_end)

    #set fallback range based on mode
    if(mode=='Heating'):
        min_fallback = min(15,fb_curr-3) 
        max_fallback = min(T_sp+0.5,fb_curr+0.5)
        best_fb = fb_curr-1
    else:#cooling mode
        min_fallback = max(np.ceil(T_sp),fb_curr)
        max_fallback = max(fb_curr+3,28)
        best_fb = fb_curr+1
    
    lowest_cost = float('inf')
    
    #set default warmup time to be so that setpoint starts at 00:00 if no usable warmup time was found
    best_warmup = datetime.datetime.strptime(occ_start,'%H:%M').hour + datetime.datetime.strptime(occ_start,'%H:%M').minute/60#0
    
    #go through possible fallback temps
    for fb in np.arange(min_fallback,max_fallback,0.5):
        t_warmup = temp_change_time_sim(data,sensor,fb,T_sp,fb_curr,sp_curr,sp_start,sp_end)

        if(t_warmup!=t_warmup):#check if it's nan
            t_warmup=0
        if(t_warmup==0):
            continue

        sp_start_new = (pd.to_datetime(occ_start) - timedelta(hours=t_warmup)).strftime('%H:%M')

        if(sp_start_new >sp_end or t_warmup>8): #if too high, not usable
            continue

        cost = get_schedule_cost(data,fb,T_sp,t_sp,t_warmup,mode)

        if(cost < lowest_cost): #if better cost found
            lowest_cost = cost
            best_fb = fb
            best_warmup = t_warmup
    
    #calculate best setpoint time
    t_warmup = np.rint(best_warmup)
    sp_start_new = pd.to_datetime(occ_start) - timedelta(hours=t_warmup)
    sp_end_new = pd.to_datetime(occ_end)
    hour_format = "%H:%M"
    sp_start_new = sp_start_new.strftime(hour_format)
    sp_end_new = sp_end_new.strftime(hour_format)
    return sp_start_new, sp_end_new,best_fb,t_warmup

#cost saving ##################################################################
def func_fit_savings(t,a,b,c):
    '''
    Function used to fit cost savings.
    Parameters:
        t (float): Independant value(s).
        a (float): Coefficient.
        b (float): Coefficient.
        c (float): Coefficient.
    Returns:
        value (float): Calculated output.
    '''
    return a*np.log(t+b)+c

def get_cost_savings(building_size,fb_change,sp_change,sp_time_change,early_start):
    '''
    Find overall cost savings of the new setpoint schedule.
    Parameters:
        building_size (float): Size of the building in squared feet.
        fb_change (float): How much fallback was changed in the new schedule.
        sp_change (float): How much setpoint was changed in the new schedule.
        sp_time_change (float): How much longer the duration of setpoint being active is.
        early_start (float): How much sooner is the setpoint activated.
    Returns:
        overall_savings (float): Percentage savings.
    '''

    #cost due to larger hvac schedule
    # times = [0,-4]
    # savings = [0,10.5]
    # popt=np.polyfit(times,savings,1)
    # pred_savings = get_poly_y([sp_time_change],popt)

    #savings due to early start


    #savings due to lower fallback (should be seperated from deadband savings)
    # temp = [18.3,15.56] #converted from fahrenheit [65,60]
    # savings = [0,10.2]
    # popt=np.polyfit(temp,savings,1)
    # pred_savings = get_poly_y([fb_change],popt)

    #cost due to sp change
    

    #--------------------------------------
    #cost savings due to early start, from research
    building_sizes = np.array([20000,53600,200000])
    hour_savings = np.array([2.13,2.47,3])

    #fit curve to predict hour savings based on building size
    popt,_ = curve_fit(func_fit_savings,building_sizes,hour_savings,maxfev=10000)

    #test fit by MSE and graphing
    # test_pred_hour_savings = func_fit_savings(building_sizes,*popt)
    # MSE = mean_squared_error(hour_savings, test_pred_hour_savings)
    # print(MSE)
    # fig = go.Figure()
    # fig.add_trace(go.Scatter(x=building_sizes,y=hour_savings,name='actual'))
    # fig.add_trace(go.Scatter(x=building_sizes,y=test_pred_hour_savings,name = 'predicted'))
    # fig.show()

    #predict hour savings based on building size
    pred_hour_saving = func_fit_savings(building_size,*popt)

    overall_savings = early_start * pred_hour_saving
    return overall_savings

#predictive new setpoint data
def sp_improved_data(data,df_full,sp_curr,sp_change,temp_change_time,sp_start,sp_end):
    '''
    Find estimated overtime temperatures given the setpoint change and warmup time.
    Extend occupied temp values using the middle of day temps, and shift to left by warmup time
    Parameters:
        data (dataframe): Data.
        sp_curr (float): Current setpoint temp.
        sp_change (float): Optimal setpoint change.
        temp_change_time (float): Temp change time for the new schedule.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
    Returns:
        df_new2 (dataframe): Estimated dataframe.
    '''
    #shift temps accroding to setpoint change
    df_new = shift(data,df_full,sp_curr,sp_start,sp_end,sp_change)

    df_new['Time_of_day'] = df_new['TimeStamp'].dt.strftime("%H:%M")
    df_new.index = df_new['TimeStamp']
    df_new = df_new.sort_index()
    df_new2 = pd.DataFrame()
    sensors = df_new['Sensor Number'].unique()
    for sensor in sensors:
        dfi = df_new[df_new['Sensor Number']==sensor]
        dates = dfi['Date'].unique()
        for date in dates:
            dfd = dfi[dfi['Date']==date]

            #seperate before and afternoon data
            dfd_afternoon = get_data_between_time(dfd,'12:00','23:59')
            dfd_beforenoon = get_data_between_time(dfd,'00:00','11:59')

            #find time temp_change_time hours after 12:00
            t = (pd.to_datetime('12:00') + timedelta(hours=temp_change_time)).strftime('%H:%M')

            #get data starting at 12:00, ending after temp_change_time hours. then shift it to end at 12:00.
            dfd_afternoon_start = get_data_between_time(dfd_afternoon,'12:00',t)
            dfd_afternoon_start['TimeStamp'] = dfd_afternoon_start['TimeStamp'] -timedelta(hours=temp_change_time)
            dfd_afternoon_start['Date'] = pd.to_datetime(dfd_afternoon_start['TimeStamp'].dt.strftime('%Y-%m-%d'))
            
            #open space for new data by shifting beforenoon data to the left
            dfd_beforenoon['TimeStamp'] = dfd_beforenoon['TimeStamp'] - timedelta(hours=temp_change_time)
            dfd_beforenoon['Date'] = pd.to_datetime(dfd_beforenoon['TimeStamp'].dt.strftime('%Y-%m-%d'))

            #remove times that go into next day after shift
            dfd_beforenoon = dfd_beforenoon[dfd_beforenoon['Date']==date] 
            
            #combine the three dataframes 
            dfd_beforenoon = dfd_beforenoon.append(dfd_afternoon_start)
            dfd_beforenoon.index = dfd_beforenoon['TimeStamp']
            df_new2 = df_new2.append(dfd_afternoon)
            df_new2 = df_new2.append(dfd_beforenoon)

        
    df_new2['Temperature'] = df_new2['Temperature_shifted']
    df_new2 = df_new2.drop(columns=['Temperature_shifted'])
    df_new2.index = df_new2['TimeStamp']
    df_new2 = df_new2.sort_index()
    return df_new2


#testing graph#####################################################################
def graph_test_all(data,fb,sp,sp_start,sp_end,var='Temperature'):
    '''
    Graphs all sensors' temperature values and setpoint schedule overtime. For testing purposes.
    '''
    hovertemplate = 'Date: %{x|%Y %b %d, %a}<br>Time: %{x|%H:%M}<br>'+var+': %{y}<br>'

    data.index = data['TimeStamp']
    sensors = np.sort(data['Sensor Number'].unique())
    fig = general_graph_overtime_multiline(data,'Sensor Number',sensors,'',var,hovertemplate,'','Date',var)

    #add grey rectangles for occupied time
    dates = data['Date'].unique()
    for date in dates:
        dfi = data[data['Date']==date]
        dfi = get_data_between_time(dfi,sp_start,sp_end)
        #dfi = get_occupied(dfi)
        dfi = dfi.loc[dfi.index.notnull()]
        #dfi.index = dfi['TimeStamp']
        if(len(dfi)==0):
            continue

        fig.add_vrect(x0=dfi.index.min(),x1=dfi.index.max(),fillcolor='grey',opacity=.1,line_width=0)
    fig.update_layout({
    'plot_bgcolor': 'white',
    'paper_bgcolor': 'white',
    })

    #add setpoint schedule
    data['sp'] = sp
    data.loc[(data['Time_of_day']<sp_start) | (data['Time_of_day']>sp_end), 'sp'] = fb
    fig = plot_add_dotted_line(fig,data.index,data['sp'],'Setpoint','',[],'blue')

    #Add outside temp
    #fig.add_trace(go.Scatter(x=data.index,y=data['Temperature_Outside']))
    fig.update_traces(hovertemplate=hovertemplate)
    fig.update_xaxes(dtick='D',tickformat="%A<br>%b %d")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7')

    fig.show()

# testing graph controllability ####################################################################################
def test_plot_control(data,fb,sp_curr,sp_start,sp_end,comf_min,comf_max,control_type=''):
    '''
    Makes three overtime graphs, one for each of controllable, uncontrollable, unknown. For testing purposes.
    '''
    data = remove_partial_dates(data,sp_start,sp_end)
    data.index = data['TimeStamp']
    
    data['sp'] = sp_curr
    data.loc[(data['Time_of_day']<sp_start) | (data['Time_of_day']>sp_end), 'sp'] = fb


    df_ctrl = comb_control(data,sp_curr,sp_start,sp_end,control_type)
    sensors_good = df_ctrl[df_ctrl['Temp Control']==1]['Sensor Number']
    sensors_unknown = df_ctrl[df_ctrl['Temp Control']==0]['Sensor Number']
    sensors_bad = df_ctrl[df_ctrl['Temp Control']==-1]['Sensor Number']
    if(len(sensors_good)==0):
        print('No controllable sensors, optimizing based on sensors with unknown controllability')
        return ['<div class="alert alert-danger" role="alert">No controllable sensors, optimizing based on sensors with unknown controllability</div>']
    
    df_good = data[data['Sensor Number'].isin(sensors_good)]
    df_unknown = data[data['Sensor Number'].isin(sensors_unknown)]
    df_bad = data[data['Sensor Number'].isin(sensors_bad)]


    filterVar = 'Sensor Number'
    items = np.sort(data['Sensor Number'].unique())
    x_column = ''
    y_column = 'Temperature'
    name_item = ''
    xaxis_label = 'Date'
    yaxis_label = 'Temperature'
    linewidth = 1
    customdata = ['Sensor Number']
    ticksuffix = '°C'

    #controllable 
    hovertemplate = 'Sensor Number: %{customdata[0]}<br>Date: %{x|%b %d, %Y, %a}<br>Time: %{x|%H:%M}<br>Temperature: %{y}<br>'
    fig = general_graph_overtime_multiline(df_good, filterVar, items, x_column, y_column, hovertemplate, name_item, xaxis_label, yaxis_label, linewidth, customdata, ticksuffix)
    fig.add_hrect(y0=comf_min,y1=comf_max,fillcolor='LightSeaGreen',opacity=.1)
    fig = plot_add_dotted_line(fig,data.index,data['sp'],'Setpoint','',[],'blue')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7')
    fig.show()

    #df_unknown 
    hovertemplate = 'Sensor Number: '+df_unknown['Sensor Number'].astype(str)+'<br>Date: %{x|%b %d, %Y, %a}<br>Time: %{x|%H:%M}<br>Temperature: %{y}<br>'
    fig = general_graph_overtime_multiline(df_unknown, filterVar, items, x_column, y_column, hovertemplate, name_item, xaxis_label, yaxis_label, linewidth, customdata, ticksuffix)
    fig.add_hrect(y0=comf_min,y1=comf_max,fillcolor='LightSeaGreen',opacity=.1)
    fig = plot_add_dotted_line(fig,data.index,data['sp'],'Setpoint','',[],'blue')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7')
    fig.show()

    #uncontrollable 
    hovertemplate = 'Sensor Number: %{customdata[0]}<br>Date: %{x|%b %d, %Y, %a}<br>Time: %{x|%H:%M}<br>Temperature: %{y}<br>'
    fig = general_graph_overtime_multiline(df_bad, filterVar, items, x_column, y_column, hovertemplate, name_item, xaxis_label, yaxis_label, linewidth, customdata, ticksuffix)
    fig.add_hrect(y0=comf_min,y1=comf_max,fillcolor='LightSeaGreen',opacity=.1)
    fig = plot_add_dotted_line(fig,data.index,data['sp'],'Setpoint','',[],'blue')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7')
    fig.show()

#test sepoint vision #######################################################################################################################################################################
def test_sp_vision(data,sp_start,sp_end):
    '''
    Graphs stable parts of data, that is used to find the optimal setpoint.
    Parameters:
        data (dataframe): Data.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
    '''
    data = remove_partial_dates(data,sp_start,sp_end)
    data,_ = get_data_days(data)
    df = data
    df.index = df['TimeStamp']
    df = df.sort_index()
    sensors = df['Sensor Number'].unique()
    fig = go.Figure()
    for sensor in sensors:
        dfi = df[df['Sensor Number']==sensor]
        dates = dfi['Date'].unique()
        df_new = pd.DataFrame()
        for date in dates:
            dfd = dfi[dfi['Date']==date]
            start_row,stable_row,_,dfd = get_start_stable_rows(dfi,date,sp_start,sp_end)
            if(len(dfd)==0):
                continue
            dfd.loc[dfd['TimeStamp']<=stable_row['TimeStamp'],'Temperature'] = np.NaN #so it doesn't connect the missing values
            df_new = df_new.append(dfd)
        fig.add_trace(go.Scatter(x=df_new.index,y=df_new['Temperature'],name=sensor))
    fig.show()

#graph module ###########################################################################################################################
def sp_opt_main(data,sensors_good,fb_curr,sp_curr,sp_start,sp_end,occ_start,occ_end,comf_temp_min,comf_temp_max,mode='Auto'):
    '''
    Finds the optimal setpoint and schedule.
    Parameters:
        data (dataframe): Data.
        sensors_good (list): List of controllable sensors for the chosen mode.
        fb_curr (float): Current fallback temp.
        sp_curr (float): Current setpoint temperature.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
        occ_start (string): Occupied time start.
        occ_end (string): Occupied time end.
        comf_temp_min (float): Minimum comfortable temp.
        comf_temp_max (float): Maximum comfortable temp.
        mode (string): Auto, Heating, or Cooling.
    Returns:
        best_fb (float): New fallback temperature.
        sp_new (float): New setpoint temperature.
        best_time_start (string): New setpoint time start.
        best_time_end (string): New setpoint end time.
        best_warmup_time (float): Warmup time for this schedule.
    '''
    #determine whether we give setpoint schedule for cooling or heating system
    if(mode=='Auto'):
        if(sp_curr>=fb_curr): #if setpoint is higher than fallback, likely optimizing heating
            mode='Heating'
        else: #else, likely optimizing cooling
            mode='Cooling'

    #get portion of data to optimize
    df_good_sp = get_setpoint_data(data,sp_start,sp_end)
    
    #find new setpoint
    sp_change = find_best_setpoint(df_good_sp,data,sp_curr,sp_start,sp_end,comf_temp_min,comf_temp_max) 
    sp_new = sp_curr + sp_change

    #find best schedule for each sensor
    time_start_list = []
    time_end_list = []
    fb_list = []
    t_warmup_list = []
    for sensor in sensors_good:
        time_start,time_end,fb,t_warmup = find_setpoint_schedule(data,sensor,fb_curr,sp_curr,sp_new,sp_start,sp_end,occ_start,occ_end,mode)  
        time_start_list.append(time_start)
        time_end_list.append(time_end)
        fb_list.append(fb)
        t_warmup_list.append(t_warmup)  
    
    #take average values of the sensors' schedule
    time_end_list = list(np.sort(time_end_list))
    best_time_end = time_end_list[int(len(time_end_list)/2)]#choose middle value as best time
    best_fb = np.median(fb_list)
    t_warmup_list = list(np.sort(t_warmup_list))
    best_warmup_time = np.rint(np.mean([x for x in t_warmup_list])) #int(x)?
    best_time_start = pd.to_datetime(occ_start) - timedelta(hours=best_warmup_time)
    best_time_start = best_time_start.strftime("%H:%M")
    return best_fb,sp_new,best_time_start,best_time_end,best_warmup_time

#cost saving graph ################################################################################################
def graph_cost_savings_donut(value): 
    '''
    Plots a donut plot of the given value followed by percent sign.
    Parameters:
        value (float): value to plot.
    '''
    fig, ax = plt.subplots(figsize=(10,5), subplot_kw=dict(aspect="equal"))

    data = [100-round(value,1), round(value,1)]

    #make a pie graph
    wedges, texts = ax.pie(data,colors=['#B2BABB','#065BA7'], wedgeprops=dict(width=0.3), startangle=-270)

    sumstr = str(data[1])+'%'
    font = {'family': 'arial', #title font
        'color':  '#065BA7',
        'weight': 'bold',
        'size': 25,
        }
    font2 = {'family': 'arial', #text font
        'color':  '#065BA7',
        'weight': 'bold',
        'size':30,
        }
    
    #Put the score text in the centre of the donut
    ax.text(0, 0., sumstr,fontdict=font2,color='#065BA7', horizontalalignment='center', verticalalignment='center')
    
    #plt.savefig("donut.png", dpi = 100, transparent=False, bbox_inches='tight', pad_inches=-.36)
    
    plt.title('Annual Energy Savings', fontdict=font)
    imgdata = StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)
    data = imgdata.getvalue()
    return data

def graph_cost_savings_bar(savings):
    '''
    Makes a barplot that shows the savings provided.
    '''
    x = ['Annual Cost Savings']
    y = np.array([round(savings,1)])
    yaxis_label = 'Cost Savings'
    texttemplate = '%{y}'
    hoverVarComb = []
    hovertemplate = '%{x}: %{y}<extra></extra>'
    yrange = [0,savings+1]
    ticksuffix = '%'
    fig = general_barplot(x,y,'',yaxis_label,texttemplate,hoverVarComb,hovertemplate,yrange,ticksuffix)
    #fig.update_traces(orientation='h')
    #fig['data'][0].width=0.2
    return fig

#summary function#################################################################################################
def opt_setpoint_graph(fb1,sp1,fb2,sp2,sp1_start,sp1_end,sp2_start,sp2_end):
    '''
    Graph two setpoint schedules and show recommendation text.
    Parameters:
        fb1 (float): Current fallback temp.
        sp1 (float): Current setpoint temp.
        fb2 (float): New fallback temp.
        sp2 (float): New setpoint temp.
        sp1_start (string): Start time of current setpoint.
        sp1_end (string): End time of current setpoint.
        sp2_start (string): Start time of new setpoint.
        sp1_end (string): End time of new setpoint.
    '''
    #to show every other hour on the xaxis
    times = []
    zero = pd.to_datetime('00:00')
    for h in range(12):
        tmp = zero + timedelta(hours=2*h)
        tmp = tmp.strftime('%H:00')
        times.append(tmp)

    #add setpoint schedules to a dataframe
    base_times=pd.DataFrame({'time': pd.date_range(start='00:00', end='23:59', freq='1 min')})
    base_times['time'] = base_times.apply(lambda row: row['time'].strftime('%H:%M'),axis='columns')
    base_times['Temp1'] = float(fb1)
    base_times.loc[(base_times['time']>=sp1_start) & (base_times['time']<=sp1_end),'Temp1'] = float(sp1)

    base_times['Temp2'] = float(fb2)
    base_times.loc[(base_times['time']>=sp2_start) & (base_times['time']<=sp2_end),'Temp2'] = float(sp2)


    hovertemplate1 = '<b>Current Setpoint Schedule</b><br>Temperature: %{y}<br>Time: %{x}<extra></extra>'
    hovertemplate2 = '<b>Optimized Setpoint Schedule</b><br>Temperature: %{y}<br>Time: %{x}<extra></extra>'
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=base_times['time'],y=base_times['Temp1'],line=dict(dash='dashdot',color='#065ba7'),name='Current Setpoint Schedule',hovertemplate=hovertemplate1))
    fig.add_trace(go.Scatter(x=base_times['time'],y=base_times['Temp2'],line=dict(dash='dashdot',color='#64ad1d'),name='Optimized Setpoint Schedule',hovertemplate=hovertemplate2))
    fig.update_xaxes(tickvals=times,ticktext=times)
    fig.update_layout({'plot_bgcolor': 'white','paper_bgcolor': 'white'},legend= {'itemsizing': 'constant'})
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7',ticksuffix='°C')
    fig.update_layout(showlegend=True)
    fig.update_yaxes(title='Temperature')
    fig.update_xaxes(title='Time')

    #add recommendation text
    text = '<b>Recommendation: </b> Have '+str(sp2)+'°C as your setpoint from '+str(sp2_start)+' to '+str(sp2_end)+' and '+str(fb2)+'°C afterwards.'
    fig = add_annotations(fig,[0.1],[1.25],[text],['#d9f7d3'])

    return fig

def get_comfort_range(data,comf_temp_min,comf_temp_max,pmv_min,pmv_max):
    '''
    Determine comfort range based on given pmv or temperatures. If comf_temp min and max are equal, use pmv.
    Parameters:
        data (dataframe): Data.
        comf_temp_min (float): Min comfortable temp.
        comf_temp_max (float): Max comfortable temp.
        pmv_min (float): Min PMV value.
        pmv_max (float): Max PMV value.
    Returns:
        comf_temp_min (float): Min comfortable temp.
        comf_temp_max (float): Max comfortable temp.
    '''

    #comfort temperature range to use
    if(comf_temp_min!=comf_temp_max): #if comfort temp provided
        pass
    else: #else use pmv
        comf_temp_min,comf_temp_max=opt_temp_pmv(data,pmv_min,pmv_max)

    return comf_temp_min,comf_temp_max


def add_comfort(data,comf_temp_min,comf_temp_max):
    '''
    Add comfortable status to every row of the data.
    Parameters:
        data (dataframe): Data.
        comf_temp_min (float): Min comfortable temp.
        comf_temp_max (float): Max comfortable temp.
    Returns:
        data (dataframe): Data with added comfort status.
    '''
    comf=list()
    for i in range(len(data)):
        if((comf_temp_min<=data['Temperature'][i]<=comf_temp_max)):
            comf.append(1)
        else:
            comf.append(0)
    data['Comfort']=comf
    return data

def get_comf_percent_summary_op(data, floor='Building'):
    '''
    Get comfort percentage of locations within building or specified floor.
    Parameters:
        data (dataframe): Contains sensors and their data.
        floor (string): use this floor's data only.
    Returns:
        df (dataframe): Contains sensors and their comfort percentage.
    '''
    locations = data['Location'].unique()
    locations = [l for l in locations if l==l]
    zone = sorted(locations)
    loc = list()
    comfp = list()
    for z in zone:
        f_data = data[data['Location'] == z]
        if(floor != 'Building'):
            f_data = f_data[f_data['Floor'] == floor]
        if(len(f_data) != 0):
            loc.append(z)
            PT=round(len(f_data[f_data['Comfort']==1])*100/len(f_data),2)
            comfp.append(PT)

     
    dict = {'Location': loc, 'comf_percentage': comfp}  
    df = pd.DataFrame(dict)
    return df  

def get_text_size(text,size):
    '''
    Change text to the specified size.
    '''
    text_new = f'<span style="font-size: 10px;">' + text
    return text_new

def sp_opt_comf_barplots(data,data_new,occ_start,occ_end,comf_temp_min,comf_temp_max):
    '''
    Shows double barplots for thermal comfort percentage of the two provided datasets for each of their locations.
    Parameters:
        data (dataframe): Data to use as a baseline.
        data_new (dataframe): Data to compare the baseline to.
        occ_start (string): The time occupancy starts.
        occ_end (string): The time occupancy ends.
        comf_temp_min (float): Minimum comfortable temperature.
        comf_temp_max (float): Maximum comfortable temperature.
    '''
    #get occupied portion of data
    data = get_data_between_time(data,occ_start,occ_end)
    data_new = get_data_between_time(data_new,occ_start,occ_end)
    
    #add comfort info to data and get comfortable percentage of each location
    data = add_comfort(data,comf_temp_min,comf_temp_max)
    
    # data['Location']=['Cafeteria']*len(data)
    comf_perc = get_comf_percent_summary_op(data)

    data_new = add_comfort(data_new,comf_temp_min,comf_temp_max)
    # data_new['Location']=['Cafeteria']*len(data_new)
    comf_perc_new = get_comf_percent_summary_op(data_new)
   
    #make the graph
    xlabel = 'Location'
    ylabel = 'Percent of Time in Comfortable Range'
    texttemplate = '%{y}'
    hoverVarComb = []
    hovertemplate_curr = '<b>Current Setpoint Schedule</b><br>Current Occupant Comfort: %{y} of the occupied time<br>Location: %{x}<extra></extra>'
    hovertemplate_pred = '<b>Optimized Setpoint Schedule</b><br>Predicted Occupant Comfort: %{y} of the occupied time<br>Location: %{x}<extra></extra>'
    yrange = [0,110]
    ticksuffix = '%'
    ticktext = []
    tickvals = []
    time = ''
    comf_perc['comf_percentage'] = np.rint(comf_perc['comf_percentage'])
    comf_perc_new['comf_percentage'] = np.rint(comf_perc_new['comf_percentage'])
    fig = general_barplot_opt(comf_perc['Location'],comf_perc['comf_percentage'],xlabel,ylabel,texttemplate,hoverVarComb,hovertemplate_curr,yrange,ticksuffix,ticktext,tickvals,time)
    fig['data'][-1]['name'] = 'Current Floor Performance'
    fig['data'][-1]['showlegend'] = True

    #add the second bar
    fig.add_bar(x=comf_perc_new['Location'],y=comf_perc_new['comf_percentage'],hovertemplate=hovertemplate_pred,marker={'color':'#008000'},texttemplate=texttemplate,textangle=0)
    fig['data'][-1]['showlegend'] = True
    fig['data'][-1]['name'] = 'Predicted Floor Performance'
    
    #show small values outside the bar so they fit
    textposition_list = []
    e_max = max(comf_perc['comf_percentage'].max(),comf_perc_new['comf_percentage'].max())
    e_outside = e_max*.15
    for e,v in zip(comf_perc['comf_percentage'],comf_perc_new['comf_percentage']): 
        if(e<=e_outside or v <=e_outside):
            textposition_list.append('outside')
        else:
            textposition_list.append('inside')
    fig.update_traces(textposition=textposition_list)
    
    #add target line
    fig.add_trace(go.Scatter(x=comf_perc['Location'],y=[100]*len(comf_perc), mode='lines', line=dict(color='#9BCA3B', width=3), name = 'Target'))

    #add time period and comfortable range text
    timeText = get_occupancy_text('Occupied Hours',occ_start,occ_end)
    fig = add_legend_text(fig,timeText)
    comf_range_text = get_text_size('<br><b>Comfortable<br>Temperature<br>Range <br></b>'+str(comf_temp_min)+'°C - '+str(comf_temp_max)+'°C<br>',10)
    fig = add_legend_text(fig,comf_range_text)
    
   
    #find comfort improvement and add text saying that
    avg_comf_curr = round(comf_perc['comf_percentage'].mean(),2)
    avg_comf_new = round(comf_perc_new['comf_percentage'].mean(),2)
    comf_diff = round((avg_comf_new - avg_comf_curr),1)
    fig.update_layout(title='Predicted average occupant comfort improved by '+str(comf_diff)+'% if optimized setpoint is followed')
    
    fig.update_layout(margin={'t':100, 'b':40})
    return fig


# summary ############################################################################################
def sp_opt_summary(floor,data,fb_curr,sp_curr,sp_start,sp_end,occ_start,occ_end,pmv_min=-1,pmv_max=1,comf_temp_min=0,comf_temp_max=0,days=['Mon','Tue','Wed','Thu','Fri'],mode='Auto',building_size=0,report=False):
    '''
    Graphs optimal setpoint schedule and shows comfort improvements for each location using barplots.
    Parameters:
        floor (string): Use this floor's data.
        data (dataframe): Sensors' data.
        fb_curr (float): Current fallback temp.
        sp_curr (float): Current setpont temp.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
        occ_start (string): Occupied time start.
        occ_end (string): Occupied time end.
        pmv_min (float): Minimum predicted mean vote index (for comfort).
        pmv_max (float): Maximum predicted mean vote index (for comfort).
        comf_temp_min (float): Minimum comfortable temp.
        comf_temp_max (float): Maximum comfortable temp.
        days (list): Which days to consider in the analysis.
        mode (string): Auto, Heating, or Cooling.
    '''

    if(floor=='Building'):
        pass
    else:
        data = data[data['Floor']==floor]
    print(len(data))
    #remove start/end date if we don't have enough data for them.
    data = remove_partial_dates(data,sp_start,sp_end)

    data,removed_dates = get_data_days(data,days)

    if(len(data)==0):
        print('No data')
        return ['<div class="alert alert-danger" role="alert">No data exists during the times you have requested. Please review your analysis request, or contact ioAirFlow for assistance.</div>']

    #find comfortable temp range
    comf_temp_min,comf_temp_max = get_comfort_range(data,comf_temp_min,comf_temp_max,pmv_min,pmv_max)
    
    #find sensor controllability
    df_ctrl = comb_control(data,sp_curr,sp_start,sp_end,control_type=mode)
    sensors_good = df_ctrl[df_ctrl['Temp Control']==1]['Sensor Number'].values
    sensors_unknown = df_ctrl[df_ctrl['Temp Control']==0]['Sensor Number'].values
    sensors_bad = df_ctrl[df_ctrl['Temp Control']==-1]['Sensor Number'].values

    if(len(sensors_good)==0):
        print('No controllable sensors, existing')
        return ['<div class="alert alert-danger" role="alert">No controllable sensors, existing</div>']

    df_good = data[data['Sensor Number'].isin(sensors_good)]
    df_unknown = data[data['Sensor Number'].isin(sensors_unknown)]
    df_bad = data[data['Sensor Number'].isin(sensors_bad)]

    #find best setpoint schedule and temperatures
    best_fb,sp_new,best_time_start,best_time_end,best_warmup_time = sp_opt_main(df_good,sensors_good,fb_curr,sp_curr,sp_start,sp_end,occ_start,occ_end,comf_temp_min,comf_temp_max,mode)
    sp_change = sp_new-sp_curr

    #estimate the data if the new schedule was followed
    comf_data_new = sp_improved_data(df_good,data,sp_curr,sp_change,best_warmup_time,sp_start,sp_end)

    comf_data_new = comf_data_new.append(df_unknown)
    comf_data_new = comf_data_new.append(df_bad)
    r=[]
    #graph setpoint schedule
    fig1=opt_setpoint_graph(fb_curr,sp_curr,best_fb,sp_new,sp_start,sp_end,best_time_start,best_time_end)
    r.append(fig1.to_html())
    if(report == False):
        r.append('<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" data-target="#tahm_3"  >Guide on How to Read This Graph</h5><div id="tahm_3" ><p style="padding:15px;">This graph represents your current setpoint schedule over a typical 24-hour period during occupied hours in blue, with a new recommended setpoint schedule provided in green. The specific figures and times for the optimized setpoint schedule can also be found at the top of the graph.</p></div></div>')
    
    #graph comfort change barplots
    fig2=sp_opt_comf_barplots(data,comf_data_new,occ_start,occ_end,comf_temp_min,comf_temp_max)
    r.append(fig2.to_html())
    r.append('<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" data-target="#tahm_3"  >Guide on How to Read This Graph</h5><div id="tahm_3" ><p style="padding:15px;">This graph forecasts the effect on occupant comfort that will be realized with the new recommended setpoint schedule in green. Columns in blue represent the current occupant comfort levels in your space. Areas are categorized by room type, and are measured against ASHRAE 55 standards on occupant comfort, with a target value of 100%. </p></div></div>')

    #graph cost savings if building size is provided
    if(building_size==0 and report==False):
        return r
    cost_savings = get_cost_savings(building_size,(best_fb-fb_curr),sp_change,best_warmup_time,best_warmup_time)
    fig3=graph_cost_savings_bar(cost_savings)
    r.append(fig2.to_html())
    r.append(graph_cost_savings_donut(cost_savings))

    if(report):
        graphs = []
        graphs.append(fig1)
        graphs.append(fig2)
        return graphs
    return r

# controllable sensors ####################################################################################################
def controllable_sensors(data,floor,fb_curr,sp_curr,sp_start,sp_end,occ_start,occ_end,pmv_min=-1,pmv_max=1,comf_temp_min=0,comf_temp_max=0,days=['Mon','Tue','Wed','Thu','Fri'],mode='Auto'):
    '''
    Shows overtime graphs of controllable sensors before and (their estimate) values after optimization.
    Parameters:
        data (dataframe): Sensors' data.
        floor (string): Use this floor's data.
        fb_curr (float): Current fallback temp.
        sp_curr (float): Current setpont temp.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
        occ_start (string): Occupied time start.
        occ_end (string): Occupied time end.
        pmv_min (float): Minimum predicted mean vote index (for comfort).
        pmv_max (float): Maximum predicted mean vote index (for comfort).
        comf_temp_min (float): Minimum comfortable temp.
        comf_temp_max (float): Maximum comfortable temp.
        days (list): Which days to consider in the analysis.
        mode (string): Auto, Heating, or Cooling.
    '''
    print(floor)
    if(floor !='Building'):
        data = data[data['Floor']==floor]

    #remove start/end date if we don't have enough data for them.
    data = remove_partial_dates(data,sp_start,sp_end)

    data,removed_dates = get_data_days(data,days)

    if(len(data)==0):
        print('No data')
        return ['<div class="alert alert-danger" role="alert">No data exists during the times you have requested. Please review your analysis request, or contact ioAirFlow for assistance.</div>']
    r=[]
    #find comfortable temp range and add comfort info to data
    comf_temp_min,comf_temp_max = get_comfort_range(data,comf_temp_min,comf_temp_max,pmv_min,pmv_max)
    data = add_comfort(data,comf_temp_min,comf_temp_max)

    #find controllable sensors
    df_ctrl = comb_control(data,sp_curr,sp_start,sp_end,mode)
    sensors_good = df_ctrl[df_ctrl['Temp Control']==1]['Sensor Number'].values
    df_good = data[data['Sensor Number'].isin(sensors_good)]

    if(len(sensors_good)==0):
        print('No controllable sensors, exiting')
        return ['<div class="alert alert-danger" role="alert">No controllable sensors, exiting</div>']

    #find best setpoint schedule and temperatures
    best_fb,sp_new,best_time_start,best_time_end,best_warmup_time = sp_opt_main(df_good,sensors_good,fb_curr,sp_curr,sp_start,sp_end,occ_start,occ_end,comf_temp_min,comf_temp_max,mode)
    sp_change = sp_new-sp_curr


    #Add average comfort percentage of each sensor to its data
    df_good_comf = pd.DataFrame()
    for sensor in sensors_good:
        dfi = df_good[df_good['Sensor Number']==sensor]
        dfi_occ = get_data_between_time(dfi,occ_start,occ_end)
        if(len(dfi_occ)==0):
            continue
        comf = round(len(dfi_occ[dfi_occ['Comfort']==1])*100/len(dfi_occ),2)
        dfi['Comfort Avg'] = comf
        df_good_comf = df_good_comf.append(dfi)

    
    #Overtime graph of current values
    y_column = 'Temperature'
    groups = df_good_comf['Location'].unique()
    group_var = 'Location'
    filter_var = 'Sensor Number'
    xaxis_label = 'Date'
    yaxis_label = 'Temperature'
    ticksuffix = '°C'
    hovertemplate = '<b>Current Setpoint Schedule</b><br>Sensor Number: %{customdata[0]}<br>Location: %{customdata[1]}<br>Temperature: %{y}<br>Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Current Occupant Comfort: %{customdata[2]}% of the occupied time'
    customdata = ['Sensor Number','Location','Comfort Avg']
    fig_curr = go.Figure()

    #add sp schedule
    df_sp_schedule = df_good_comf[df_good_comf['Sensor Number']==sensors_good[0]]
    df_sp_schedule['sp'] = sp_curr
    df_sp_schedule.loc[(df_sp_schedule['Time_of_day']<sp_start) | (df_sp_schedule['Time_of_day']>sp_end), 'sp'] = fb_curr
    hovertemplate_sp = '<b>Current Setpoint Schedule</b><br>Temperature: %{y}<br>Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}'
    fig_curr = plot_add_dotted_line(fig_curr,df_sp_schedule.index,df_sp_schedule['sp'],'Current Setpoint Schedule',hovertemplate_sp,[],'#065ba7')
    
    #add comfort range
    fig_curr.add_hrect(y0=comf_temp_min,y1=comf_temp_max,fillcolor='LightSeaGreen',opacity=.1)
    fig_curr = add_legend_text(fig_curr,'Comfortable Range')
    fig_curr.data[-1]['line']['color']='LightSeaGreen'
    fig_curr.data[-1]['line']['dash']='dash'
    fig_curr = general_graph_overtime_group_legend(df_good_comf,'',y_column,groups,group_var,filter_var,xaxis_label,yaxis_label,ticksuffix,hovertemplate,customdata,fig_curr)
    
    fig_curr.update_layout(title='Current Sensor Performance on Floor ' + str(floor))

    #don't show dates that were removed, in the graph
    fig_curr.update_xaxes(rangebreaks=[dict(values=removed_dates)])
    r.append(fig_curr.to_html())
    r.append('<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" data-target="#tahm_3"  >Guide on How to Read This Graph</h5><div id="tahm_3" ><p style="padding:15px;">The horizontal axis represents the 24-hour average of all data collected during this performance test. Temperature is recorded on the vertical axis, with the current setpoint schedule noted in blue. The comfortable range for occupants based on ASHRAE 55 standards is highlighted in green.</p></div></div>')
    

    #get predicted sensor data and add comfort info to it
    comf_data_new = sp_improved_data(df_good_comf,data,sp_curr,sp_change,best_warmup_time,sp_start,sp_end)
    comf_data_new = add_comfort(comf_data_new,comf_temp_min,comf_temp_max)
    
    #add sensor's overall comfort average
    df_good_comf_new = pd.DataFrame()
    for sensor in sensors_good:
        dfi = comf_data_new[comf_data_new['Sensor Number']==sensor]
        dfi_occ = get_data_between_time(dfi,occ_start,occ_end)

        if(len(dfi_occ)==0):
            continue
        comf = round(len(dfi_occ[dfi_occ['Comfort']==1])*100/len(dfi_occ),2)
        dfi['Comfort Avg New'] = comf
        df_good_comf_new = df_good_comf_new.append(dfi)
    
    #add comfort increase info
    df_good_comf_new['Comfort Increase'] = df_good_comf_new['Comfort Avg New'] - df_good_comf_new['Comfort Avg']
    df_good_comf_new['Comfort Increase'] = np.round(df_good_comf_new['Comfort Increase'],2)

    #Make predicted overtime graph
    customdata = ['Sensor Number','Location','Comfort Avg New','Comfort Increase']
    hovertemplate = '<b>Optimized Setpoint Schedule</b><br>Sensor Number: %{customdata[0]}<br>Location: %{customdata[1]}<br>Temperature: %{y}<br>Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}<br>Predicted Occupant Comfort: %{customdata[2]}% of the occupied time<br>Predicted Comfort Increase: %{customdata[3]}%'
    fig_pred = go.Figure()

    #add sp schedule
    df_good_comf_new['Time_of_day'] = df_good_comf_new['TimeStamp'].dt.strftime('%H:%M')
    df_sp_schedule_new = df_good_comf_new[df_good_comf_new['Sensor Number']==sensors_good[0]]
    df_sp_schedule_new['sp'] = sp_new
    df_sp_schedule_new.loc[(df_sp_schedule_new['Time_of_day']<best_time_start) | (df_sp_schedule_new['Time_of_day']>best_time_end), 'sp'] = best_fb
    hovertemplate_sp = '<b>Optimized Setpoint Schedule</b><br>Temperature: %{y}<br>Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}'
    fig_pred = plot_add_dotted_line(fig_pred,df_sp_schedule_new.index,df_sp_schedule_new['sp'],'Optimized Setpoint Schedule',hovertemplate_sp,[],'#64ad1d',)
    
    #highlight comfort range
    fig_pred.add_hrect(y0=comf_temp_min,y1=comf_temp_max,fillcolor='LightSeaGreen',opacity=.1)
    fig_pred = add_legend_text(fig_pred,'Comfortable Range')
    fig_pred.data[-1]['line']['color']='LightSeaGreen'#dcdc34, ffffd9
    fig_pred.data[-1]['line']['dash']='dash'

    #add overtime traces
    fig_pred = general_graph_overtime_group_legend(df_good_comf_new,'',y_column,groups,group_var,filter_var,xaxis_label,yaxis_label,ticksuffix,hovertemplate,customdata,fig_pred)
    
    fig_pred.update_layout(title='Predicted Sensor Performance on Floor ' + str(floor))

    #don't show days that were removed, in the graph
    fig_pred.update_xaxes(rangebreaks=[dict(values=removed_dates)])
    r.append(fig_pred.to_html())
    r.append('<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" data-target="#tahm_3"  >Guide on How to Read This Graph</h5><div id="tahm_3" ><p style="padding:15px;">The horizontal axis represents the 24-hour average of all data collected during this performance test. Temperature is recorded on the vertical axis, with the new recommended setpoint schedule noted in green. The comfortable range for occupants based on ASHRAE 55 standards is highlighted in green.</p></div></div>')
    return r


#uncontrollable sensors ########################################################################################################################################################################
def plot_setpoint_schedule(data,comf_min,comf_max,fb,sp,sp_start,sp_end,y_column='Temperature'):
    '''
    Makes a figure that shows temperature values over time and shows the setpoint schedule.
    Parameters:
        data (dataframe): Data.
        comf_min (float): Min comfortable temperature.
        comf_max (float): Max comfortable temperature.
        fb (float): Fallback temp.
        sp (float): Setpoint temp.
        sp_start (time): The time setpoint starts.
        sp_end (time): The time setpoint ends.
        y_column (string): Which column to use the values of for graphing.
    Returns:
        fig (figure object): Figure with specified properties.
    '''

    data.index = data['TimeStamp']
    groups = data['Location'].unique()
    group_var = 'Location'
    filter_var = 'Sensor Number'
    xaxis_label = 'Date'
    yaxis_label = 'Temperature'
    ticksuffix = '°C'
    hovertemplate = 'Sensor Number: %{customdata[0]}<br>Location: %{customdata[1]}<br>Date: %{x|%b %d, %Y, %a}<br>Time: %{x|%H:%M}<br>Temperature: %{y}<br>Current Occupant Comfort: %{customdata[2]}% of the occupied time'
    customdata = ['Sensor Number','Location','Comfort Avg']
    fig = go.Figure()

    #add setpoint schedule
    data_sp = data[data['Sensor Number']==data['Sensor Number'].unique()[0]]
    data_sp['sp'] = sp
    data_sp.loc[(data_sp['Time_of_day']<sp_start) | (data_sp['Time_of_day']>sp_end), 'sp'] = fb
    hovertemplate_sp = '<b>Current Setpoint Schedule</b><br>Temperature: %{y}<br>Date: %{x|%b %d, %Y}<br>Time: %{x|%H:%M}'
    fig = plot_add_dotted_line(fig,data_sp.index,data_sp['sp'],'Current Setpoint Schedule',hovertemplate_sp,[],'blue')

    #add comfort range
    fig.add_hrect(y0=comf_min,y1=comf_max,fillcolor='LightSeaGreen',opacity=.1)
    fig = add_legend_text(fig,'Comfortable Range')
    fig.data[-1]['line']['color']='LightSeaGreen'
    fig.data[-1]['line']['dash']='dash'

    #add sensor traces
    fig = general_graph_overtime_group_legend(data,'',y_column,groups,group_var,filter_var,xaxis_label,yaxis_label,ticksuffix,hovertemplate,customdata,fig)
    return fig

def uncontrollable_sensors(floor,data,fb_curr,sp_curr,sp_start,sp_end,occ_start,occ_end,pmv_min,pmv_max,comf_temp_min,comf_temp_max,days=['Mon','Tue','Wed','Thu','Fri'],mode='Auto'):
    '''
    Shows overtime graphs of uncontrollable and unknown controllable sensors.
    Parameters:
        floor (string): Use this floor's data.
        data (dataframe): Sensors' data.
        fb_curr (float): Current fallback temp.
        sp_curr (float): Current setpont temp.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
        occ_start (string): Occupied time start.
        occ_end (string): Occupied time end.
        pmv_min (float): Minimum predicted mean vote index (for comfort).
        pmv_max (float): Maximum predicted mean vote index (for comfort).
        comf_temp_min (float): Minimum comfortable temp.
        comf_temp_max (float): Maximum comfortable temp.
        days (list): Which days to consider in the analysis.
        mode (string): Auto, Heating, or Cooling. 
    '''
    
    if(floor!='Building'):
        data = data[data['Floor']==floor]

    #remove start/end date if we don't have enough data for them.
    data = remove_partial_dates(data,sp_start,sp_end)

    data,removed_dates = get_data_days(data,days)

    #find comfortable temp range
    comf_temp_min,comf_temp_max = get_comfort_range(data,comf_temp_min,comf_temp_max,pmv_min,pmv_max)
    
    #add comfort info to data
    data = add_comfort(data,comf_temp_min,comf_temp_max)

    #add average comfort percentage for each sensor
    sensors = data['Sensor Number'].unique()
    df_comf = pd.DataFrame()
    for sensor in sensors:
        dfi = data[data['Sensor Number']==sensor]
        dfi_occ = get_data_between_time(dfi,occ_start,occ_end)
        if(len(dfi_occ)==0):
            continue
        comf = round(len(dfi_occ[dfi_occ['Comfort']==1])*100/len(dfi),2)
        dfi['Comfort Avg'] = comf
        df_comf = df_comf.append(dfi)
    if df_comf.empty:
        return ['<div class="alert alert-danger" role="alert">No uncontrollable sensors and controllable sensors found.</div>']


    #find unknown and uncontrollable sensors
    df_ctrl = comb_control(df_comf,sp_curr,sp_start,sp_end,mode)
    sensors_unknown = df_ctrl[df_ctrl['Temp Control']==0]['Sensor Number']
    sensors_bad = df_ctrl[df_ctrl['Temp Control']==-1]['Sensor Number']
    df_unknown = df_comf[df_comf['Sensor Number'].isin(sensors_unknown)]
    df_bad = df_comf[df_comf['Sensor Number'].isin(sensors_bad)]
    r=[]
    #show overtime graph for uncontrollable sensors if any exist
    if(len(sensors_bad)!=0):
        fig_bad = plot_setpoint_schedule(df_bad,comf_temp_min,comf_temp_max,fb_curr,sp_curr,sp_start,sp_end)
        fig_bad.update_xaxes(rangebreaks=[dict(values=removed_dates)])
        fig_bad.update_layout(title='Current Sensor Performance on Floor '+str(floor)+' for Uncontrollable Sensors')
        # fig_bad.show()
        r.append(fig_bad.to_html())
        r.append('<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" data-target="#tahm_3"  >Guide on How to Read This Graph</h5><div id="tahm_3" ><p style="padding:15px;">The horizontal axis represents the 24-hour average of all data collected during this performance test. Temperature is recorded on the vertical axis. The comfortable range for occupants based on ASHRAE 55 standards is highlighted in green. Sensors can be toggled on or off by clicking on individual sensors, or by room categories. Click again on the removed sensor to have it displayed again.</p></div></div>')
    else:
        print('No uncontrollable sensors found.')
        r.append('<div class="alert alert-info" role="alert">No uncontrollable sensors found.</div>')

    #show overtime graph for unknown controllable sensors if any exist
    if(len(sensors_unknown)!=0):
        fig_unknown = plot_setpoint_schedule(df_unknown,comf_temp_min,comf_temp_max,fb_curr,sp_curr,sp_start,sp_end)
        fig_unknown.update_xaxes(rangebreaks=[dict(values=removed_dates)])
        fig_unknown.update_layout(title='Current Sensor Performance on Floor '+str(floor)+' for Unknown Controllability Sensors')
        # fig_unknown.show()
        r.append(fig_unknown.to_html())
        r.append('<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" data-target="#tahm_3"  >Guide on How to Read This Graph</h5><div id="tahm_3" ><p style="padding:15px;">The horizontal axis represents the 24-hour average of all data collected during this performance test. Temperature is recorded on the vertical axis. The comfortable range for occupants based on ASHRAE 55 standards is highlighted in green. Sensors can be toggled on or off by clicking on individual sensors, or by room categories. Click again on the removed sensor to have it displayed again.</p></div></div>')

    else:
        print('No unknown controllability sensors found.')
        r.append('<div class="alert alert-info" role="alert">No unknown controllability sensors found.</div>')
    
    return r

def sp_opt_floormap(floor,data,co_df,image, img_width, img_height, scale_factor,fb_curr,sp_curr,sp_start,sp_end,occ_start,occ_end,pmv_min=-1,pmv_max=1,comf_temp_min=20,comf_temp_max=24,days=['Mon','Tue','Wed','Thu','Fri'],mode='Auto'):
    '''
    Graphs floormaps showing sensors, their controllability, and their comfort percentages before and after optimization.
    Parameters:
        floor (string): Use this floor's data.
        co_df(dataframe): coordinate dataframe
        data (dataframe): Sensors' data.
        fb_curr (float): Current fallback temp.
        sp_curr (float): Current setpont temp.
        sp_start (string): Time when the setpoint is turned on (format 09:00).
        sp_end (string): Time when the setpoint is turned off (format 17:00).
        occ_start (string): Occupied time start.
        occ_end (string): Occupied time end.
        pmv_min (float): Minimum predicted mean vote index (for comfort).
        pmv_max (float): Maximum predicted mean vote index (for comfort).
        comf_temp_min (float): Minimum comfortable temp.
        comf_temp_max (float): Maximum comfortable temp.
        days (list): Which days to consider in the analysis.
        mode (string): Auto, Heating, or Cooling.
    '''
    r=[]
    if(floor!='Building'):
        data = data[data['Floor']==floor]

    #remove start/end date if we don't have enough data for them.
    data = remove_partial_dates(data,sp_start,sp_end)
  

    data,removed_dates = get_data_days(data,days)

    #find comfort temp range
    comf_temp_min,comf_temp_max = get_comfort_range(data,comf_temp_min,comf_temp_max,pmv_min,pmv_max)

    #add comfort info to data
    data = add_comfort(data,comf_temp_min,comf_temp_max)

    #get coordinate of sensors on floormap
    #co_df = get_sensor_coordinates()

    #get controllability of sensors
    df_ctrl = comb_control(data,sp_curr,sp_start,sp_end,mode)

    #combine coordinates and controllability info
    s_df = pd.merge(co_df,df_ctrl,how='left',on='Sensor Number')
    s_df = s_df[s_df['Sensor Number'].isin(df_ctrl['Sensor Number'])]
    s_df = s_df.reset_index(drop=True)
    s_df = s_df.loc[:, ~s_df.columns.str.contains('^Unnamed')]

    #add current average comfort percentage of each sensor
    sensors = s_df['Sensor Number'].unique()
    s_df['Comfort'] = 0
    for sensor in sensors:
        dfi = data[data['Sensor Number']==sensor]
        dfi = get_data_between_time(dfi,occ_start,occ_end)
        if(len(dfi)==0):
            continue
        comf = round(len(dfi[dfi['Comfort']==1])*100/len(dfi),2)
        s_df.loc[s_df['Sensor Number']==sensor,'Comfort'] = comf
        s_df.loc[s_df['Sensor Number']==sensor,'Location'] = dfi['Location'].unique()[0] #add location info


    #seperate good, unknown, and bad sensors
    sensors_good = df_ctrl[df_ctrl['Temp Control']==1]['Sensor Number'].values
    sensors_unknown = df_ctrl[df_ctrl['Temp Control']==0]['Sensor Number'].values
    sensors_bad = df_ctrl[df_ctrl['Temp Control']==-1]['Sensor Number'].values

    df_good = data[data['Sensor Number'].isin(sensors_good)]
    df_unknown = data[data['Sensor Number'].isin(sensors_unknown)]
    df_bad = data[data['Sensor Number'].isin(sensors_bad)]
    if(len(sensors_good)==0):
        print('No controllable sensors, exiting')
        return ['<div class="alert alert-danger" role="alert">No controllable sensors, exiting</div>']

    #optimize setpoint schedule
    best_fb,sp_new,best_time_start,best_time_end,best_warmup_time = sp_opt_main(df_good,sensors_good,fb_curr,sp_curr,sp_start,sp_end,occ_start,occ_end,comf_temp_min,comf_temp_max,mode)
    sp_change = sp_new-sp_curr

    #add predicted comfort values after optimization
    comf_data_new = sp_improved_data(df_good,data,sp_curr,sp_change,best_warmup_time,best_time_start,best_time_end)
    comf_data_new = add_comfort(comf_data_new,comf_temp_min,comf_temp_max)
    s_df['Comfort New'] = s_df['Comfort']
    for sensor in sensors_good:
        dfi = comf_data_new[comf_data_new['Sensor Number']==sensor]
        dfi = get_data_between_time(dfi,occ_start,occ_end)
        if(len(dfi)==0):
            continue
        comf = round(len(dfi[dfi['Comfort']==1])*100/len(dfi),2)
        s_df.loc[s_df['Sensor Number']==sensor,'Comfort New'] = comf
    
    #add comfort increase info
    s_df.loc[(~s_df['Comfort New'].isna()),'Comfort Inc'] = s_df['Comfort New'] - s_df['Comfort']
    s_df['Comfort Inc'] = np.round(s_df['Comfort Inc'],2)
    
    #graph current floormap
    value_column = 'Comfort'
    color_column = ''
    sensor_column = 'Sensor Number'
    #color_scale = [(0,"#EF5A45"),(0.11,"#EF5A45"),(0.11,"#EFA243"),(0.22,"#EFA243"),(0.22,"#F0E443"),(0.33,"#F0E443"),(0.33,"#D1D029"),(0.44,"#D1D029"),(0.44,"#9BCA3D"),(0.55,"#9BCA3D"),(0.55,"#5BBA47"),(0.66,"#5BBA47"),(0.66,"#47B489"),(0.77,"#47B489"),(0.77,"#208B93"),(0.88,"#208B93"),(0.88,"#0E5DA8"),(1.0,"#0E5DA8")]
    color_scale = [(0,"#EF5A45"),(0.11,"#EFA243"),(0.22,"#F0E443"),(0.33,"#D1D029"),(0.44,"#9BCA3D"),(0.55,"#5BBA47"),(0.66,"#47B489"),(0.77,"#208B93"),(0.88,"#0E5DA8"),(1.0,"#0E5DA8")]
    min_val = 0
    max_val = 100
    legend_title = 'Percent of Time in <br>Comfortable Range'
    tickvals = [0,50.0,100.0]
    ticktext = ["0%", "50%","100%"]
    black_font_start = 11
    black_font_end = 55
    hoverVarComb = []
    hovertemplate='<b>Current Setpoint Schedule</b>Sensor Number: '+s_df['Sensor Number'].astype(str)+'<br>Location: '+s_df['Location'].astype(str)+'<br>Controllability: '+s_df['Temp Control Status'].astype(str)+'<br>Current Occupant Comfort: '+s_df['Comfort'].astype(str)+'% of the occupied time<extra></extra>'
    fig = general_floormap(s_df, image, img_width, img_height, scale_factor , value_column, sensor_column, color_scale, tickvals, ticktext, legend_title, black_font_start, black_font_end, hoverVarComb, hovertemplate, min_val, max_val, 400, color_column,'Occupied Hours',sp_start,sp_end)
    #fig = general_floormap(floor,s_df, value_column, 'Sensor Number', color_scale, tickvals, ticktext, legend_title, black_font_start, black_font_end, hoverVarComb, hovertemplate, min_val, max_val,color_column=color_column,time='Occupied Hours')
    fig.update_layout(title={'text':'<b>Current Floor Comfort','y':.95,'x':0.05})

    #for controllable sensors, keep their current color, for others make them grey
    s_df['color'] = 'yellow' #default value
    s_df['font color'] = fig['data'][0]['textfont']['color']
    for i in range(len(s_df)):
        if(s_df['Temp Control'][i]!=1): #not controllable
            s_df['color'][i] = '#adadad'
            s_df['font color'][i] = 'black'
        else:
            #add color using color scale to value relation
            comf = s_df['Comfort'][i]/100
            color = 'yellow'
            for j in range(len(color_scale)):
                c = float(color_scale[j][0])
                if c >= comf:
                    color = color_scale[j][1]
                    break
            s_df['color'][i] = color

    fig.update_traces(marker={'color':s_df['color']})
    fig.update_traces(textfont_color=s_df['font color'])
    fig['data'][-1]['showlegend'] = False

    #add non-controllable sensors' color to legend as a grey circle
    fig.add_trace(go.Scatter(x=[np.NaN],y=[np.NaN],name='Non-controllable Sensors',marker={'color':'#adadad','size':60},mode='markers')) 
    fig.update_layout(legend={'yanchor':'top','y':.8})
    if fig is not None:
        r.append(fig.to_html())
        r.append('<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" data-target="#tahm_3"  >Guide on How to Read This Graph</h5><div id="tahm_3" >Locations where sensors have collected data are represented on this floorplan, with the current average percentage of time spent in acceptable occupant comfort ranges based on ASHRAE 55 standards are colour-coded according to the legend on the right-hand side. The occupied time period is building-dependent and is inputted by the user prior to performing this analysis. The target value is 100%, which means that the corresponding location was comfortable during the entire occupied time period.<p style="padding:15px;"></p></div></div>')
    #fig.show()

    #graph predicted floormap
    value_column = 'Comfort New'
    hovertemplate='<b>Optimized Setpoint Schedule</b>Sensor Number: '+s_df['Sensor Number'].astype(str)+'<br>Location: '+s_df['Location'].astype(str)+'<br>Controllability: '+s_df['Temp Control Status'].astype(str)+'<br>Current Occupant Comfort: '+s_df['Comfort'].astype(str)+'% of the occupied tim<br>Predicted Occupant Comfort: '+s_df['Comfort New'].astype(str)+'% of the occupied time<br>Predicted Comfort Increase '+s_df['Comfort Inc'].astype(str)+'%<extra></extra>'
    fig = general_floormap(s_df, image, img_width, img_height, scale_factor , value_column, sensor_column, color_scale, tickvals, ticktext, legend_title, black_font_start, black_font_end, hoverVarComb, hovertemplate, min_val, max_val, 400, color_column,'Occupied Hours',sp_start,sp_end)
    #fig = general_floormap(floor,s_df, value_column, 'Sensor Number', color_scale, tickvals, ticktext, legend_title, black_font_start, black_font_end, hoverVarComb, hovertemplate, min_val, max_val,color_column=color_column,time='Occupied Hours')
    fig.update_layout(title={'text':'<b>Predicted Floor Comfort','y':.95,'x':0.05})

    #for controllable sensors, keep their current color, for others make them grey
    s_df['color'] = 'yellow' #default value
    s_df['font color'] = fig['data'][0]['textfont']['color']
    for i in range(len(s_df)):
        if(s_df['Temp Control'][i]!=1): #not controllable
            s_df['color'][i] = '#adadad'
            s_df['font color'][i] = 'black'
        else:
            #add color from color scale to value relation
            comf = s_df['Comfort New'][i]/100
            color = 'yellow'
            for j in range(len(color_scale)):
                c = float(color_scale[j][0])
                if c >= comf:
                    color = color_scale[j][1]
                    break
            s_df['color'][i] = color

    fig.update_traces(marker={'color':s_df['color']})
    fig.update_traces(textfont_color=s_df['font color'])
    fig['data'][-1]['showlegend'] = False

    #add non-controllable sensors' color to legend as a grey circle
    fig.add_trace(go.Scatter(x=[np.NaN],y=[np.NaN],name='Non-controllable Sensors',marker={'color':'#adadad','size':60},mode='markers')) #CHANGED sp opt
    fig.update_layout(legend={'yanchor':'top','y':.8})
    #fig.show()
    if fig is not None:
        r.append(fig.to_html())
        r.append('<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" data-target="#tahm_3"  >Guide on How to Read This Graph</h5><div id="tahm_3" ><p style="padding:15px;">Locations where sensors have collected data are represented on this floorplan, with the predicted average percentage of time spent in acceptable occupant comfort ranges based on ASHRAE 55 standards are colour-coded according to the legend on the right-hand side. The occupied time period is building-dependent and is inputted by the user prior to performing this analysis. The target value is 100%, which means that the corresponding location was comfortable during the entire occupied time period.</p></div></div>')
    return  r


#using try for testing purposes, where there may not be sensor coordinates or floormap for all datafiles
def get_data_any_type(df_iot,tz_name=''): 
    '''
    Read data and format it as needed.
    Parameters:
        fileName (string): Name of the csv file to be read (include the file extension).
        tz_name (strnig): If the timezone of the "time" column is different than the timezone of the building, 
                        specify the timezone special name to convert it to that. Example: US/Central for CST time.
    Return:
        df_iot (dataframe): Formatted dataframe containing all the sensors' data.
        df_tph (dataframe): Formatted dataframe containing data for sensors that have temperature, RH, and pressure reading.
        df_iaq (dataframe): Formatted dataframe containing data for sensors that have CO2 and TVOC reading.
    '''

    # df_iot = pd.read_csv(fileName,header=2)
    # if 'time' not in df_iot: #raw file
    #     df_iot = pd.read_csv(fileName,header=1) 
    #     if 'time' not in df_iot:
    #         df_iot = pd.read_csv(fileName) #formatted data file


    df_iot['TimeStamp'] = df_iot['TimeStamp'].str.replace(r'\(.*\)','',regex=True) #remove (CST) etc text from time column
   
    df_iot['TimeStamp'] = pd.to_datetime(df_iot['TimeStamp'])

    #handle time zone
    if(tz_name!=''):
        df_iot['TimeStamp'] = df_iot['TimeStamp'].dt.tz_convert(tz=tz_name)
    df_iot['TimeStamp'] = df_iot['TimeStamp'].dt.tz_localize(None)

    
    if ('TVOC-Level' in df_iot) and ('TVOC' in df_iot): #Merge IAQ columns with different names
        df_iot['TVOC'].fillna(df_iot['TVOC-Level'], inplace=True)
        df_iot['CO2'].fillna(df_iot['CO2-Level'],inplace=True)
    elif 'TVOC-Level' in df_iot:
        df_iot = df_iot.rename(columns={'TVOC-Level': 'TVOC'})

    if 'CO2' not in df_iot:
        df_iot['CO2'] = np.nan


    df_iot = df_iot.rename(columns={'epName': 'Sensor Number'})
    df_iot['Sensor Number'] = df_iot['Sensor Number'].astype(str)

    if 'Floor' in df_iot:
        df_iot['Floor'] = df_iot['Floor'].astype(str)#final_df only

    #Keep only needed columns
    columns_keep = ['TimeStamp', 'Sensor Number', 'CO2', 'Humidity', 'Pressure', 'TVOC', 'Temperature','Comfort','Floor','Location','Notes','Perimeter']
    #df_iot = df_iot[columns_keep]
    df_iot = df_iot.loc[:,df_iot.columns.isin(columns_keep)]


    #Convert the Pressure measurement to kPa
    if 'Pressure' in df_iot.columns:
        df_iot.loc[df_iot['Pressure']>300,'Pressure']/=10

    df_iot = df_iot.sort_values(by='TimeStamp')
    df_iot = df_iot.set_index(['TimeStamp'])
    # if(date_start != ''):
    #     df_iot['Date'] = df_iot['TimeStamp'].dt.strftime('%Y-%m-%d')
    #     df_iot = df_iot[df_iot['Date']>=date_start]
    df_iot = cutoff(df_iot)

    df_tph = df_iot[df_iot['Temperature'].notna()]
    df_iaq = df_iot[df_iot['CO2'].notna()]
    
    return df_iot,df_tph,df_iaq


#####################################################################################################
def optimal_setpoint_requests(request,id):
    current_task = Task.objects.get(id=id)
    floor = request.POST.get("floor",None)
    mode= 'Auto'
    width= request.POST.get("width","0")
    days= request.POST.get("days",None)
    pmvmax= request.POST.get("pmv",None)
    pmvmin = None
    temp_comfort = request.POST.get("temp_comfort",None)
    sp_start=current_task.weekday_temp_occupied_start
    sp_end=current_task.weekday_temp_occupied_end
    min_temp = request.POST.get("min_temp",None)
    max_temp= request.POST.get("max_temp",None)
    if temp_comfort == "ashrae":
        final_df= load_csv(current_task.building.id,id,"final_df.csv")
        comf_temp_min,comf_temp_max= get_comf_temo_min_max(final_df)
        pmvmin=-1
        pmvmax=1
        min_temp= comf_temp_min
        max_temp=comf_temp_max
    elif temp_comfort == "pmv_level":
        pmvmax = int(pmvmax)
        pmvmin = -1*pmvmax
        min_temp=0
        max_temp=0
    else:
        pmvmax=1
        pmvmin=-1


    if width:
        width=int(width)
   
    if days:
        days= json.loads(days)
    else:
        days=['Mon','Tue','Wed','Thu','Fri']
  

    final_df= process_file(current_task)
    #
    co_df,img,img_width,img_height,scale_factor,wk_start,wk_end=get_sensors_images(current_task.building.id,id,floor,width)
    co_df=co_df.rename(columns={'snsr_num':'Sensor Number'})
    setpoint_temp = float(str(current_task.weekday_occupied_temperature))
    fallback_temp =float(str(current_task.weekday_unoccupied_temperature))
    return floor,final_df,co_df,img, img_width, img_height, scale_factor,fallback_temp,setpoint_temp,sp_start,sp_end,wk_start,wk_end,pmvmin,pmvmax,min_temp,max_temp,days,mode

def process_file (current_task):
    # if floor and mode:
    dataFile= load_csv(current_task.building.id,current_task.id,"IoT.csv")
    df_iot_base, df_tph_base, df_iaq_base = get_data_any_type(dataFile)
    df_iot_base=df_iot_base.reset_index()
    allSensors = df_iot_base["Sensor Number"].unique()
    allSensors = np.sort(allSensors)
    df_tph_base=df_tph_base.reset_index()

    badSensors_lowReadings=[]
    sensors_readings = df_iot_base.groupby(['Sensor Number']).size()
    sensors_readings = pd.concat([sensors_readings],axis=1).reset_index()
    for i in range(len(sensors_readings)):
        if sensors_readings[0][i] < min(sensors_readings[0].mean()*0.5,300):
            badSensors_lowReadings.append(sensors_readings['Sensor Number'][i])
 

    #don't use sensors with low number of readings
    usedSensors = [sensor for sensor in allSensors if sensor not in badSensors_lowReadings]

    df_tph = df_tph_base[df_tph_base['Sensor Number'].isin(usedSensors)]

    df_tph['TimeStamp'] = pd.to_datetime(df_tph['TimeStamp'])

    #handle timezone
    #df_tph['TimeStamp'] = df_tph['TimeStamp'].dt.tz_convert(tz='US/Central')
    df_tph['TimeStamp'] = df_tph['TimeStamp'].dt.tz_localize(None)

    df_tph['Date'] = df_tph['TimeStamp'].dt.strftime('%Y-%m-%d')
    df_tph['Date'] = pd.to_datetime(df_tph['Date'])
    df_tph.index = df_tph['TimeStamp']
    df_tph['Time_of_day']=df_tph['TimeStamp'].dt.strftime("%H:%M")
    df_tph['Hours']=pd.to_datetime(df_tph['TimeStamp']).apply(lambda t: t.replace(minute=0))
    df_tph['Hours'] = df_tph['Hours'].dt.strftime('%Y-%m-%d %H:00') 
    #get placement file if possible
    try:
        query = SensorPlacement.objects.filter(task_id=current_task.id).values("snsr_num","snsr_type","floor",'location','perimeter','notes')
        equipment = pd.DataFrame(list(query)) 
         
        pl_dict = {'snsr_num':'Sensor Number', 'floor':'Floor','perimeter':'Perimeter','location':'Location','notes':'Notes'}
        equipment.rename(columns=pl_dict,inplace=True)

        #add placement info to data  
        final_df = pd.merge(df_tph,equipment,on='Sensor Number',how='left')
        # floors = final_df['Floor'].unique()

    except:
        print('no placement file found')
        final_df = df_tph
        final_df['Location'] = final_df['Sensor Number']
    return final_df

def general_barplot_opt(x, y, xaxis_label='', yaxis_label='', texttemplate='', hoverVarComb=[], hovertemplate='', yrange=[], ticksuffix='',ticktext=[], tickvals=[],time='NaN'):
    '''
    Makes a barplot with the specified properties and returns the corresponding figure object.
    Parameters: 
        x (list): List containing the names of the bars.
        y (list): List containig the values of the bars.
        xaxis_label (string): Title of the horizontal axis.
        yaxis_label (string): Title of the vertical axis.
        texttemplate (string): Format of the text to show inside each bar.
        hoverVarComb (multi-dimensional array): custom data to use for hover text (for hovetemplate).
        hovertemplate (string): The format of the text to show when hovering over the bars.
        yrange (2-element list): List containing the min and max value of the y axis.
        ticksuffix (string): Specifies the text to display beside the y values in the yaxis, bar text, and hover text.
        ticktext (list): List containing custom labels to show for the yaxis.
        tickvals (list): At which values on the yaxis to show the items in ticktext.
        time (string): Time period to display as text.
    Returns:
        fig: figure object with the specified properties.
    '''

    fig = go.Figure()

    
    if(texttemplate!= ''): #add bar with text
        fig.add_bar(
            x=x, 
            y=y, 
            text=y.astype(str),
            textposition='inside', texttemplate = texttemplate, showlegend=False,textangle=0
        )
    else:
        fig.add_bar(x=x, y=y,textangle=0)
    
    fig.update_layout({
    'plot_bgcolor': 'white',
    'paper_bgcolor': 'white',
    })
        

    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7')
    fig.update_yaxes(title_text=yaxis_label)
    fig.update_xaxes(title_text=xaxis_label)
    fig.update_traces(marker_color='#065ba7')
    
    if(len(ticktext)!=0 and len(tickvals)!=0):
        fig.update_yaxes(ticktext=ticktext, tickvals=tickvals)
        #fig.update_layout(showlegend=False)
        fig.add_bar(x=x,y=y,yaxis='y2',texttemplate = texttemplate,showlegend=False,textangle=0)#marker=dict(color='rgba(0,100,200,1)')
        fig.update_layout(yaxis2=dict(range=yrange,showticklabels=False))
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7')
        fig.update_traces(marker_color='#065ba7')
        


    fig.update_traces(customdata = hoverVarComb, hovertemplate=hovertemplate)
   

    if(len(yrange)!=0):
        fig.update_layout(yaxis_range=yrange)

    fig.update_yaxes(ticksuffix=ticksuffix)

    #display small values outside the bar so it fits
    if(len(y)>1): #CHANGED SP OPT
        textposition_list = []
        e_max = y.max()
        e_outside = e_max*.15
        for e in y: 
            if(e<=e_outside):
                textposition_list.append('outside')
            else:
                textposition_list.append('inside')

        fig.update_traces(textposition=textposition_list)

    if(time!=''):#CHANGED SP
        timeText = get_occupancy_text(time,10)
        fig = add_legend_text(fig,timeText)
    
    if(xaxis_label=='Date'):
        fig.update_xaxes(tickangle = 0)
    else:
        fig.update_xaxes(tickangle = 90)
        
    fig.update_layout(margin={'t':20, 'b':25})
    return fig