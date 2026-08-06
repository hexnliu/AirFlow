
import gc,math,boto3,json,s3fs,os,io,asyncio,datetime
from botocore.config import Config
from inventory.views import *

# s3 bucket credential, return boto client and boto resource

def get_credential():
  REGION_NAME = 'ca-central-1'
  SIGNATURE_VERSION = "s3v4"
  credentials = read_json_file('credentials.json')
  aws_id = credentials.get('UPLOAD_AWS_ACCESS_KEY_ID')
  aws_key = credentials.get('UPLOAD_AWS_SECRET_ACCESS_KEY')
  bucket = credentials.get('UPLOAD_BUCKET_LOCAL')  
  s3 = boto3.client('s3',
                    aws_access_key_id=aws_id,
                    aws_secret_access_key=aws_key,
                    config=Config(signature_version=SIGNATURE_VERSION),
                    region_name=REGION_NAME)
  s3_=boto3.resource('s3', aws_access_key_id=aws_id,aws_secret_access_key=aws_key,config=Config(signature_version=SIGNATURE_VERSION),region_name=REGION_NAME)
  return s3,s3_,bucket

# read json files
def read_json_file(json_file):
    parent_path = os.path.abspath(os.path.join(os.path.dirname(__file__),os.path.pardir))
    file_name = os.path.join(parent_path, json_file)
    with open(file_name, 'r') as fd:
        read_file = json.loads(fd.read())
    return read_file