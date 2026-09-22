from django.urls import path

from . import views

app_name="Data Analysis"
urlpatterns=[
    path('view_analysis/<int:id>', views.AnalysisView.as_view(), name='view_analysis'),#task id
    path('view_floor_plan/<int:id>', views.view_floor_plan, name='view_floor_plan'),#task id
    path('get_sensors_by_floor/<int:id>', views.get_sensors_by_floor, name='get_sensors_by_floor'),#task id
    path('get_locations_by_floor/<int:id>', views.get_locations_by_floor, name='get_locations_by_floor'),#task id
    path('get_perimeters_by_location/<int:id>', views.get_perimeters_by_location, name='get_perimeters_by_location'),#task id
    path('run_data_analysis/<int:id>', views.run_data_analysis, name='run_data_analysis'),#task id

    # occupant_comfort
    path('occupant_comfort/summary/<int:id>',views.occupant_comfort_summary,name='occupant_comfort_summary'),
    path('occupant_comfort/location/<int:id>',views.occupant_comfort_location,name='occupant_comfort_location'),
    path('occupant_comfort/sensor/<int:id>',views.occupant_comfort_sensor,name='occupant_comfort_sensor'),
    path('occupant_comfort/floor_plan/<int:id>',views.occupant_comfort_floor_plan,name='occupant_comfort_floor_plan'),
    path('occupant_comfort/temp_RH/<int:id>',views.occupant_comfort_temp_RH,name='occupant_comfort_temp_RH'),
    # temperature 
    path('temperature/cluster_analysis/summary/<int:id>',views.temperature_cluster_analysis_summary,name='temperature_cluster_analysis_summary'),
    path('temperature/floor_plan/summary/<int:id>',views.temperature_floor_plan_summary,name='temperature_floor_plan_summary'),
    path('temperature/temp_vs_time/location/<int:id>',views.temperature_vs_time_location,name='temperature_temp_vs_time_location'),
    path('temperature/temp_vs_time/sensor/<int:id>',views.temperature_vs_time_sensor,name='temperature_temp_vs_time_sensor'),
    path('temperature/temperature_differential/summary/<int:id>',views.temperature_differential_summary,name='temperature_differential_summary'),
    path('temperature/temperature_differential/location/<int:id>',views.temperature_differential_location,name='temperature_differential_location'),
    path('temperature/temperature_differential/sensor/<int:id>',views.temperature_differential_sensor,name='temperature_differential_sensor'),
    path('temperature/temperature_variations/summary/<int:id>',views.temperature_variations_summary,name='temperature_variations_summary'),
    path('temperature/temperature_variations/location/<int:id>',views.temperature_variations_location,name='temperature_variations_location'),
    path('temperature/temperature_variations/sensor/<int:id>',views.temperature_variations_sensor,name='temperature_variations_sensor'),
    # Relative Humidity
    path('rh/cluster_analysis/summary/<int:id>',views.rh_cluster_analysis_summary,name='rh_cluster_analysis_summary'),
    path('rh/floor_plan/summary/<int:id>',views.rh_floor_plan_summary,name='rh_floor_plan_summary'),
    path('rh/rh_vs_time/location/<int:id>',views.rh_vs_time_location,name='rh_vs_time_location'),
    path('rh/rh_vs_time/sensor/<int:id>',views.rh_vs_time_sensor,name='rh_vs_time_sensor'),

    # pressure
    path('pressure/pressure_vs_time/summary/<int:id>',views.pressure_vs_time_summary,name='pressure_vs_time_summary'),
    path('pressure/pressure_differential/floor_plan/<int:id>',views.pressure_differential_floor_plan,name='pressure_differential_floor_plan'),
    path('pressure/pressure_differential/sensor_pair/<int:id>',views.pressure_differential_sensor_pair,name='pressure_differential_sensor_pair'),

    # air quality
    path('air_quality/tvoc/summary/<int:id>',views.air_quality_tvoc_summary,name='air_quality_tvoc_summary'),
    path('air_quality/tvoc/location/<int:id>',views.air_quality_tvoc_location,name='air_quality_tvoc_location'),
    path('air_quality/tvoc/sensor/<int:id>',views.air_quality_tvoc_sensor,name='air_quality_tvoc_sensor'),
    path('air_quality/tvoc/floor_plan/<int:id>',views.air_quality_tvoc_floor_plan,name='air_quality_tvoc_floor_plan'),
    path('air_quality/co2/summary/<int:id>',views.air_quality_co2_summary,name='air_quality_co2_summary'),
    path('air_quality/co2/location/<int:id>',views.air_quality_co2_location,name='air_quality_co2_location'),
    path('air_quality/co2/sensor/<int:id>',views.air_quality_co2_sensor,name='air_quality_co2_sensor'),
    path('air_quality/co2/floor_plan/<int:id>',views.air_quality_co2_floor_plan,name='air_quality_co2_floor_plan'),
    # virus transmission
    path('virus_transmission/summary/<int:id>',views.virus_transmission_summary,name='virus_transmission_summary'),
    path('virus_transmission/location/<int:id>',views.virus_transmission_location,name='virus_transmission_location'),

]