import json
from django import template
register = template.Library()
import re
import ast
import base64
from base64 import b64encode
import requests
from django.conf import settings
from datetime import date
import ast

@register.filter
def get_as_base64(_bin):
    
  if _bin is None or _bin =="None" or _bin =="":
       _bin="/media/grey.png"   
  return (base64.b64encode(requests.get("http://127.0.0.1:8000"+_bin).content)).decode()

@register.filter
def bin_2_img(_bin,upload=False):
  if upload == False:
    if _bin is not None and _bin !="None" and _bin !="":
      return _bin
    else:
      return "/media/grey.png"
  else:
     if _bin is not None and _bin !="None" and _bin !="":
      return _bin
     else:
      return "/media/image_upload.png"

# format date 
@register.filter
def format_date(date):
  if date:
   return date.isoformat()
  else:
     return ""

@register.filter
def format_time(time):
  if time:
   return time
  return ""

@register.filter
def boolean_2_str(value):
  if value == True:
   return "True"
  elif value == False:
    return "Flase"
  else:
    return ""

@register.filter
def sep_camel_case(text):
  return re.sub("([a-z])([A-Z])","\g<1> \g<2>",text).title()


@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)

@register.filter
def available(arg1):
  return int(arg1)==5

@register.filter
def formate_datetime(arg1):
  return arg1.strftime("%Y/%m/%d, %H:%M:%S")


# compare to two string equal to get active class name
@register.filter
def active_class(arg1, arg2):
    if arg1==arg2:
      return "active"
    return ""
@register.filter
def str_equal(arg1, arg2):
    if arg1==arg2:
      return "true"
    return "false"
@register.filter
def active_tab(arg1, arg2):
    if arg1==arg2:
      return "show active"
    return ""
@register.filter
def str_2_list(arg1):
    return json.load(arg1)

@register.filter
def str_2_int(arg1):
    return int(arg1)

    
@register.filter
def get_floor_text(v):
  if v != '':
    v= int(float(v))
    if v > 1:
      return v
    elif v==1:
      return "Ground (1)"
    else:
      return "B"+str(v*-1)
  else:
    return ''

@register.filter
def str2Array(str):
  print(str)
  return json.loads(str)
