import dateutil.parser
from analysis.data_analysis_library import *
from placements.models import *
from analysis.common import *
from io import StringIO
from tasks.models import *
import datetime
import shutil
import  reports.report as report_class
class AnalyzeData:
    def __init__(self,tb_id,versionId):
        '''
        Gets IAQ and IEQ data that's been processed and has weather and placement information added,
        and adds time of day, comfort, and setpoint info to it, and saves it in AWS.
        Parameters:
            tb_id (int): building Id
            versionId (): task id
        '''               
        task_entry = Task.objects.get(id=versionId)        
        wk_start = str(task_entry.weekday_occupied_start)
        wk_end = str(task_entry.weekday_occupied_end)
        wek_start = str(task_entry.weekday_unoccupied_start)
        wek_end = str(task_entry.weekday_unoccupied_end)   
        final_df,iaq_df,df_tph1=self.get_merged_data(tb_id,versionId) 
        print(final_df['Unnamed: 0'])
        final_df['Time_of_day']=final_df.index.strftime('%H:%M:%S') 
        if not iaq_df.empty:     
            iaq_df['Time_of_day']=iaq_df.index.strftime('%H:%M:%S')
            self.saveOccNonData(iaq_df,wk_start,wk_end,tb_id,versionId,'iaq_df.csv','iaq_occ.csv','iaq_non_occ.csv')
        #add comfort info to data
        comf=list()
        for i in range(len(final_df)):
            if((20<=final_df['Temperature'][i]<=24) and (20<=final_df['Humidity'][i]<=60)):
                comf.append(True)
            else:
                comf.append(False)
        final_df['Comfort']=comf 
        #add setpoint info to data        
        set_point=[]
        if task_entry.setpoint ==True:
            sp_wk_occ = task_entry.weekday_occupied_temperature
            sp_wkend_occ = task_entry.weekend_occupied_temperature
            sp_wk = task_entry.weekday_unoccupied_temperature
            sp_wkend = task_entry.weekend_unoccupied_temperature  
                 
            for i in range(len(final_df)):
                if pd.to_datetime(final_df['Date'][i]).weekday()>=5:
                    if (final_df['Time_of_day'][i]>=wek_start) & (final_df['Time_of_day'][i]<=wek_end):
                         #add occupied time setpoint value
                        set_point.append(sp_wkend_occ)
                    else:
                        #add unoccupied time setpoint value
                        set_point.append(sp_wkend)
                else:#add weekday setpoint
                    if (final_df['Time_of_day'][i]>=wk_start) & (final_df['Time_of_day'][i]<=wk_end):
                         #add occupied time setpoint value
                        set_point.append(sp_wk_occ)
                    else:
                         #add unoccupied time setpoint value
                        set_point.append(sp_wk)
            final_df['Set_point']=set_point 
        #save datasets in AWS       
        self.saveOccNonData(final_df,wk_start,wk_end,tb_id,versionId,'final_df.csv','occ.csv','non_occ.csv')
        self.saveOccNonData(df_tph1,wk_start,wk_end,tb_id,versionId,'df_tph.csv','df_tph_occ.csv','df_tph_non_occ.csv')
        df_tph_occ =df_tph1.between_time(wk_start, wk_end,include_start=True, include_end=False)
        #    
        Task.objects.filter(id=versionId).update(merge_file=True,status_id=5,merge_time=datetime.datetime.now())
        # remove report
        current_location=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = current_location+"/media/"+str(task_entry.building.id)+"/"+str(versionId)+"/Report"
        if os.path.exists(file_path):
            shutil.rmtree(file_path)
        curated_report_images.objects.filter(task=task_entry).delete()
        report_class.generate_report_images(final_df,iaq_df,df_tph_occ,versionId)

        

    def get_placement_ioT_df(self,tb_id,versionId):
        '''
        Format data, add placement info, remove data of bad sensors, upsample and interpolate, and remove warmup period.
        Parameters:
            tb_id (int): building id 
            versionId (int): task id
        Returns:
            df_IAQ (dataframe): IAQ data (with CO2 values).
            df_tph (dataframe): IEQ data (with Temperature values).
        '''
        #read data 
        loT_df=load_csv(tb_id,versionId,"IoT.csv")
        #keep only the needed columns
        IoT_columns=['epName','Humidity','Pressure','Temperature','CO2','TVOC','TimeStamp','Date']
        loT_df=loT_df[IoT_columns] 
        loT_dict = {'epName': 'Sensor Number'}
        loT_df.rename(columns=loT_dict,inplace=True)
        #get placement data and rename the columns   
        query = SensorPlacement.objects.filter(task_id=versionId).values("snsr_num","snsr_type","floor",'location','perimeter','notes')
        equipment = pd.DataFrame(list(query)) 
         
        pl_dict = {'snsr_num':'Sensor Number', 'floor':'Floor','perimeter':'Perimeter','location':'Location','notes':'Notes'}
        equipment.rename(columns=pl_dict,inplace=True)
         #add hours column
        loT_df['Hours']=pd.to_datetime(loT_df['TimeStamp']).apply(lambda t: t.replace(minute=0))
        loT_df['Hours']=loT_df['Hours'].dt.strftime('%Y-%m-%d %H:00')
        #add placement info to data  
        df2=pd.merge(loT_df, equipment, on="Sensor Number",how='left')  
        #IEQ data
        #split in to IEQ (tph: temperature, pressure, humidity) and IAQ data
        df_tph = df2[df2['Temperature'].notna()] 
        df_IAQ = df2[df2['CO2'].notna()]
        #IAQ data
        if not df_IAQ.empty:  
             #format timestamp and remove seconds info              
            df_IAQ['TimeStamp']=pd.to_datetime(df_IAQ['TimeStamp'].apply(lambda x: dateutil.parser.isoparse(x).strftime('%Y-%m-%d %H:%M:00')) )
            df_IAQ = df_IAQ.sort_values(by="TimeStamp")        
            df_IAQ.set_index('TimeStamp',drop=True,inplace=True)

            #remove bad sensors' data
            df_IAQ = remove_bad_sensors(df_IAQ)        
            #upsample and interpolate data
            df_IAQ = upsample_interpolate_data(df_IAQ,equipment)
            #cutoff the start of data, to remove warmup period
            df_IAQ = cutoff(df_IAQ)
        #tph data
        #format timestamp and remove seconds info
        df_tph['TimeStamp']=pd.to_datetime(df_tph['TimeStamp'].apply(lambda x: dateutil.parser.isoparse(x).strftime('%Y-%m-%d %H:%M:00')) )
        df_tph = df_tph.sort_values(by="TimeStamp")        
        df_tph.set_index('TimeStamp',drop=True,inplace=True)        
        #remove bad sensors' data
        df_tph = remove_bad_sensors(df_tph)    
        #upsample and interpolate data
        df_tph = upsample_interpolate_data(df_tph,equipment)  
        return df_IAQ,df_tph

    def get_merged_data(self,tb_id,id):
        '''
        Get data, add weather data, interpolate, and remove warmup period.
        Parameters:
            tb_id (int): building id 
            id (int): task id
        Returns:
            data (dataframe): IEQ data containing weather data, interpolated at a frequency of 1min.
            iaq_df (dataframe): IAQ data interpolated based on sample steps (typically 5min frequency).
            df_tph1 (dataframe): IEQ data interpolated based on sample steps (typically 5min frequency).
        '''
        #get formatted and upsampled data
        iaq_df,daily =  self.get_placement_ioT_df(tb_id,id)      
        df_tph1=daily.copy()    
        weather_flag = str(Task.objects.get(id=id).weather_upload_time)
        daily['TimeStamp']=daily.index 
        daily = daily.set_index('Hours')
        startTime=daily['TimeStamp'].min()
        endTime=daily['TimeStamp'].max()
        #if we have weather data
        if weather_flag !='':             
            startDate = min(daily.index)      
            endDate=max(daily.index)
            weather_df=load_csv(tb_id,id,"Weather.csv")  
            weather_dict={'Date/Time (LST)':'Date_Hour', 'Temp (°C)':'Temperature_Outside','Rel Hum (%)':'Humidity_Outside', 'Stn Press (kPa)':'Pressure_Outside'}
            weather_df.rename(columns=weather_dict,inplace=True)
            weather=weather_df[(weather_df['Date_Hour'] >= startDate) & (weather_df['Date_Hour'] <= endDate)]
           #keep only portion of weather info that we have data for
            c_daily = weather.set_index('Date_Hour')
            merge=pd.merge(left=daily,right=c_daily, how='left', left_index=True, right_index=True)
            merge.interpolate(method='linear', inplace=True)##fill missing values using interpolate 'time' method
            merge = merge[merge['Pressure_Outside'].notna()]  
            
        else:
            merge=daily    
        merge['Floor']=merge['Floor'].astype('str')
        merge['Sensor Number']=merge['Sensor Number'].astype('str')      
        
        #interpolate and fill missing values
        data = interpolate_fill_data(merge,startTime,endTime,'1 min')
        #remove the warmup period of data
        data = cutoff(data)
        df_tph1 = cutoff(df_tph1)   
        return data,iaq_df,df_tph1

    def saveOccNonData(self,df,wk_start,wk_end,tb_id,versionId,fn1,fn2,fn3):
        """
        Save the data to orignal, occupied, unoccupied files
        Parameters:
            self: self object
            df(dataframe):data frame
            wk_start(datetime): weekday occupied start time
            wk_end(datetime): weekday occupied end time
            tb_id(int): building id
            versionId(int): task id
            fn1(string): file name --- original one's file name
            fn2(string): file name --- occupied one's file name
            fn3(string): file name --- unoccupied one's file name
        """  
        self.save_data_to_s3(df,tb_id,versionId,fn1) 

        occ =df.between_time(wk_start, wk_end,include_start=True, include_end=False)
        self.save_data_to_s3(occ,tb_id,versionId,fn2)
        
        non_occ =df.between_time(wk_end, wk_start,include_start=True, include_end=False)
        self.save_data_to_s3(non_occ,tb_id,versionId,fn3)

    def save_data_to_s3(self,df,tb_id,versionId,fn):
        """
        Save the dataframe as a file in aws server
        Parameters:
            self: self object
            df(dataframe): data frame
            tb_id(int): building id
            versionId(int): task id
            fn(string): file name
        """
        csv_buffer = StringIO()        
        df.to_csv(csv_buffer)
        key = r"{}/{}/{}".format(tb_id,versionId,fn)
        s3,s3_,bucket=get_credential() 
        s3_.Bucket(bucket).put_object(Key=key,Body=csv_buffer.getvalue())