import logging
import boto3
from typing import Any, List, Mapping
from os import path
from io import BytesIO
from json import loads, dumps
from lib.bucket import IS3Object, S3Object
from lib.labels import FaceRecordDocument, LabelDocument
from logging import Logger

logger = Logger('RekClient')
class RekClient:
  def __init__(self, region_name:str=None)->None:
    self.__rekognition = boto3.client('rekognition',region_name=region_name)
    self.__s3 = boto3.client('s3', region_name=region_name)
    self.__collections = {}

  @property
  def rekognition_client(self)->boto3.client:
    return self.__rekognition

  @property
  def s3_client(self)->boto3.client:
    return self.__s3

  def detect_s3_labels(self,s3_object:IS3Object)->LabelDocument:
    """
    Perform basic object detection on the frame
    """
    logger.info('detect_s3_labels - {}'.format(
      s3_object.s3_uri))

    # Check if this file is already processed
    existing = self.__try_get_s3_labels(s3_object)
    if existing != None:
      logger.info('returning existing')
      return existing

    # Process the image
    try:
      response = self.rekognition_client.detect_labels(
        MaxLabels=1000,
        #MinConfidence=55,
        Image={
          'S3Object':{
            'Bucket': s3_object.bucket,
            'Name': s3_object.key
          },
        })
    except Exception as err:
      logger.error(err)
      raise err

    # Persist the file
    document = LabelDocument(response)
    self.__save_s3_labels(s3_object, document)

    return document

  def detect_s3_faces(self,s3_object:IS3Object, collection_id:str)->FaceRecordDocument:
    response = self.rekognition_client.index_faces(
      CollectionId=collection_id,
      MaxFaces=100,
      DetectionAttributes=["ALL"],
      Image={
        'S3Object':{
          'Bucket': s3_object.bucket,
          'Name': s3_object.key
        },
      })

    return FaceRecordDocument(response=response)


  def __try_get_s3_labels(self, s3_object:S3Object)->LabelDocument:
    """
    Attempt to fetch an previous request
    """
    response=None
    try:
      response = self.s3_client.get_object(
        Bucket=s3_object.bucket,
        Key='labels/{}.json'.format(s3_object.key))
    except:
      return None

    body = response['Body'].read()
    decode= body.decode()
    props = loads(decode)
    return LabelDocument(props)

  def __save_s3_labels(self, s3_object:S3Object, document:LabelDocument)->None:
    """
    Attempt to cache the label results
    """
    response = self.s3_client.put_object(
      Bucket=s3_object.bucket,
      Key='labels/{}.json'.format(s3_object.key),
      Body = dumps(document.as_dict(), indent=True).encode())

    print('Saved LabelDocument')
    