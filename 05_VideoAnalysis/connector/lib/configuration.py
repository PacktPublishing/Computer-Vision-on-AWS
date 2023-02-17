from os import environ, path
from json import loads
from typing import Any, List, Mapping
from boto3 import client

def get_value(key:str):
  """
  Gets a configuration value.
  """
  value = environ.get(key)
  if value == None or len(str(value)) == 0:
    raise ValueError('Missing env: '+key)
  return value

secrets = client('secretsmanager', region_name=get_value('REGION'))

class CameraBaseStation:
  """
  Represents an individual Eufy base station.
  """
  def __init__(self, url:str, props:dict) -> None:
    self.__address = url
    self.__base_name=url
    self.__secret_name = props['secret']
    self.__cameras = props['cameras']

    if 'base_name' in props.keys():
      self.__base_name = props['base_name']

  @property
  def name(self)->str:
    return self.__base_name

  @property
  def secret_name(self)->str:
    return self.__secret_name

  @property
  def cameras(self)->List[str]:
    return self.__cameras

  @property
  def rtsp_address(self)->str:
    try:
      response = secrets.get_secret_value(
        SecretId=self.secret_name)

      creds= response['SecretString']
      return 'rtsp://{}@{}'.format(creds,self.__address)
    except Exception as error:
      print('Unable to access secret:{}'.format(self.secret_name))
      raise error

class CameraNetTopology:
  """
  Represents the camera topology for Chatham.
  """
  def __init__(self, file_name:str='config.json') -> None:
    # Fix any relative pathing issues...
    if not path.exists(file_name):
      full_path = path.join(path.dirname(__file__), file_name)
      if not path.exists(file_name):
        raise FileExistsError("Unable to find {} and we really looked.".format(file_name))
      file_name = full_path
    
    with open(file_name, 'r') as f:
      self.__json = loads(f.read())

  @property
  def json(self)->Mapping[str,Any]:
    return self.__json

  @property
  def home_bases(self)->List[CameraBaseStation]:
    return [CameraBaseStation(url=x, props=self.__json[x]) for x in self.__json.keys()]

class Configuration:
  """
  Gets the thread execution configuration.
  """
  def __init__(self, server_uri=None, base_name:str=None, camera_name=None, bucket_name=None):
    self.server_uri = server_uri
    self.base_name = base_name
    self.camera_name = camera_name
    self.bucket_name = bucket_name

  def __str__(self):
    return "Config:[rtsp://{}/{} -> {}]".format(
      self.base_name,
      self.camera_name,
      self.bucket_name)

  @property
  def camera_name(self)->str:
    return self.__camera_name

  @camera_name.setter
  def camera_name(self, value)->None:
    self.__camera_name = value

  @property
  def server_uri(self)->str:
    return self.__server_uri

  @server_uri.setter
  def server_uri(self, value)->None:
    self.__server_uri = value

  @property
  def bucket_name(self)->str:
    return self.__bucket

  @bucket_name.setter
  def bucket_name(self, value)->None:
    self.__bucket = value

  @staticmethod
  def __get_setting(name) ->str:
    value = environ.get(name)
    if value is None:
      raise ValueError('MissingValue: '+name)
    return value

  @staticmethod
  def from_environment():
    print('from_environment')
    
    result = Configuration()
    result.server_uri = "rtsp://{}".format(Configuration.__get_setting('SERVER_URI'))
    result.bucket = Configuration.__get_setting('BUCKET')
    return result

  @staticmethod
  def from_request(request:dict):
    result = Configuration()
    result.server_uri = request['SERVER_URI']
    result.bucket_name = request['BUCKET']
    return result
