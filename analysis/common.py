from accounts.credential import *
import pandas as pd
from PIL import Image
from placements.models import SensorMapping
import plotly.offline as opy
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from tasks.models import Task
import scipy.cluster.hierarchy as hac
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from os.path import dirname

def load_df(buildingId,v_id,name):
    """
    Get file from AWS server
    Parameters:
        buildingId(int): building id
        v_id(int): task id
        name(str): file name
    Return:
        df: the file as dataframe format
    
    """
    s3,s3_,bucket=get_credential()  # connect the asw server
    key = r"{}/{}/{}".format(buildingId, v_id,name)    #format eg. buildingId/taskId/fileName
    obj = s3.get_object(Bucket=bucket, Key=key)
    df =pd.read_csv(io.BytesIO(obj['Body'].read())) #read the file as df
    df=df.set_index('TimeStamp') # set the time stamp as a index
    df=df[df['Floor'].notna()] #get all floors that have data
    df['Floor']=df['Floor'].astype(int).astype(str)#convert floor column as string type
    df['Sensor Number']=df['Sensor Number'].astype(str)# conver the sensor number column as string type
    return df
    

def load_csv(buildingId,v_id,name):
    '''
    Read .csv file from AWS server
    Parameters:
       buildingId(int): building id
       v_id(int): task id
       name(string): file name
    Returns:
		 df: the file as dataframe format
    '''
    s3,s3_,bucket=get_credential()  
    key = r"{}/{}/{}".format(buildingId, v_id,name)    
    obj = s3.get_object(Bucket=bucket, Key=key)
    df =pd.read_csv(io.BytesIO(obj['Body'].read()))
    return df


def put_df_to_s3(buildingId,v_id,name,data):
    """
    Generate the s3 bucket for uploading file
    Parameters:
        buildingId(int): building Id
        v_id(int): task id
        name(string): file name
        data(dataframe): the actualy file
    Returns:
        s3 bucket message that indicate the stauts of the file
    """
    s3,s3_,bucket=get_credential()  
    key = r"{}/{}/{}".format(buildingId, v_id,name)    
    return s3_.Bucket(bucket).put_object(Key=key,Body=data)

def get_link_from_s3(buildingId,v_id,name):
    """
    Get the download link for existing file 
    Parameters:
        buildingId(int): building Id
        v_id(int): task id
        name(string): file name
    Returns:
        a link if the file exists or '' if it is not
    """
    s3,s3_,bucket=get_credential()  
    key = r"{}/{}/{}".format(buildingId,v_id,name)
    try:
        s3_.Object(bucket, key).load()
        return s3.generate_presigned_url("get_object", Params={'Bucket': bucket,'Key':key}, ExpiresIn=3600)
    except:
        return ''


def put_link_to_s3(buildingId,v_id,name):
    """
    Generate the link for upload file to aws server
    Parameters:
         buildingId(int): building Id
         v_id(int): task id
         name(string): file name
    Returns:
         a link for uploading a file
    """
    s3,s3_,bucket=get_credential()  
    key = r"{}/{}/{}".format(buildingId,v_id,name)
    return s3.generate_presigned_url("put_object", Params={'Bucket': bucket,'Key': key}, ExpiresIn=3600)

#get the dictionary of the location data from final.df
#final_df: data in dataframe format
#return location data in object type and a list
def get_loc_dic(final_df):
    locations=final_df['Location'].unique() # get a list of the unique lcoation data
    locations = [x for x in locations if str(x) != 'nan']#remove the nan value
    loc_full={}
    for x in locations:
        loc_full['{0}'.format(x)] = final_df[(final_df['Location']==x)]
    return loc_full,locations


def config_setting(file_name):
    """
    configure setting for image
    Parameters:
        file_name(string):file name
    Returns:
         configure setting in object 
    """   
    config = {
        'toImageButtonOptions': {
            'format': 'png', # one of png, svg, jpeg, webp
            'filename': file_name,            
            'scale': 1 # Multiply title/legend/axis/canvas sizes by this factor
        }}   
    return config

#General graph functions
#floor map containing scatter values of sensors
def general_floormap(s_df, image, img_width, img_height, scale_factor , value_column, sensor_column, color_scale, tickvals, ticktext, legend_title, black_font_start, black_font_end, hoverVarComb, hovertemplate, min_val, max_val, legend_length=400, color_column='',time='NaN',wk_start='',wk_end=''):
    '''
    Returns a figure object that shows each sensor represented as a point on the given image
    that is colored based on its value.
        Parameters: 
            s_df (dataframe): Contains the sensor numbers, values, coordinates, and other things needed to make the floormap.
            image (string): The floor's image path from Building Images
            img_width (float): The floor's width. 
            img_height (float): The floor's height. 
            scale_factor (float): For scaling the size of the graph.
            value_column (string): Name of the column in s_df that contains the values.
            sensor_column (string): Name of the column in s_df that contains the sensor numbers.
            color_scale (list): List of (start_portion,color) pairs specifying legend's colors and at which in the legend each color starts.
            tickvals (list): List specifying at which values color change occurs for the sensors.
            ticktext (list): List containing the text to show at each tickval in the legend.
            legend_title (text): title of the color bar
            black_font_start (float): Starting from this value, the sensor names are displayed in black in their circle (before this value: in white).
            black_font_end (float): After this value, the sensor names are displayed in white.
            hoverVarComb (multi-dimensional array): custom data to use for hover text (for hovetemplate).
            hovertemplate (string): The format of the text to show when hovering over the sensors.
            min_val (float): Min legend value.
            max_val (float): max legend value.
            legend_length (int): How long (height) the legend is, default = 400
            colors_column (string): Name of the column containing the colors to be used instead of value_list.
            time (string): Time period to display as text.
            wk_start (string): Time when occupancy starts.
            wk_end (string): Time when occupancy ends.
        Returns:
            fig: figure object with the specified properties.
    '''
     #add time period text to legend title
    timeText = get_occupancy_text(time,wk_start,wk_end,15*scale_factor)
    legend_title = legend_title + '<br>' + timeText 
    #make figure
    fig = go.Figure() 
    #add the sensors on the floor plan
    fig.add_trace(go.Scatter(x=s_df['x'] * scale_factor,y=s_df['y'] * scale_factor, text=s_df[sensor_column].astype(str),textposition="middle center",textfont_size=15*scale_factor,
            mode="markers+text",marker={'size':53*scale_factor,'cmax':max_val,'cmin':min_val,'color':s_df[value_column],#set color equal to a variable
             'colorscale':color_scale,'showscale':True,'colorbar':{'title':legend_title,'tickvals':tickvals,'thickness':40*scale_factor,'titlefont': {'size':18* scale_factor},
            'ticktext':ticktext,'ticks':'outside','lenmode':"pixels", 'len':legend_length*scale_factor,'tickfont_size':15* scale_factor} }, marker_opacity=1,))    
    col=list()    
    #color of each sensor is based on color_column's values, not value_column's values
    if(color_column!=''):
        fig.update_traces(marker={'color':s_df[color_column]})           
        for i in s_df[color_column].values: 
            if i<=black_font_start or i>=black_font_end:#set color inside each circle to white
                col.append('white')
            else:#set the color inside each circle to black
                col.append('black')
    #color of each sensor is based on value_list column
    else:
        for i in s_df[value_column].values: 
            if i<=black_font_start or i>=black_font_end:
                col.append('white') #set color inside each circle to white
            else:#set the color inside each circle to black
                col.append('black') 
    # Configure axes
    fig.update_xaxes(visible=True, range=[0, float(str(img_width)) * scale_factor],showgrid=False,showticklabels=False)
    fig.update_yaxes(visible=True,range=[0,float(str(img_height)) * scale_factor], scaleanchor="x",showgrid=False,showticklabels=False)
    # Add floormap image
    fig.add_layout_image({
            'x':0,'sizex':float(str(img_width)) * scale_factor,'y':float(str(img_height)) * scale_factor,'sizey':float(str(img_height)) * scale_factor,
            'xref':"x",'yref':"y",'opacity':1.0,'layer':"below",'sizing':"stretch",'source':Image.open(image)})
    #update hover and circles' text font color
    fig.update_traces(customdata=hoverVarComb,hovertemplate=hovertemplate,textfont_color=col)
   #set margines and dimensions
    fig.update_layout(width=float(str(img_width)) * scale_factor, height=float(str(img_height)) * scale_factor,margin={"l": 0, "r": 0, "t": 0, "b": 0},template="plotly_white")
    return fig

#CHANGED
def general_barplot(x, y, xaxis_label='', yaxis_label='', texttemplate='', hoverVarComb=[], hovertemplate='', yrange=[], ticksuffix='',ticktext=[], tickvals=[],time='',wk_start='',wk_end=''):
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
        wk_start (string): Time when occupancy starts.
        wk_end (string): Time when occupancy ends.
    Returns:
        fig: figure object with the specified properties.
    '''
    fig = go.Figure()
    if(texttemplate!= ''): #add bar with visible text in it
        fig.add_bar(x=x, y=y, text=y.astype(str), textposition='inside', texttemplate = texttemplate, showlegend=False,textangle=0)
    else:#add bar without a visible text
        fig.add_bar(x=x, y=y,textangle=0)
    #set properties
    fig.update_layout({'plot_bgcolor': 'white', 'paper_bgcolor': 'white',},margin={'t':20, 'b':25})
    fig.update_traces(customdata = hoverVarComb, hovertemplate=hovertemplate,marker_color='#065ba7')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7',title_text=yaxis_label) 
     #if want to use custom text in the yaxis, add it using a secondary y axis 
    if(len(ticktext)!=0 and len(tickvals)!=0):
        fig.update_yaxes(ticktext=ticktext, tickvals=tickvals)        
        fig.add_bar(x=x,y=y,yaxis='y2',texttemplate = texttemplate,showlegend=False,textangle=0)#marker=dict(color='rgba(0,100,200,1)')
        fig.update_layout(yaxis2=dict(range=yrange,showticklabels=False))
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7')
        fig.update_traces(marker_color='#065ba7')
        fig.update_traces(hovertemplate=hovertemplate)   
    #if range of yaxis is specified, set it     
    if(len(yrange)!=0):
        fig.update_layout(yaxis_range=yrange)   

    #Display dates horizontally on xaxis, otherwise xaxis label is vertical
    if(xaxis_label=='Date'):
         #display text of xaxis text horizontally and format it, if it's date
        fig.update_xaxes(tickangle = 0)
        fig.update_xaxes(dtick='D',tickformat="%a<br>%b %d") 
    else:
        #display xaxis text vertically
        fig.update_xaxes(tickangle = 90)
    #add the suffix for displayed values
    fig.update_yaxes(ticksuffix=ticksuffix)
     #display small values outside the bar so they fit
    textposition_list = []
    e_max = y.max()
    e_outside = e_max*.15
    for e in y: 
        if(e<=e_outside):
            textposition_list.append('outside')
        else:
            textposition_list.append('inside')
    fig.update_traces(textposition=textposition_list)
   #if time period is given, add it to the legend
    if(time!=''):
        timeText = get_occupancy_text(time,wk_start,wk_end,10)
        fig = add_legend_text(fig,timeText)

    
    return fig

#CHANGED
def general_graph_overtime(x, y, xaxis_label='', yaxis_label='', hoverVarComb=[], hovertemplate='', color='#065ba7', legendName ='', yrange = [], ticksuffix=''):
    '''
    Returns a figure object containing a line (over time) of the given data.
    Parameters:    
        x (list): Values of the location of the points in the horizontal axis.
        y (list): Values of the location of the points in the vertical axis.
        xaxis_label (string): Title of the horizontal axis.
        yaxis_label (string): Title of the vertical axis.
        hoverVarComb (multi-dimensional array): custom data to use for hover text (for hovetemplate).
        hovertemplate (string): The format of the text to show when hovering over the graphed line.
        color (string): Color of the graphed line (hexadecimal web color code)
        legendName (string): Graph's legend title.
        yrange (list): List of two elements corresponding to the min and max values of the y axis.
        ticksuffix (string): Specifies the text to display beside the y values in the yaxis and hover text.
    Returns:
        fig: figure object with the specified properties.
    '''

    #make the figure with specified properties
    fig=px.line(x=x, y=y)
    fig.update_xaxes(title_text=xaxis_label)
    fig.update_yaxes(title_text=yaxis_label)    
    fig.update_traces(customdata=hoverVarComb, hovertemplate=hovertemplate)
    #if legend title specified, add it
    if(legendName!=''):
        fig.data[-1].name = legendName
        fig.data[-1].showlegend = True
        fig.data[-1]['line']['color'] = color    
    fig.update_layout({'plot_bgcolor': 'white','paper_bgcolor': 'white',},margin={'t':20, 'b':25})    
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7',ticksuffix=ticksuffix)
    fig.update_traces(marker_color=color) 
    #if range of yaxis is specified, set it 
    if(len(yrange)!=0):
        fig.update_layout(yaxis_range=yrange)    
    #if xaxis is date, format it
    if(xaxis_label=='Date'):
        fig.update_xaxes(dtick='D',tickformat="%a<br>%b %d")
    return fig

#CHANGED
def general_graph_overtime_multiline(data, filterVar, items, x_column, y_column, hovertemplate, name_item, xaxis_label, yaxis_label, lineWidth=1, customdata = [], ticksuffix=''):
    '''
    Returns a figure object containing lines (over time) correpsonding to each specified item.
    Parameters: 
        data (dataframe): data containig the information to be graphed.
        filterVar (string): The column name by which each item is distinguished (example: Sensor Number).
        items (list): List containng all the items for which a line is to be drawn (example: list of sensors).
        x_column (string): The column to use as the x values of the lines. 
                           Empty string means use the index.
                           'Time_of_day' means group values by each hour's average (used for avg_hour_temp)
                           'TimeStampGrouped' means group by index and take mean. (used for pressure over time)
        y_column (string): The column to use as the y values of the lines.
        hovertemplate (string): The format of the text to show when hovering over the graphed line.
        name_item (string): Text to put before each sensor's name for the items in the legend
        xaxis_label (string): Title of the horizontal axis.
        yaxis_label (string): Title of the vertical axis.
        lineWidth (int): The thickness of each graphed line.
        customdata (list): list of column names of "data" to use as custom data for the hovertemplate.
        ticksuffix (string): Specifies the text to display beside the y values in the yaxis and hover text.
    Returns:
        fig: figure object with the specified properties.
    '''
    #if plotting pressure vs time graph, custom data is occupancy times
    if(x_column=='TimeStampGrouped'): 
        occ_start = customdata[0]
        occ_end = customdata[1]
        customdata = ['Time Period']
    
    fig=go.Figure()  
    #go through each item and make a line for each
    for i in items:
        #filter data to this item
        df = data[data[filterVar] == i]
        if(x_column=='Time_of_day'):#if graphing average temperature during a day (avg_plot)
            #group by each time of day
            df = df.groupby(x_column).mean()
            df = df.reset_index()
        elif(x_column=='TimeStampGrouped'):#group by timestamp, used for pressure over time
            df = df[y_column].groupby(df.index).mean()
            df = pd.concat([df], axis=1).reset_index()
            df[y_column] = round(df[y_column],2)
            df = df.rename(columns={'TimeStamp':'TimeStampGrouped'})
            #add column that states the time period of each row, to add to hover
            df = add_time_period_col(df,'TimeStampGrouped',occ_start,occ_end)

        if(x_column != ''):#x values are not in index
            fig.add_trace(go.Scatter(x=df[x_column], y=df[y_column],hovertemplate=hovertemplate, customdata=df[customdata],
                                     name=name_item+str(i), line={'shape':'linear','width':lineWidth}))
        else: #use index values
            fig.add_trace(go.Scatter(x=df.index, y=df[y_column],hovertemplate=hovertemplate, customdata=df[customdata],
                                 name=name_item+str(i), line={'shape':'linear','width':lineWidth}))        
    fig.update_xaxes(title_text=xaxis_label)
    fig.update_yaxes(title_text=yaxis_label,ticksuffix=ticksuffix)   
    fig.update_layout({'plot_bgcolor': 'white','paper_bgcolor': 'white',},legend= {'itemsizing': 'constant'},margin={'t':20, 'b':25})    
    #if xaxis is date, format it
    if(xaxis_label=='Date'):
        fig.update_xaxes(dtick='D',tickformat="%a<br>%b %d") 
    
    return fig

#CHANGED
def plot_add_box(fig, x0, y0, x1, y1, outlineColor = "lightgreen", fillColor="lightgreen", opacity=1):
    '''
    Adds a rectangular box to the given figure and returns the updated figure object.
    Parameters: 
        fig: Figure to add the rectangle to.
        x0: x value of the lower left corner of the rectangle.
        y0: y value of the lower left cornder of the rectangle.
        x1: x value of the upper right corner of the rectangle.
        y1: y value of the upper right corner of the rectangle.
        outlineColor (string): string specifying the color of the sides of the rectangle.
        fillColor (string): string specifying the color of the inside of the rectangle.
        opacity (float, 0 to 1): specifies transparency level of the rectangle.
    Returns: 
        fig: figure object with the specified properties.

    '''
    fig.add_shape(type='rect', xref='x', yref='y', x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color=outlineColor, width=1),
                 fillcolor=fillColor, opacity=opacity,layer='below')
    return fig
	
	
def plot_add_dotted_line(fig, x, y, name, hovertemplate, hoverVarComb = [], color='black', width=3, secondary_y=False):    
    '''
    Adds a dash-dotted line to the given figure and returns the updated figure object.
    Parameters: 
        fig: Figure to add the new line to.
        x (list): the x coordinate of the points to be plotted (to form a line).
        y (list): the y coordinate of the points to be plotted.
        name (string): name of the new line in the legend.
        hovertemplate (string): The format of the text to show when hovering over the graphed line.
        hoverVarComb (multi-dimensional array): custom data to use for hover template.
        color (string): color of the new line.
        width (int): width of the new line.
        secondary_y (boolean): Whether to add this line to the secondary yaxis or not.
    Returns:
        fig: updated figure object with the new line added.
    
    '''
    if(secondary_y == False):#add to main yaxis
        fig.add_trace(go.Scatter(x=x, y=y, name=name, hovertemplate=hovertemplate,customdata=hoverVarComb,
                                line={'color': color, 'width': width, 'dash': 'dashdot'}))
    else:#add to secondary y axis
        fig.add_trace(go.Scatter(x=x, y=y, name=name, hovertemplate=hovertemplate,customdata=hoverVarComb,
                                line={'color': color, 'width': width, 'dash': 'dashdot'}),secondary_y=secondary_y)
    return fig

def get_temp_differential_figure(data, x_column, y_column, hovertemplate, category_orders, rounding=1, ticksuffix='', custom_data=[], yrange=[]):
    '''
    Make and return fig object for temperature differential barplot.
    Parameters:
        data (dataframe): Contains type of spaces and their associated values (percentage of time).
        x_column (string): Name of column in data that contains the spaces.
        y_column (string): Name of column in data that contains the values.
        hovertemplate (string): The format of the text to show when hovering over the bars.
        category_orders (dict): Contains barplot groupings.
        rounding (int): How many decimal points to round the values.
        ticksuffix (string): Unit of the barplot values.
        custom_data: Additional data needed for hover (not implemented/needed yet).
        yrange (list): Contains two elements specifying minimum and maximum yaxis range.
    Returns:
        fig (figure object): Figure with specified properties.
    '''
    fig = px.bar(data, x=x_column, y=y_column, text=round(data[y_column],rounding).astype(str)+ticksuffix,color=x_column,
                 color_discrete_sequence=["#065BA7",'#9BCA3B','#56B4E9'], facet_col="within",category_orders=category_orders,custom_data=["within"])  
    fig.update_layout({'plot_bgcolor': 'white','paper_bgcolor': 'white',},margin={'t':100, 'b':100})    
    fig.update_yaxes(ticksuffix=ticksuffix)
    fig.update_traces(hovertemplate=hovertemplate)
    fig.update_traces(textposition='outside')
    fig.update_xaxes(title= " ",showline=True, linewidth=1, linecolor='#d7d7d7',tickangle = 90)    
    #specific
    fig.update_yaxes(tick0=0)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7',showline=True, linewidth=1, linecolor='#d7d7d7',ticksuffix='%')
    if(len(yrange)!=0):
        fig.update_layout(yaxis_range=yrange)    
    return fig

#CHANGED
def general_threeVar_scatter(data, x_column, y_column, color_column,color_tickinterval, black_font_start, black_font_end, x_label='', y_label='',color_label='', hovertemplate='', custom_data=[], range_color=[], x_ticksuffix='', y_ticksuffix='', color_ticksuffix=''):
    '''
    Returns a sactter plot based on each sensor's specified features. One feature's value is displayed 
    based on x location, another based on y location, and the third based on circle's color in the graph.
    Parameters:
        data (dataframe): The values of this dataset are used.
        x_column (string): The column name of the first feature in the data.
        y_column (string): The column name of the second feature.
        color_column (string): The column name of the third feature.
        color_tickinterval (float): The distance between each tick in the color bar that respresents the color of each circle.
        black_font_start (float): circles with values larger than this and smaller than black_font_end in the color_column, will have a black text (instead of white).
        black_font_end (float): see above.
        x_label (string): Horizontal axis' title.
        y_label (string): Vertical axis' title.
        color_label (string): Color bar's label.
        hovertemplate (string): Format of the hover text.
        custom_data (list): list of column names to use as custom data in hovertemplate.
        range_color (number pair): List containing two numbers that specify the minimum and maximum range of color bar.
        x_ticksuffix (string): Text to display after each x value in the x-axis and hover.
        y_ticksuffix (string): Text to display after each y value in the y-axis and hover.
        color_ticksuffix (string): Text to dosplay after each color_column value in the color bar and hover.
    Returns:
        fig: Figure object containing the requested plot.
    '''
    labels = {}
    #set font color of each circle based on specified range
    col=list()
    for i in data.Comfort:
        if i<=black_font_start or i>=black_font_end:
            col.append('white')
        else:
            col.append('black')  
    #make figure
    fig = px.scatter(data, x=x_column, y=y_column, color=color_column,size=[1]*len(data),labels=labels,text=data['Sensor Number'].astype(str),custom_data=custom_data,range_color=range_color)
    #set color bar's color
    color_scale = [(0,"#EF5A45"),(0.11,"#EFA243"),(0.22,"#F0E443"),(0.33,"#D1D029"),(0.44,"#9BCA3D"),(0.55,"#5BBA47"),(0.66,"#47B489"),(0.77,"#208B93"),(0.88,"#0E5DA8"),(1.0,"#0E5DA8")]
    fig.update_coloraxes(colorscale=color_scale) 

    fig.update_layout({'plot_bgcolor': 'white','paper_bgcolor': 'white',},margin={'t':20, 'b':25})    
    fig.update_xaxes(title=x_label,ticksuffix=x_ticksuffix,showline=True, linewidth=1, linecolor='black')
    fig.update_yaxes(title=y_label,ticksuffix=y_ticksuffix,showline=True, linewidth=1, linecolor='black',gridwidth=1, gridcolor='#d7d7d7')
    fig.update_layout(coloraxis_colorbar={'title':color_label,'ticks':"outside", 'ticksuffix':color_ticksuffix,'dtick':color_tickinterval},legend={'orientation':"h",'yanchor':"bottom",'y':1.02,'xanchor':"right",'x':1})
    fig.update_traces(textfont_size=11,hovertemplate=hovertemplate,marker_size=42,textfont_color=col) 
    return fig

#CHANGED
def get_occupancy_text(time,occupied_time_start,occupied_time_end,font_size=11):
    '''
    Return the text stating the given time period with the specified font size.
    Parameters:
        time (string): Time period (All Hours, Occupied Hours, Unoccupied Hours)
        occupied_time_start (string): Time when occupancy starts.
        occupied_time_end (string): Time when occupancy ends.
        font_size (int): Font size of text
    Returns:
        Requested time period text.
    '''
    #set font size
    timeText = f'<b><span style="font-size: {font_size}px;">'  
    #add time period text if provided, else return empty string 
    if(time=='NaN'):
        return ''
    elif(time=='Unoccupied Hours'):
        t_start = datetime.datetime.strptime(occupied_time_start,'%H:%M').strftime('%I:%M%p')
        # t_start =occupied_time_start.strftime('%I:%M%p')
        t_end = datetime.datetime.strptime(occupied_time_end,'%H:%M').strftime('%I:%M%p')
        # t_end=occupied_time_end.strftime('%I:%M%p')
        timeText = timeText+ 'Unoccupied Hours<br>'+ t_end + ' - ' + t_start
    elif(time=='Occupied Hours'):
        t_start = datetime.datetime.strptime(occupied_time_start,'%H:%M').strftime('%I:%M%p')
        t_end = datetime.datetime.strptime(occupied_time_end,'%H:%M').strftime('%I:%M%p')
        # t_start =occupied_time_start.strftime('%I:%M%p')
        # t_end=occupied_time_end.strftime('%I:%M%p')
        timeText = timeText + 'Occupied Hours <br>' + t_start + ' - ' + t_end
    else:
        timeText = timeText+ 'All Hours'
    timeText = timeText + '</span></b>'
    return timeText

#CHANGED
def add_legend_text(fig,text):
    '''
    Adds specified text to the legend by adding an empty trace.
    Parameters:
        fig (Figure Object): Figure to add the legend text to.
        text (string): Text to add.
    Returns:
        fig (Figure Object): Specified figure.
    '''
    fig.add_trace(go.Scatter(x=[np.NaN],y=[np.NaN],name=text,marker={'color':'white'},mode='lines'))
    return fig
    
def add_annotations(fig, x_list, y_list, text_list, bgcolor_list):
    '''
    Adds annotations (text on top of a colored rectangle) to the figure and returns the updated figure.
    Parameters: 
        fig: Plotly figure to update.
        x_list (list): List of floats containing the relative x locations of each annotation.
        y_list (list): List of floats containing the relative y locations of each annotation.
        text_list (list): List of strings containing the text to display for each annotation.
        bgcolor_list (list): List of strings containing the background color of each annotation.
    Returns:
        fig: Updated figure.
    '''

    #check if lenght of x,y, and colors provided match
    length = len(x_list)
    if(length!=len(y_list) or length!=len(text_list) or length!=len(bgcolor_list)):
        print("Error: size of annotation properties don't match. ")
        return fig
    #add annotations
    for i in range(length):
        fig.add_annotation(x=x_list[i],y=y_list[i],xref='paper',yref='paper',text=text_list[i],font={'color':'black'},align='right',showarrow=False,bgcolor=bgcolor_list[i])
    return fig

def get_color_list(i): 
    '''
    Associate a color with the number i and return it.
    Parameters:
        i (int): Number based on which a color is returned.
    Returns:
        The color.
    '''      
    BRAND_PALLET = ['#065BA7', '#9BCA3B', '#56B4E9','#C11771', '#000000','#beabea',"#14522d","#4df08f","#7bc5ca","#d40a70", '#8E2100' , '#F0E442','#E288A0', '#A51E55', "#47B489", "#EF5A45","#bc7b48","#7a34d7", "#504713", "#7b6381","#3d3d28","#7693bd","#ee81f2"]
    i = i%(len(BRAND_PALLET)-1)    
    return BRAND_PALLET[i]

#CHANGED
def general_graph_overtime_group_legend(data,x_column,y_column,groups,group_var,filter_var,xaxis_label='',yaxis_label='',ticksuffix='',hovertemplate='',customdata=[]):
    '''
    Returns a figure object containing lines (over time) correpsonding to each specified item, with the legend items grouped together.
    Parameters: 
        data (dataframe): data containig the information to be graphed.
        x_column (string): (parameter to be implemented if needed, currently index is used for x values)
                            The column to use as the x values of the lines. 
                            Empty string means use the index.
        y_column (string): The column to use as the y values of the lines.
        groups (list): Contains all the groups.
        group_var (string): Name of the column in the data that states which group the specific data is for.
        filter_var (string): Name of the column that seperates each graphed trace (example: Sensor Number).
        xaxis_label (string): Title of the horizontal axis.
        yaxis_label (string): Title of the vertical axis.
        ticksuffix (string): Specifies the text to display beside the y values in the yaxis and hover text.
        hovertemplate (string): The format of the text to show when hovering over the graphed line.
        customdata (list): list of column names of "data" to use as custom data for the hovertemplate.
    Returns:
        fig: figure object with the specified properties.
    '''
    fig = go.Figure()
    i = 0    
    for l in groups:#go through each group
         #filter data by group
        d_tmp = data[data[group_var]==l]
        #all items in this group
        group_items = d_tmp[filter_var].unique()
         #format how to display the group text in legend
        name_formatted = '<b><span style="font-size:10px;">'+l+'</span></b>'
        #add group name to legend if it has any items
        if(len(group_items)!=0):
            fig.add_trace(go.Scatter(x=d_tmp.index,y=[d_tmp.mean()],name=name_formatted,marker={'color':'white'},legendgroup=l))
        for s in group_items:#go through each item in this group, and add a trace for it
            df_i = data[data[filter_var]==s]
            fig.add_trace(go.Scatter(x=df_i.index,y=df_i[y_column],hovertemplate=hovertemplate,customdata=df_i[customdata],name=s,line={'shape':'linear','width':1,'color':get_color_list(i)},legendgroup=l))
            i = i+1      
    fig.update_xaxes(title_text=xaxis_label)
    fig.update_yaxes(title_text=yaxis_label,ticksuffix=ticksuffix,showgrid=True, gridwidth=1, gridcolor='#d7d7d7') 
    fig.update_layout({'plot_bgcolor': 'white','paper_bgcolor': 'white',},legend= {'itemsizing': 'constant'},margin={'t':100, 'b':25})
     #if x is date, format it
    if(xaxis_label=='Date'):
        fig.update_xaxes(dtick='D',tickformat="%a<br>%b %d")
    return fig
	

def get_occupancy_text_unformatted(time,occupied_time_start,occupied_time_end):    
    '''
    Return the text stating the given time period, without giviing it a font size.
    Parameters:
        time (string): Time period (All Hours, Occupied Hours, Unoccupied Hours)
        occupied_time_start (string): Time when occupancy starts.
        occupied_time_end (string): Time when occupancy ends.
    Returns:
        Requested time period text.
    '''
    #get text based on time period
    if(time=='NaN'):
        return ''
    elif(time=='Unoccupied Hours'):
        t_start = datetime.datetime.strptime(occupied_time_start,'%H:%M').strftime('%I:%M%p')
        t_end = datetime.datetime.strptime(occupied_time_end,'%H:%M').strftime('%I:%M%p')
        # t_start =occupied_time_start.strftime('%I:%M%p')
        # t_end=occupied_time_end.strftime('%I:%M%p')
        timeText = 'Unoccupied Hours '+ t_end + ' - ' + t_start
    elif(time=='Occupied Hours'):
        t_start = datetime.datetime.strptime(occupied_time_start,'%H:%M').strftime('%I:%M%p')
        t_end = datetime.datetime.strptime(occupied_time_end,'%H:%M').strftime('%I:%M%p')
        # t_start =occupied_time_start.strftime('%I:%M%p')
        # t_end=occupied_time_end.strftime('%I:%M%p')
        timeText =  'Occupied Hours ' + t_start + ' - ' + t_end
    else:
        timeText =  'All Hours'
    return timeText

#CHANGED
def add_xlabel_occupancy_text(fig,text,time,occupied_time_start,occupied_time_end):
    '''
    Adds occupancy text as the xaxis title.
    Parameters:
        fig (figure object): Figure to add the text to.
        text (string): Text to put before the time period text.
        time (string): Time period.
        occupied_time_start (string): Time when occupancy starts.
        occupied_time_end (string): Time when occupancy ends.
    Returns:
        fig (figure object): Updated figure.
    '''
    timeText = get_occupancy_text_unformatted(time,occupied_time_start,occupied_time_end)
    fig.update_xaxes(title='<span style="font-size: 10px;"><b><i>'+ text +timeText+'</b></i></span>')
    return fig

def hovertemplate_days_barplot(floor, location, space, time, ytext):
    '''
    Make hovertemplate for barplots that have date as xaxis.
    Parameters:
        floor (string): Floor to display the text of.
        location (string): Location to display the of.
        space (string): Space to show the display the text of.
        time (string): Time period to display the text of.
        ytext (string): Text to display besides the y value.
    Returns:
        hovertemplate (string): Text that specifies what's displayed on hover.
    '''
    hovertemplate = "<br>".join(['Building Floor: '+str(floor), 'Location: '+str(location), 
                                 'Building Perimeter: '+str(space), 'Time Period: '+str(time), 
                                'Date: %{x|%b %d, %Y}', str(ytext)+': %{y}<extra></extra>'])
    return hovertemplate

#get general variable by task id
#id: task id
def get_vars(id):   
    task_entry = Task.objects.get(id=id)  # get current task object 
    wk_start=task_entry.weekday_occupied_start # weekday occupied start time
    wk_end =task_entry.weekday_occupied_end#weekday occupied end time
    buildingId = str(task_entry.building.id)#associated building id
    return buildingId,wk_start,wk_end

#get the value of the post request for floor, location and perimeter select box
def get_fl_loc_per_var(request):
    floor = request.POST.get('floor',None)
    loc = request.POST.get('location',None)
    space = request.POST.get('perimeter',None)
    return floor,loc,space

#get the floor and occupied value from post request
def get_fl_occupied(request):
    floor = request.POST.get('floor',None)
    occupied = request.POST.get('occupied',None)
    return floor,occupied


def get_floor_iaq(new,floor):
  '''
  Filters data by floor.
  Parameters:
    new (dataframe): Data.
    floor (string): Floor number or 'Building' for all floors.
  Returns:
    new (dataframe): Data filtered by specified floor.
  '''
  if floor!='Building':        
    new=new[new['Floor']==floor]       
  return new


def get_floor_sens_iaq(new,sens): 
  '''
    Filter data by sensor number.
    Parameters:
        new (dataframe): Data.
        sens (string): Sensor number.
    Returns:
        new (dataframe): Data of specified sensor.
  ''' 
  new=new[new['Sensor Number']==sens]
  return new


def check_floor_loc_per(floor,loc,space,df):
  '''
    Filter data by floor, location, and perimeter.
    Parameters:
        floor (string): Floor number.
        loc (string): Location to filter based on; All Locations or name of the location
        space (string): Space to filter based on; Entire Space, Perimeter, or Interior.
        df (dataframe): Data.
    Returns:
        data (dataframe): Filtered data.
  '''
  data=df  
  if space=='Perimeter':
    data=data[data['Perimeter']=='Yes']    
  elif space=="Interior":
    data=data[data['Perimeter']=='No']      
  ####based on location#########
  if loc!='All Locations':    
    data=data[data['Location']==loc] 
  if floor !='Building':
    data=data[data['Floor']==floor] 
  return data

def generate_fig_to_div(request,fig,config,div_info,buildingId,versionId,filename):
    """
        Generate the plotly figure to html div
        Parameters:
            request: request from template view
            fig: plotly figure
            cofig: setting object
            div_info: html string, explaining the graph
            buildingId(int): building id
            versionId(int): task id
            filename(string): file name
        Returns:
            Array of graph and description
    """
    r=[] # a list of graphs
    div = opy.plot(fig, auto_open=False, output_type='div',include_plotlyjs=False,config=config)
    # dic=export_to_png(fig,buildingId,versionId,filename)  
    r.append(div)    
    # r.append(dic)
    r.append(div_info)
    return render(request, 'partials/render.html', {"div": r})

def export_to_png(fig,buildingId,versionId,filename,report=False):
    """
        export the graph to png file.
        fig: plotly figure
        buildingId: building id
        versionId: task id
        filename: the name of the file
        report: boolean value indicate whether this file is called in report or data analysis
        return a file path for storing the graph
    """
    
    if report:# if call in report section, specific file path for storing the graph
        current_location=r"{}/{}/{}/{}/Report/".format(dirname(os.path.dirname(__file__)),'media',buildingId,versionId)
    else:
        current_location=r"{}/{}/{}/{}/".format(dirname(os.path.dirname(__file__)),'media',buildingId,versionId)
    if not os.path.exists(current_location):#check if the location of storing the graph exists or not
        os.makedirs(current_location)        
    fig.write_image(current_location+filename)
    if report:
        return '/media/'+str(buildingId)+'/'+str(versionId)+'/'+'Report/'+filename
    else:
        return '/media/'+str(buildingId)+'/'+str(versionId)+'/'+filename

def map_data(time_data,f,co_df,v):
    '''
    Find data needed for the floorplan of the specified variable "v".
    Parameters:
        time_data (dataframe): Data.
        f (string): Floor number (unused).
        co_df (dataframe): Contains sensors and their coordinate on the floorplan image.
        v (string): Variable to get mean values of.
    Returns:
        time_data (dataframe): Data filtered to contain data of sensors for which we have coordinate info.
        co_df (dataframe): Contains sensor numbers, coordinate on the floorplan, and mean values of "v" for each sensor.
        a (list): Contains unique sensor numbers that are in data and we have coordinate for.
        s_num (list): Contains sensor numbers that are in data and we have coordinate for.
    '''
    #find sensors in data that we have coordinate for  
    s_num=time_data['Sensor Number'].unique() 
    s_num = [s for s in s_num if s in co_df['snsr_num'].values]
    #keep only data of relevant sensors     
    time_data=time_data[time_data['Sensor Number'].isin(s_num)] 
    #find mean values based on "v" variable
    dd=time_data[v].groupby(time_data['Sensor Number']).mean()
    dd=pd.concat([dd],axis=1).reset_index()
    #keep only relevant data
    dd=dd[dd['Sensor Number'].isin(s_num)] 
    dd=dd.sort_values('Sensor Number')
    #combine coordinate and mean values data, and keep only sensors we have both data and coordinate for
    co_df=co_df[co_df['snsr_num'].isin(s_num)]
    co_df.rename(columns={'snsr_num':'Sensor Number'},inplace=True)
    co_df=pd.merge(left=co_df,right=dd,on="Sensor Number", how='left')   
    a = co_df['Sensor Number'].unique() 
    co_df=co_df.drop_duplicates('Sensor Number')
    co_df = co_df.sort_values(by='Sensor Number')
    return time_data,co_df,a,s_num

def clustmap_data(f,v,final_df,co_df): 
    '''
    Clusters sensors based on their overtime values, and returns data needed to graph a cluster floorplan for "v".
    Parameters:
        f (string): Floor number.
        v (string): Variable to use (column name).
        final_df (dataframe): Data.
        co_df (dataframe): Contains sensor numbers and their coordinates.
    Returns:
        s_df (dataframe): Contains sensor numbers, their coordinates, their average "v", their cluster number.
    '''
    #Add mean "v" value for each sensor, and only keep the relevant ones  
    dd,s_df,a,s_num=map_data(final_df,f,co_df,v)     
    #go through each number of clusters and find the best one (based on kmeans clustering and silhoutte score)
    table2 = pd.pivot_table(dd, values=v, index=dd.index, columns=['Sensor Number'],aggfunc=np.mean, fill_value=0)    
    x = table2.T.iloc[:,:].values   
    best_score = -1 #best score is 1, worst is -1
    best_num_clusters = 0
    best_labels = []
    min_clusters = 2
    max_clusters = 10
    num_clusters_range = list(range(min(min_clusters,len(s_num)),min(max_clusters,len(s_num)))) #lower num clusters biased
    for n in num_clusters_range:
        clustering = KMeans(n,random_state=100)
        labels = clustering.fit_predict(x)      
        score = silhouette_score(x, labels)
        if(score > best_score):#-.05
            best_score = score
            best_num_clusters = n
            best_labels = labels
    if(len(best_labels) == 0):      
        s_df['clust']=[1]*len(s_df)        
        return s_df   
    #make a cluster based on hierarchical clustering
    D = hac.linkage(table2.T, method='ward', metric='euclidean')
    #---- evaluate the dendogram
    cut_off_level = best_num_clusters  # level where to cut off the dendogram
    c=results(table2.T, D, cut_off_level)  
    s_df['clust']=c.tolist()   
    return s_df

def results(timeSeries, D, cut_off_level):
    '''
    Get cluster numbers from given linkage matrix.
    Parameters:
        timeSeries (unused)
        D (matrix): Linkage matrix.
        cut_off_level (int): How many clusters to make.
    Returns:
        result (list): Cluster numbers.
    '''
    result = pd.Series(hac.fcluster(D, cut_off_level, criterion='maxclust'))     
    return result

def get_cluster_colorbar(num_clusters):
    '''
    Find color bar properties (colors, ticktext, and tickvals) based on the number of clusters.
    Parameters:
        num_clusters (int): For how many clusters find the properties for.
    Returns:
        color_scale (list): List of tuples of (float,color) pairs that determine the color of floormaps.
        tickvals (list): List of floats that determine what color each cluster is.
        ticktext (list): List of strings that determine the text displayed on the color bar for each tick.
    '''
    colors = ['#1060c7','#c92828','#26690c','#4a0d7d','#6f4417','#302c36','#b593bd','#91e675','#73a5e7','#d8e883','#aae8ce']
    if num_clusters <=0:
        num_clusters=3
    color_scale_divisions = 1/(num_clusters)
    color_scale_divisions = round(color_scale_divisions,4)
    color_location = 0
    color_scale = []
    tickvals = []
    ticktext = []
    j = 0
    for i in range(1,num_clusters+1):
        tickvals.append(i+0.5)#cluster position on the colorbar
        ticktext.append("Cluster "+str(i))#cluster text
        color_scale.append((color_location, colors[j]))#color of the colorbar 
        color_location = color_location + color_scale_divisions
        color_location = min(1.0, color_location)#can't have higher than 1.0 value
        color_scale.append((color_location, colors[j]))
        j = j+1
    color_scale.append((1.0,colors[j-1]))#to avoid continous color
    return color_scale,tickvals,ticktext

def check_occupied_df(buildingId,id,occupied):
    '''
    Get data of the specified time period.
    Parameters:
        buildingId (int): building id
        id (int): task id
        occupied (string): Time period.
    Returns:
        data (dataframe): Data of the specified period.
        time (string): Time period text.
    '''
    data=None
    time=''
    if occupied=="Entire Day":  
        data=load_df(buildingId,id,"final_df.csv")
        time='All Hours'   
    elif occupied=="Occupied":
        data=load_df(buildingId,id,"occ.csv")
        time='Occupied Hours'
    else:
        data=load_df(buildingId,id,"non_occ.csv")
        time = 'Unoccupied Hours'
    return data,time

#CHANGED
def graph_clusters_overtime(request,floor,final_df,s_df,var,buildingId,id,filename,occ_start,occ_end):
    '''
    Makes a  graph for each cluster, showing sensor overtime value for that cluster.
    Parameters: 
        request (): request 
        floor (string): Use this floor's data.
        final_df (dataframe): Contains sensors' data.
        s_df (dataframe): Contains sensor numbers and their cluster info
        var (string): Name of the column to use the values of.
        buildingId (unused)
        id (unused)
        filename (unused)
    Returns:
        Specified figure.
    '''
    r=[]
    fig=None  
    #filter data by floor
    fl=final_df[final_df['Floor']==floor]
    fl['clust']=[0]*len(fl)
     #get list of list of sensors in each cluster
    c1=s_df[s_df['clust']==1]['Sensor Number'].unique()
    c2=s_df[s_df['clust']==2]['Sensor Number'].unique()
    c3=s_df[s_df['clust']==3]['Sensor Number'].unique()
    c4=s_df[s_df['clust']==4]['Sensor Number'].unique()
    c5=s_df[s_df['clust']==5]['Sensor Number'].unique()
    c6=s_df[s_df['clust']==6]['Sensor Number'].unique()
    c7=s_df[s_df['clust']==7]['Sensor Number'].unique()
    c8=s_df[s_df['clust']==8]['Sensor Number'].unique()
    c9=s_df[s_df['clust']==9]['Sensor Number'].unique()
    c10=s_df[s_df['clust']==10]['Sensor Number'].unique()
    n_clust=s_df['clust'].unique()
    # col=['#BEE6F3',"#379ECC","#243E91"]
    all_c=[c1,c2,c3,c4,c5,c6,c7,c8,c9,c10]
    #set text based on variable
    if(var=='Humidity'):
        ticksuffix = '%'
        hover_value_text = 'Relative Humidity'
    elif(var=='Temperature'):
        ticksuffix = '°C'
        hover_value_text = 'Temperature'
    else:
        ticksuffix = ''
        hover_value_text = 'Value'     
    config = config_setting('Relative Humidity - Cluster Analysis - Summary')
    #go through each cluster, and make an overtime graph of the sensors in that cluster
    for i in range(len(n_clust)):
        str_sensors = all_c[i]
        str_sensors = [str(s) for s in str_sensors] 
        #Add time period to overtime graph
        dc1=fl[fl['Sensor Number'].isin(str_sensors)]
        if(len(dc1)==0):
            continue
        dc1[var] = np.round(dc1[var],2)  

        #Add time period to overtime graph
        dc1 = add_time_period_col(dc1,'',occ_start,occ_end)
        #make figure
        hovertemplate = "<br>".join(["Sensor Number: %{customdata[1]}", "Location: %{customdata[0]}", "Time Period: %{customdata[2]}","Date: %{x|%b %d, %Y}","Time: %{x|%H:%M}",hover_value_text+": %{y}","<extra></extra>"])
        fig = general_graph_overtime_group_legend(dc1,'',var,dc1['Location'].unique(),'Location','Sensor Number','Date',var,ticksuffix,hovertemplate,['Location',"Sensor Number",'Time Period']   )
        fig.update_layout(showlegend=True,legend_title_text='Location')            
        fig.update_layout(title=u'<b>\u2022 Cluster '+str(i+1),title_font_color=get_color_list(i))
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#d7d7d7')
        div = opy.plot(fig, auto_open=False, output_type='div',include_plotlyjs=False,config=config)
        # dic=export_to_png(fig,buildingId,versionId,filename)  
        r.append(div)            
    div_info=''
    if var=='Temperature':
        div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" >Guide on How to Read This Graph</h5><p style="padding:15px;">Time is labeled on the horizontal axis, and temperature is on the vertical axis. This figure represents the temperature over time for the selected location, with all of the individual sensors categorized by that location, as well as temperature setpoint illustrated for reference.</p></div></div>'       
    elif var=='Humidity':
        div_info='<div class="giContainer mt-5"><div class="gi"><h5 style="color:#719620;" class="ml-3" >Guide on How to Read This Graph</h5><p style="padding:15px;">Time is labeled on the horizontal axis, and humidity is on the vertical axis. This figure represents the humidity over time for the selected location, with all of the individual sensors categorized by that location.</p></div></div>'
    
    # r.append(dic)
    r.append(div_info)
    return r

def get_sensors_images(id,v_id,floor,screen_width):
    """
        Get floor plan for sensor mapping
        id(int): building id
        v_id(int): task id
        floor(int): floor value
        screen_width()float: user screen value
    """  
    #get a lis of sensors that have been placed
    sensorlist=SensorMapping.objects.filter(task_id=v_id,floor=floor).values("snsr_num","x","y")  
    task_entry = Task.objects.get(id=v_id)  #get the current task
    wk_start = task_entry.weekday_occupied_start
    wk_end = task_entry.weekday_occupied_end   
    if sensorlist.count()>0:   
        co_df = pd.DataFrame(list(sensorlist)) 
        co_df['x']=co_df['x'].astype('str').astype('float')
        co_df['y']=co_df['y'].astype('str').astype('float')      
        width = float(str(BuildingImages.objects.get(building_id=id,floor_building=floor).width))
        height = float(str(BuildingImages.objects.get(building_id=id,floor_building=floor).height))
        img=r"{}/{}".format(dirname(os.path.dirname(__file__)),BuildingImages.objects.get(building_id=id,floor_building=floor).img_path)
        scale_factor = img_converter(screen_width,width)*0.8 # covert the image size
        # co_df the dataframe of the coordinates
        return co_df,img,width,height,scale_factor,wk_start,wk_end
    else:
        return pd.DataFrame(),'',0,0,0.0,wk_start,wk_end

def img_converter(w,width):
    """
        Convert the image ratio that can fit in user screen
        Parameters:
            w: actual image size
            width: user screen size
        Returns:
            ratio
    """   
    ratio=w/width # compare two sizes
    if ratio>1:#if the actual image wdith is bigger than user screen size, use user screen width
      ratio=1    
    return float(ratio)


def ashrae(hours,floor,data):
    '''
    Finds whether temperatures have exceeded ashrae standards.
    Parameters:
        hours (float): time interval, 0.25,0.5,1,2,4
        floor (string): floor.
        data (dataframe): sensors' data.
    Returns:
        sensors (dataframe): Contains dates for each sensor and how much sensor has exceeded for that day.
        ashrae (dataframe): Contains sensors, their location, and how much the have exceeded the standard.
    ''' 
    w=[16,31,61,121,241] ##window sizes for 15min, 30min, 1hour, 2hour, and 4hours
    ash=[1.1,1.7,2.2,2.8,3.3] ##ashrae threshold for each time
    time=['15 Minutes','30 Minutes','1 Hour','2 Hours','4 Hours']
    h=[0.25,0.5,1.0,2.0,4.0]
    w_=0
    ash_=0.0
    time_=''
    ###store window size and threshold based on given hours
    for i in range(len(h)):
        if h[i]==float(hours):
            w_=w[i]
            ash_=ash[i]
            time_=time[i]    
    ashrae = pd.DataFrame()
    #filter  by floor       
    if floor!='Building':
        data=data[data['Floor']==floor]
    #find exceed value of each sensor        
    a= data['Sensor Number'].unique() ##unique sensor numbers    
    for j in a: 
        s1=data[data['Sensor Number']==j]
        date=s1['Date'].unique() ##unique dates
        ex=list()
        notex=list()
        dd=[]
        for m in date:
            #filter data set for each day. Data for one sensor on a single date 
            d1=s1[s1['Date']==m]            
            if len(d1)>w_:
                dd.append(m)
                exceed=list()
                for i in range(len(d1)-w_):
                    d=abs(d1['Temperature'][i]-d1['Temperature'][i+w_]) #Temperature difference within window
                    d=round(d,2) 
                    ###check whether it exceeds the limit
                    if(d > ash_):
                        exceed.append('TRUE')
                    else:
                        exceed.append('FALSE')
                #store exceeded and not exceeded percentage for each day for each sensor
                ex.append(round(len([e for e in exceed if e == 'TRUE'])/len(exceed)*100,2))
                notex.append(round(len([e for e in exceed if e == 'FALSE'])/len(exceed)*100,2))
        sens=[j]*len(dd)
        #new dataframe which shows not exceeded time percentage for each sensor on each day.     
        dict = {'sensor': sens, 'Date':dd,'not_exceeded':notex}  
        exdf = pd.DataFrame(dict)
        ashrae=ashrae.append(exdf)
    #mean "not exceeded" percentages for each sensor
    sensors=ashrae['not_exceeded'].groupby(ashrae['sensor']).mean()
    sensors=pd.concat([sensors],axis=1).reset_index()    
    data = data.groupby(['Sensor Number', 'Location']).size().reset_index() ###filter locationns of each sensor number
    sensors['Location']=data['Location'] ##add locations   
    return sensors,ashrae,time_


#CHANGED (new function)
def get_date_range_text(data): #returns date range and its text for hover
    '''
    Get text that shows date range of this data, for hover.
    Paramters:
        data (dataframe): Data.
    Returns:
        text (string): Text of data's date range.
    '''
    if(len(data)==0):
        return ''
    minDate = pd.to_datetime(data['Date'].min()).strftime('%b %d, %Y')
    maxDate = pd.to_datetime(data['Date'].max()).strftime('%b %d, %Y')
    text = '<br>Date Range: '+str(minDate)+' to '+ str(maxDate)
    return text


#CHANGED (new function)
def add_comfort_range_legend(fig,dot_type='solid',size=11,compact=False,bold=True):
    '''
    Add comfort range text to legend.
    Parameters:
        fig (figure object): Figure to add legend text to.
        dot_type (string): Type of legend entry's line.
        size (int): Font size of the text.
        compact (boolean): Whether to add detailed text (size and bold parameters don't change the text if this is true).
        bold (boolean): Whether to make the text bold.
    '''
    if compact==True:#add short text
        comfortText = 'Comfortable Range'
    else:#add detailed text
        if(bold==True):#make the text bold
            comfortText = f'<b><span style="font-size: {size}px;">'+'Comfortable Range<br>'+str(20)+'-'+str(24)+'°C, '+str(20)+'-'+str(60)+'% Relative Humidity'+'</span></b>'
        else:#don't make the text bold
            comfortText = f'<span style="font-size: {size}px;">'+'Comfortable Range<br>'+str(20)+'-'+str(24)+'°C, '+str(20)+'-'+str(60)+'% Relative Humidity'+'</span>'
    #add text to legend
    fig = add_legend_text(fig,comfortText)
    fig.data[-1]['line']['color']='lightgreen'
    fig.data[-1]['line']['dash']=dot_type
    return fig

#Adds a column to the data that states whether the time period is occupied or unoccupied.
def add_time_period_col(data,time_col,occ_start,occ_end):
    '''
    Adds a column to the data that states whether the time period is occupied or unoccupied.
    Paramters: 
        data (dataframe): Data.
        time_col (string): Column containing timestamp values. If empty string, means index has the timestamps.
        occ_start (string): Start of occupied time.
        occ_end (string): End of occupied time.
    Returns:
        data (dataframe): Data with time period column.
    '''
    if(time_col==''):#timestamp in index
        data['Time_tmp'] = pd.to_datetime(data.index).strftime('%H:%M')
        data['Time Period'] = 'Occupied Hours'
        data.loc[(data['Time_tmp']<occ_start) | (data['Time_tmp']>occ_end),'Time Period'] = 'Unoccupied Hours'
    else:#timestamp in a column
        data['Time_tmp'] = pd.to_datetime(data[time_col]).dt.strftime('%H:%M')
        data['Time Period'] = 'Occupied Hours'
        data.loc[(data['Time_tmp']<occ_start) | (data['Time_tmp']>occ_end),'Time Period'] = 'Unoccupied Hours'
    return data