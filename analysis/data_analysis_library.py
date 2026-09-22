import numpy as np
import pandas as pd
import datetime


def cutoff(data):
    '''
    Removes starting part of the data, to exclude warmup time from analysis.
    Parameters:
        data (dataframe): Input data.
    Returns:
        data (dataframe): Data with starting part removed.
    '''

    #remove sensors without enough readings
    d=data.groupby(['Sensor Number']).size() 
   
    d=pd.concat([d],axis=1).reset_index()
    ###if it is less than 50% of the mean count we remove those sensors
    badSens=[]
    for i in range(len(d)):
        if d[0][i] < (d[0].mean()*0.5):
            badSens.append(d['Sensor Number'][i])

    # data.index = data['TimeStamp']
    time=[]### store change points
    sensor=data['Sensor Number'].unique() ### number of sensors
    sensor = [s for s in sensor if s not in badSens]
    for i in sensor:
        dd11=data[data['Sensor Number']==i]
        x = np.array(range(0, dd11.shape[0]))
        x_hat = np.linspace(x.min(), x.max(), 100)
        breaks=x_hat[1:2]
        time.append(dd11.iloc[breaks.astype('int')].index)
    dt=max(time).item()
    dt = pd.to_datetime(dt, format='%Y-%m-%d %H:%M:%S')
    resolution=60
    new_minute = (dt.minute // resolution + 1) * resolution
    a = dt + datetime.timedelta(minutes=new_minute - dt.minute)
    data = data[data.index > a]
   
    return data
	
	
#use for df_iaq, df_tph
def upsample_interpolate_data(data, equipment):
    '''
    Finds sampling time of the dataset (if cannot find it, uses default value of 5min),
    then resamples it to the sampling rate then interpolates for values that may have skipped, and adds placement info. (used for df_iaq, df_tph)
    Parameters:
        data (dataframe): Data.
        equipment (dataframe): Contains sensor placement info.
    Returns:
        df (dataframe): Upsampled and interpolated data with placement info.
    '''
    sensors_data = data['Sensor Number'].unique()
    default_sample_steps = 5
    try:#try finding sampling steps
        #finds difference between consecutive values
        data['timeDelta'] = data.index.to_series().diff()
        sampling_time = data['timeDelta'].mode()[0]
        sampling_time_minute = round(sampling_time.seconds /60)
        sample_steps = sampling_time_minute
        if(sample_steps <= 0):#use default value if couldnt find a valid value
            sample_steps = default_sample_steps
        data = data.drop(columns=['timeDelta'])
    except:
        print('Error finding sample_steps, using default value of 5.')
        sample_steps = default_sample_steps
    #sample_steps = default_sample_steps

    #go through data of each sensor and upsample and interpolate it
    df = pd.DataFrame()
    for sensor in sensors_data:
        df_i = data[data['Sensor Number'] == sensor]
        if((len(df_i) == 0)):
            print("Error, data size shouldn't be 0.")
            continue
            
        #df_i = upsample_iterpolate1(df_i, sample_steps)
        upsampled = df_i.resample(str(sample_steps)+'T').mean()
        df_i = upsampled.interpolate(method='linear')
        
        df_i['Sensor Number'] = sensor
                
        df = df.append(df_i)
        
        
    df = df.reset_index()
    #add additional columns and add placement info
    df['Hours']=df['TimeStamp'].apply(lambda t: t.replace(minute=0))
    df['Hours']=df['Hours'].dt.strftime('%Y-%m-%d %H:00')
    df['Date'] = df['TimeStamp'].dt.strftime('%Y-%m-%d')
    df = pd.merge(df, equipment, on="Sensor Number",how='left')
    
    df.set_index('TimeStamp',drop=True,inplace=True)
    return df






def remove_bad_sensors(data):
    '''
    Removes data of sensors that have low number of readings.
    Parameters:
        data (dataframe): Data.
    Returns:
        data (dataframe): Data with bad sensors' data removed.
    '''
    dd=data.groupby(['Sensor Number']).size() 
    dd=pd.concat([dd],axis=1).reset_index()
    ###if it is less than 50% of the mean count we remove those sensors
    remv=[]
    for i in range(len(dd)):
        if dd[0][i] < (dd[0].mean()*0.5):
            remv.append(dd['Sensor Number'][i])
    data=data[~data['Sensor Number'].isin(remv)]
    return data
	
	
#use for final_df
def interpolate_fill_data(data,start,end,freq='1 min'):
    '''
    Interpolate and fill data by merging it with an empty dataset that consists of only times and interpolating missing values.
    Parameters:
        data (dataframe): Data.
        start (timestamp): When the data should start.
        end (timestamp): When the data should start.
        freq (string): What to set the data's frequency to.
    Returns:
        final_df (dataframe): Interpolated and filled data. 
    '''
    data.interpolate(method='linear', inplace=True)##fill missing values using interpolate 'time' method
    t_data=data.set_index('TimeStamp') # here df2 is final merge data set. here I have created time series data set using that df2   
    
    time=pd.DataFrame({'TimeStamp': pd.date_range(start=start, end=end, freq=freq)})
    time=time.set_index('TimeStamp')    
    
    final_df = pd.DataFrame() #create empty dataset
    ##loop to create sub dataframes for each sensor
    un_sort_list =t_data['Sensor Number'].unique()       
    for i in sorted(un_sort_list): 
        sens=t_data[t_data['Sensor Number']==i] 
        new=pd.merge(left=time,right=sens, how='left', left_index=True, right_index=True)#left merge time dataset with sensor dataframe  
        new = new[~new.index.duplicated(keep='first')]
        new.interpolate(method='time', inplace=True)##fill missing values using interpolate 'time' method
        new=new.ffill() ##fill character values using forward fill
        final_df=final_df.append(new)##append datasets of each sensor to the final_df  
    final_df = final_df[final_df['Sensor Number'].notna()]
    return final_df