from django import forms
from .models import Building
from .views import *
import json

# admin page 
#get country by reading json file
def get_country():
    """ GET COUNTRY SELECTION """
    all_data = read_json("files/countries.json")
    all_countries = [('-----', '---Select a Country---')]
    for x in all_data:
            y = (x['name'], x['name'])
            all_countries.append(y)
    return all_countries


def return_state_by_country(country,_all=False):
    """ GET STATE SELECTION BY COUNTRY INPUT """
    all_data = read_json("files/countries.json")
    all_states=[]
    if _all:
        all_states = [('-----', '---Select a Province / State---')]
        for x in all_data:
      
            for state in x['states']:
                y = (state['name'], state['name'])
                all_states.append(y)
    else:
        for x in all_data:

            if x['name'] == country:
                for state in x['states']:
                    all_states.append(state['name'])
    return all_states

def return_city_by_country_state(country,province,_all=False):
    """ GET STATE SELECTION BY COUNTRY INPUT """
    all_data = read_json("files/countries.json")
    all_cities=[]
    if _all:
        all_cities = [('-----', '---Select a City---')]
        for x in all_data:
            for state in x['states']:
                for c in state["cities"]:
                    y = (c['name'], c['name'])
                    all_cities.append(y)
    else:
        for x in all_data:
            if x['name'] == country:
                for state in x['states']:
                        if province == state["name"]:
                            for c in state["cities"]:
                                    all_cities.append(c['name'])
    return all_cities



