#!/usr/bin/env python3
from constructs import Construct
import aws_cdk as cdk
from aws_cdk import (
    aws_iam as iam,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_sqs as sqs,
    aws_lambda as lambda_)

def read_file(filename)->str:
    with open(filename,'rt') as f:
        return f.read()

class VideoContentModerationStack(cdk.Stack):
    def __init__(self, scope:Construct, id:str, **kwargs)->None:
        super().__init__(scope, id, **kwargs)

        self.__create_resources()
        self.__create_outputs()
        self.__grant_access()
        self.__create_topic_subscriptions()
        self.__create_bucket_notifications()

    def __create_resources(self):
        self.bucket = s3.Bucket(self,'Bucket')

        self.topic = sns.Topic(self,'Topic')

        self.message_queue = sqs.Queue(self,'AuditQueue',
            retention_period=cdk.Duration.days(7))        

        self.rekognition_role = iam.Role(self,'RekognitionRole',
            assumed_by=iam.ServicePrincipal(service='rekognition'))        

        self.start_analysis_function = lambda_.Function(self,'StartAnalysisFunction',
            handler='index.lambda_handler',
            runtime=lambda_.Runtime.PYTHON_3_9,
            architecture= lambda_.Architecture.X86_64,
            code=lambda_.Code.from_inline(read_file('start-analysis_function.py')),
            environment={
                'BUCKET_NAME': self.bucket.bucket_name,
                'NOTIFICATION_CHANNEL_ROLEARN': self.rekognition_role.role_arn,
                'NOTIFICATION_CHANNEL_SNSTOPIC_ARN': self.topic.topic_arn
            })

        self.get_results_function = lambda_.Function(self,'GetResultsFunction',
            handler='index.lambda_handler',
            runtime=lambda_.Runtime.PYTHON_3_9,
            architecture= lambda_.Architecture.X86_64,
            code=lambda_.Code.from_inline(read_file('get-results_function.py')),
            environment={
                'BUCKET_NAME': self.bucket.bucket_name
            })

    def __create_topic_subscriptions(self):
        self.topic.add_subscription(subs.LambdaSubscription(self.get_results_function))
        self.topic.add_subscription(subs.SqsSubscription(self.message_queue,
            raw_message_delivery=True))

    def __create_bucket_notifications(self):
        self.bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.start_analysis_function))
        
        # self.bucket.add_event_notification(
        #     s3.EventType.OBJECT_CREATED,
        #     s3n.LambdaDestination(self.start_analysis_function),
        #     suffix='.mov')

    def __grant_access(self):
        self.topic.grant_publish(self.rekognition_role)
        self.bucket.grant_read(self.rekognition_role)
        self.bucket.grant_read_write(self.get_results_function.role)
        self.bucket.grant_read_write(self.start_analysis_function)

        self.start_analysis_function.role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name(
            managed_policy_name='AmazonRekognitionReadOnlyAccess'))
        self.get_results_function.role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name(
            managed_policy_name='AmazonRekognitionReadOnlyAccess'))
        
        self.get_results_function.role.attach_inline_policy(iam.Policy(self,'CloudWatchMetricsPolicy',
            document=iam.PolicyDocument(statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=['cloudwatch:PutMetricData'],
                    resources=['*']
                )])))

    def __create_outputs(self):
        cdk.CfnOutput(self,'NotificationChannel_RoleArn',
            export_name='NotificationChannel-RoleArn',
            value=self.rekognition_role.role_arn,
            description='The role used by Amazon Rekognition for publishing updates')
        cdk.CfnOutput(self,'NotificationChannelSNSTopicArn',
            export_name='NotificationChannel-SNSTopicArn',
            value=self.topic.topic_arn,
            description='The topic for receiving Amazon Rekognition notifications')
        cdk.CfnOutput(self,'VideoBucket',
            export_name='Video-InputBucket',
            value=self.bucket.bucket_name,
            description='The input Amazon S3 bucket for holding video files')

class VideoContentModerationApp(cdk.App):
    def __init__(self, **kwargs)->None:
        super().__init__(**kwargs)
        VideoContentModerationStack(self,'VideoContentModeration')

app = VideoContentModerationApp()
app.synth()