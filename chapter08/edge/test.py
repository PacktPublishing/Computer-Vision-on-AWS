import time
import numpy as np
import cv2
import grpc
import edge_agent_pb2 as pb2
from edge_agent_pb2_grpc import (
    EdgeAgentStub
)
import sys
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
import time as t
import json
import sys, os

ENDPOINT = "endpoint_name"
CLIENT_ID = "client_id"
MODEL_COMPONENT = "l4vmanufacturingcomponent"
PATH_TO_CERTIFICATE = "/greengrass/v2/thingCert.crt"
PATH_TO_PRIVATE_KEY = "/greengrass/v2/privKey.key"
PATH_TO_AMAZON_ROOT_CA_1 = "/greengrass/v2/rootCA.pem"
TOPIC = "l4vmanufacturing/testclient"
SAMPLE_FILE = "/home/ubuntu/environment/sample_images/anomaly/image-2020-04-22-10-51-51-85-cropped-right-top.jpg"


def run_inference(model_component, image_file_name):
    img = cv2.imread(image_file_name)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    cv2.imwrite('frame.bmp',img)
    with grpc.insecure_channel('unix:///tmp/aws.iot.lookoutvision.EdgeAgent.sock') as channel:
        stub = EdgeAgentStub(channel)
        h, w, c = img.shape
        print('input image shape: '+str(img.shape))
        start = time.time()
        response = stub.DetectAnomalies(
            pb2.DetectAnomaliesRequest(
                    model_component=model_component,
                    bitmap=pb2.Bitmap(
                        width=w,
                        height=h,
                        byte_data=bytes(img.tobytes())
                        )
                    )
        )
        inference_call_time_in_ms = round((time.time() - start)*1000)
        #print(f'got a local response in {inference_call_time_in_ms} ms')
        return response.detect_anomaly_result

def analyse_response(detect_anomaly_result):
    if not detect_anomaly_result.is_anomalous:
        print(f'the image has NO anomaly - confidence {detect_anomaly_result.confidence}')
    else:
        print(f'the image has an anomaly - confidence {detect_anomaly_result.confidence}')
       # if detect_anomaly_result.anomaly_mask:
        #    print(f'there is an anomaly mask with width {detect_anomaly_result.anomaly_mask.width} and height {detect_anomaly_result.anomaly_mask.height}')
         #   mask_bytes = detect_anomaly_result.anomaly_mask.byte_data
          #  print('the following anomalies are declared in the mask:')
           # for anomaly in detect_anomaly_result.anomalies:
            #    pixel_anomaly = anomaly.pixel_anomaly
             #   print(f'anomaly named {anomaly.name} with pixel_anomaly color {pixel_anomaly.hex_color} and total percentage area {pixel_anomaly.total_percentage_area}')


def create_result_html(detect_anomaly_result, image_file_name):
    with open('result.html', 'w') as f:
        f.write(f'<html><head><title>Inference result</title><meta http-equiv="refresh" content="1" ><head><body><h1>Inference result</h1>')
        f.write(f'<p>run inference on image {image_file_name} </p>')
        if not detect_anomaly_result.is_anomalous:
            f.write(f'<b> no anomaly detected </b><br/>')
        else:
            f.write(f'<b color="red">anomaly detected </b><br/><br/>')
        f.write(f'<img src="{image_file_name}"')
        f.write(f'<body></html>')


def send_mqtt(detect_anomaly_result):
   event_loop_group = io.EventLoopGroup(1)
   host_resolver = io.DefaultHostResolver(event_loop_group)
   client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
   mqtt_connection = mqtt_connection_builder.mtls_from_path(
                    endpoint=ENDPOINT,
                    cert_filepath=PATH_TO_CERTIFICATE,
                    pri_key_filepath=PATH_TO_PRIVATE_KEY,
                    client_bootstrap=client_bootstrap,
                    ca_filepath=PATH_TO_AMAZON_ROOT_CA_1,
                    client_id=CLIENT_ID,
                    clean_session=False,
                    keep_alive_secs=6
                    )
   print(f'Connecting to {ENDPOINT} with client ID "{CLIENT_ID}"...')
   connect_future = mqtt_connection.connect()
   connect_future.result()
   print("Connected!")
   print('Begin Publish')
   data = "{} [{}]".format(str(detect_anomaly_result),1)
   message = {"message" : data, "is_anomalous": detect_anomaly_result.is_anomalous, "confidence": detect_anomaly_result.confidence}
   mqtt_connection.publish(topic=TOPIC, payload=json.dumps(message), qos=mqtt.QoS.AT_LEAST_ONCE)
   print("Published: '" + json.dumps(message) + "' to the topic: " + TOPIC)
   t.sleep(0.1)
   print('Publish End')
   disconnect_future = mqtt_connection.disconnect()
   disconnect_future.result()


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        image_file_name = SAMPLE_FILE
    else:
        image_file_name = sys.argv[1]
    print(f'run inference on model component "{MODEL_COMPONENT}" with image {image_file_name}')
    detect_anomaly_result = run_inference(MODEL_COMPONENT, image_file_name)
    analyse_response(detect_anomaly_result)
    send_mqtt(detect_anomaly_result)
    create_result_html(detect_anomaly_result, image_file_name)
