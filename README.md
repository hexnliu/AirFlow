AirFlow Website Source Code
====================================
## Introduction
This site is designed to collect data from sensors and display the results on the page for data analysis, finally showing building problems and solution report.
## devDependencies
* language: python 3.13.15
* framework: Django 6.1
* Database: MongoDB
* additional installed package: 
    * paho-mqtt
    * numpy
    * aws
    * json
    * pandas
    * plotly
    * seaborn
    * matplotlib
    * requests
    * statemodels
    * boto3
    * s3fs


## Website Structure

This system is divided into two parts according to the service: `Application` and `Website`.

* `Application`: All python applications are under the folder: `accounts`.
    * `proceedFile.py`: 1. Collect the loT data from `Base station`. 
                        2. Sensor Placement data from `web page` or `csv` file. 
                        3. Weather data from `csv` file. 
    * `uploadFile.py`: upload `csv`,`xls`,`xlxs` file
    * `dataAnalysis.py`: Analysis temprature flactuation, temperature floor variation, and so on.
    

* `Website`: The website follows the structure design of Django framework. frontend under accounts-> templates floder and static

## How to run
We are using ` visual studio ` for development, in order to avoid problems because of the built environment by running.

After you install , right click the directory folder, open git bush, `git clone https://github.com/hexnliu/AirFlow.git`.

then open `visual studio` File-> `open floder` add airFlow folder to work place.
* To run `Application`, click Terminal, change powershell to cmd, activate virtual environment, run `python manage.py runserver`
    * `Host`: localhost
    * `Port`: 8000
   
