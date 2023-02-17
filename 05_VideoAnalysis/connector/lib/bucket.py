class IS3Object:
  def __init__(self):
    self.__bucket:str = None
    self.__key:str=None
  
  @property
  def bucket(self)->str:
    return self.__bucket

  @property
  def key(self)->str:
    return self.__key

  @bucket.setter
  def bucket(self,value)->None:
    self.__bucket=value

  @key.setter
  def key(self,value)->None:
    self.__key=value

  @property
  def s3_uri(self)->str:
    return 's3://{}/{}'.format(self.bucket,self.key)

class S3Object(IS3Object):
  def __init__(self,bucket:str=None,key:str=None)->None:
    self.bucket = bucket
    self.key = key

  @staticmethod
  def from_s3_uri(uri:str)->IS3Object:
    if uri is None:
      raise ValueError('No image_uri specified')

    bucket = uri.split('/')[2]
    key = '/'.join(uri.split('/')[3:])
    return S3Object(bucket=bucket,key=key)