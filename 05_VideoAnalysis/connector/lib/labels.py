import re
from typing import List

from PIL.Image import Image

class BoundingBox:
  def __init__(self, props:dict)->None:
    self.__width = props['Width']
    self.__height = props['Height']
    self.__left = props['Left']
    self.__top = props['Top']

  @property
  def width(self)->float:
    return self.__width

  @property
  def height(self)->float:
    return self.__height

  @property
  def left(self)->float:
    return self.__left

  @property
  def top(self)->float:
    return self.__top

  def resize(self,size)->dict:
    w, h = size
    return {
      'Width':w * self.width,
      'Height':h * self.height,
      'Left': w * self.left,
      'Top': h*self.top,
    }

class ParentLabel:
  def __init__(self, props:dict)->None:
    self.__name = props['Name']

  @property
  def name(self)->str:
    return self.__name

class LabelInstance:
  def __init__(self, props:dict)->None:
    if 'BoundingBox' in props:
      self.__bounding_box = BoundingBox(props['BoundingBox'])

    if 'Confidence' in props:
      self.__confidence = props['Confidence']

  @property
  def confidence(self)->float:
    return self.__confidence

  @property
  def bounding_box(self)->BoundingBox:
    return self.__bounding_box

class Label:
  def __init__(self, properties:dict)->None:
    self.__name = properties['Name']
    self.__confidence = properties['Confidence']
    self.__instances = [LabelInstance(x) for x in properties['Instances']]
    self.__parents = [ParentLabel(x) for x in properties['Parents']]

  @property
  def name(self)->str:
    return self.__name

  @property
  def confidence(self)->float:
    return self.__confidence

  @property
  def instances(self)->List[LabelInstance]:
    return self.__instances

  @property
  def parent_labels(self)->List[ParentLabel]:
    return self.__parents

class LabelDocument:
  def __init__(self, response:dict)->None:
    if 'Labels' not in response:
      raise ValueError('Invalid Document')

    self.__response = response
    self.__labels = [Label(x) for x in response['Labels']]

  def as_dict(self):
    return self.__response

  @property
  def labels(self)->List[Label]:
    return self.__labels

  @property
  def bounded_labels(self)->List[Label]:
    results = []
    for label in self.labels:
      for instance in label.instances:
        if instance.bounding_box != None:
          results.append(label)
          break

    return results

  @property
  def has_person(self)->bool:
    """
    Check if there are bounding boxes with Person or Human
    """
    for label in self.bounded_labels:
      if label.name  == "Person" or label.name == "Human":
        return True
    return False

class FaceRecord:
  def __init__(self, props:dict) -> None:
    self.__face = props['Face']
    self.__face_detail = props['FaceDetail']
    
  @property
  def face(self)->dict:
    return self.__face

  @property
  def face_detail(self)->dict:
    return self.__face_detail

  def summarize(self, image:Image)->dict:
    bounding_box = BoundingBox(props=self.face['BoundingBox'])
    resized_box = bounding_box.resize(image.size)

    return {
      'FaceId': self.face['FaceId'],
      'ImageId': self.face['ImageId'],
      'BoundingBox': resized_box,
      'Confidence': self.face['Confidence'],
      'Age': self.face_detail['AgeRange'],
      'Gender': self.face_detail['Gender'],
      'Emotions': self.face_detail['Emotions'],
      'Quality': self.face_detail['Quality'],
    }

class FaceRecordDocument:
  def __init__(self, response:dict) -> None:
    self.__response = response
    self.__faces = [FaceRecord(props=x) for x in response['FaceRecords']]

  @property
  def faces(self)->List[FaceRecord]:
    return self.__faces

  def as_dict(self):
    return self.__response