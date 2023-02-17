import boto3
from json import loads

rekognition = boto3.client('rekognition')
cloudwatch = boto3.client('cloudwatch')

def get_complete_content_moderation_results(jobId):
    next_token = None
    complete_response = None
    while True:
        if next_token:
            response = rekognition.get_content_moderation(            
            JobId=jobId,
            NextToken=next_token)        
            complete_response['ModerationLabels'].extend(response['ModerationLabels'])
        else:
            response = rekognition.get_content_moderation(
            JobId=jobId)
            complete_response = response

        if 'NextToken' in response:
            next_token = response['NextToken']
        else:
            break
    return complete_response


def get_frequency(notification):
    moderation_results = get_complete_content_moderation_results(notification['JobId'])
    parent_frequency = {}
    for label in moderation_results['ModerationLabels']:
        name = label['ModerationLabel']['Name']
        parent = label['ModerationLabel']['ParentName']

        if len(parent) == 0:
            parent = 'TopLevel'
        if len(name) == 0:
            name = "None"

        if parent not in parent_frequency:
            parent_frequency[parent]= { name: 1 }
        else:
            if name not in parent_frequency[parent]:
                parent_frequency[parent][name]=1
            else:
                parent_frequency[parent][name] += 1
    return parent_frequency

def publish_metrics(frequency):
    metric_data = []
    for (parent,secondary) in frequency.items():
        metric_data.append({
            'MetricName':'ContentModeration',
            'Dimensions': [
                {
                    'Name': 'TopLevel',
                    'Value': str(parent),
                }
            ],
            'Value': sum(secondary.values()),
            'Unit':'Count',
        })
        for (name, count) in secondary.items():
            metric_data.append({
                'MetricName':'ContentModeration',
                'Dimensions': [
                    {
                        'Name': 'TopLevel',
                        'Value': str(parent),
                        'Name': 'Secondary',
                        'Value': str(name),
                    }
                ],
                'Value': count,
                'Unit':'Count',
            })

    cloudwatch.put_metric_data(
        Namespace='VideoContentModeration',
        MetricData=metric_data)

def lambda_handler(event,context):
    print(event)
    for record in event['Records']:
        notification = loads(record['Sns']['Message'])
        print(notification)
        frequency = get_frequency(notification)
        publish_metrics(frequency)

