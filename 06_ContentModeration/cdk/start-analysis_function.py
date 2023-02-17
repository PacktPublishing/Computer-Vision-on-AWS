import boto3
from json import dumps
from os import environ
rekognition = boto3.client('rekognition')

NOTIFICATION_CHANNEL_ROLEARN = environ.get('NOTIFICATION_CHANNEL_ROLEARN')
NOTIFICATION_CHANNEL_SNSTOPIC_ARN = environ.get('NOTIFICATION_CHANNEL_SNSTOPIC_ARN')

def is_supported_file(name):
    name = str(name).lower()
    if name.endswith('.mp4') or name.endswith('.mov'):
        return True
    return False

def process_file(bucket, name):
    moderation_job = rekognition.start_content_moderation(
        NotificationChannel={
            'RoleArn': NOTIFICATION_CHANNEL_ROLEARN,
            'SNSTopicArn': NOTIFICATION_CHANNEL_SNSTOPIC_ARN
        },
        Video={
            'S3Object':{
                'Bucket':bucket,
                'Name':name
            }
        })
    print(dumps(moderation_job, indent=2))

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        name = record['s3']['bucket']['object']['key']

        if not is_supported_file(name):
            print("UNSUPPORTED FILE: s3://{}/{})".format(bucket,name))            
        else:
            print("StartContentModeration(s3://{}/{})".format(bucket,name))
            process_file(bucket, name)
        