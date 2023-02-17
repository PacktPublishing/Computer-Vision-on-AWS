from time import sleep
from lib.configuration import Configuration, get_value
from rtsp import Client
from PIL import Image
from io import BytesIO
from datetime import datetime
from random import random
from json import dumps
import boto3
from lib.rekclient import RekClient
from lib.bucket import S3Object

collection_id = get_value('REK_COLLECT_ID')
region_name = get_value('REGION')
analyzed_frame_topic_arn = get_value('FRAME_ANALYZED_TOPIC')
frame_size=(1920,1080)
default_sampling_rate = 1#0.05
delay_frame_processed = 30
delay_no_frame=0.5

s3 = boto3.client('s3', region_name=region_name)
sns = boto3.client('sns',region_name=region_name)
cloudwatch = boto3.client('cloudwatch', region_name=region_name)
rekclient = RekClient(region_name=region_name)

def include_sample(sampling_rate=default_sampling_rate)->bool:
  if random() <= sampling_rate:
    return True
  return False

class Producer:
  """
  Represents the RTSP Video Producer Component
  """
  @property
  def config(self)->Configuration:
    return self.__config

  def __init__(self, config:Configuration)->None:
    self.__config = config

  def invoke(self)->bool:
    with Client(rtsp_server_uri=self.config.server_uri, verbose=False) as client:
      if not client.isOpened():
        print('{} server is not running.'.format(self.config.server_uri))
        sleep(delay_no_frame)
        return False

      image = client.read()
      while True:
        try:
          if self.process_image(image):
            sleep(delay_frame_processed)
          else:
            sleep(delay_no_frame)

          image = client.read()
        except Exception as e:
          print(e)
          return False

  def process_image(self, image:Image) -> bool:
    has_processed_frame = False

    if image is None:
      if include_sample(0.01):
        print('No frame to write {}:[{}], skipping.'.format(
        self.config.base_name,
        self.config.server_uri,
      ))
      return has_processed_frame

    if not include_sample():
      return has_processed_frame

    array = BytesIO()
    image.save(array, format='PNG')

    dt = datetime.now()
    key = 'eufy/{}/{}/{}.png'.format(
      self.config.base_name,
      self.config.camera_name,
      dt.strftime('%Y/%m/%d/%H/%M/%S.%f'))

    s3_object = S3Object(bucket=self.config.bucket_name, key=key)
    
    # Attempt to write the frame
    try:
      s3.put_object(
        Bucket=s3_object.bucket,
        Key=s3_object.key,
        Body=array.getvalue(),
        Metadata={
          'BaseName': self.config.base_name,
          'Camera':self.config.camera_name,
        })
      print('Wrote Frame {}: {}'.format(s3_object.s3_uri, image))

      # Record that we actually got a valid frame and uploaded it.
      has_processed_frame = True
    except Exception as error:
      print('Unable to write frame: '+str(error))
      return has_processed_frame

    self.__increment_counter("FrameUploaded")

    # Analyze the frame
    try:
      labels = rekclient.detect_s3_labels(
        s3_object=s3_object)
    except Exception as error:
      print('Unable to DetectLabels in {} - {}'.format(s3_object.s3_uri, str(error)))
      return has_processed_frame

    self.__increment_counter('BoundedLabelDetected', count=len(labels.bounded_labels))

    # Find any faces within the document
    try:
      face_document = rekclient.detect_s3_faces(
        s3_object=s3_object, 
        collection_id=collection_id)

      for face in face_document.faces:
        meta = face.summarize(image)
        meta['S3_Uri'] = s3_object.s3_uri
        meta['Camera'] = self.config.camera_name
        meta['BaseName'] =self.config.base_name

        response = sns.publish(
          TopicArn=analyzed_frame_topic_arn,
          Message=dumps(meta,indent=2,sort_keys=True),
          MessageAttributes={
            'Camera': {
              'DataType':'String',
              'StringValue':self.config.camera_name
            },
            'BaseName': {
              'DataType':'String',
              'StringValue':self.config.base_name
            },
            'HasPerson': {
              'DataType':'String',
              'StringValue':'true'
            },
          })
        print(response)
        self.__increment_counter('FaceDetected', count=len(face_document.faces))
    except Exception as error:
      print('Unable to DetectFaces in {} - {}'.format(s3_object.s3_uri, str(error)))
      return has_processed_frame

    return has_processed_frame

  def __increment_counter(self,metric_name:str, count=1)->None:
    assert metric_name != None, "No metric_name provided"
    
    # Attempt to call put_metric_data
    try:
      print('sending metric: {} with count {}'.format(
        metric_name, count))

      cloudwatch.put_metric_data(
        Namespace='HomeNet',
        MetricData=[
          {
            "MetricName": metric_name,
            "Value":count,
            "Unit": 'Count',
            "Dimensions": [
              {
                "Name": 'base_name',
                "Value": self.config.base_name
              },
              {
                "Name": 'camera_name',
                "Value": self.config.camera_name
              },
            ]
          }
        ],
      )
    except Exception as error:
      print('Unable to put_metric_data :'+str(error))
      raise error

  # def capture_video(self, client:Client)->None:
  #   print('capture_video entered')
  #   fourcc = cv2.VideoWriter_fourcc(*'avc1') #(*'mp4v')
  #   out = cv2.VideoWriter('/tmp/output.mp4',fourcc,60,frame_size)

  #   frame_count=0
  #   while True:
  #     if frame_count > 1000:
  #       print('Reached max frames')
  #       break

  #     image = client.read(raw=False)
  #     if image is None:
  #       print ('No frame, skipping')
  #       continue

  #     frame_count += 1
  #     out.write(image)
  #     print(image)

  #   out.release()
  #   self.upload_video('/tmp/output.mp4')

  # def upload_video(self, file:str):
  #   print('upload_video({})'.format(file))

  #   dt = datetime.now()
  #   key = 'video/{}/{}.mp4'.format(self.config.camera_name,dt.strftime('%Y/%m/%d/%H/%M.%S.%f'))
  #   bucket = boto3.resource('s3').Bucket(self.config.bucket_name)

  #   print('Uploading to s3://{}/{}'.format(
  #     self.config.bucket_name, key))

  #   bucket.upload_file(file,key)

