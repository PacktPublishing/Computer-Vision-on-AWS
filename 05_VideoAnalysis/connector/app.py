#!/usr/bin/python3
import threading
from time import sleep
from signal import signal, SIGTERM
from lib.processor import Producer
from lib.configuration import Configuration, CameraNetTopology, get_value
from json import dumps

def shutdown(signnum, frame):
  print('Caught SIGTERM, exiting')
  exit(0)

def handler(request, context):
  print(dumps(request))
  config = Configuration.from_request(request)
  producer = Producer(config)
  producer.invoke()

def friendly_sleep(secs)->None:
  for _ in range(0,secs):
    sleep(1)

def run_continously(config:Configuration=None):
  if config == None:
    config = Configuration.from_environment()

  while(True):
    try:
      #print('Processing: '+str(config))
      Producer(config).invoke()
    except Exception as error:
      print(error)

def run_multi_threaded(topology:CameraNetTopology):
  """
  Create one thread per camera in the topology.
  """
  threads = []
  for home_base in topology.home_bases:
    for camera_name in home_base.cameras:
      print('Starting {}/{}\n'.format(home_base.name, camera_name))
      config = Configuration(
        server_uri= "{}/{}".format(
          home_base.rtsp_address,
          camera_name),
        base_name = home_base.name,
        camera_name= camera_name,
        bucket_name= get_value('BUCKET'))

      thread = threading.Thread(target=run_continously, args=(config,))
      threads.append(thread)
      thread.start()

  for t in threads:
    t.join()

if __name__ == '__main__':
  signal(SIGTERM, shutdown)

  # Run topology...
  topology = CameraNetTopology()
  run_multi_threaded(topology)
