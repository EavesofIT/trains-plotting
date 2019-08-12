from aws_cdk import (
    core,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_events as events,
    aws_lambda as lambda_,
    aws_events_targets as targets,
    aws_lambda_event_sources as lambdaevents,
    aws_sns as sns,
    aws_iam as iam
)


class TrainsplottingCdkStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create bucket for image uploads
        bucket = s3.Bucket(self, 
            "trainsplotting-ingestion",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        #**********#
        # Could add another bucket here and add the zip of the code to use in Lambda functions
        #**********#

        # Read code for processing rekognition results
        with open("lambda_handlers/process-rekog-results.py", encoding="utf8") as fp:
            rekogresults_code = fp.read()

        # Creation of lambda function to process results of rekognition
        rekogResultsFn = lambda_.Function(
            self, "rekognition-results",
            #code=lambda_.cfn_parameters or lambda_.bucket may need to be used if code is bigger than 4KiB
            code=lambda_.InlineCode(rekogresults_code),
            handler="index.main",
            timeout=core.Duration.seconds(150),
            runtime=lambda_.Runtime.PYTHON_3_7,
            memory_size=256
        )

        # SNS Topic for Rekognition to publish to when completed
        resultstopic = sns.Topic(self,'rekognition-results-topic',
            display_name='rekognition-results-topic'
        )

        # Subscribe the lambda function to the SNS topic that Rekognition will use to publish finished results
        rekogResultsFn.add_event_source(lambdaevents.SnsEventSource(resultstopic))


        with open("lambda_handlers/photo-ingestion.py", encoding="utf8") as fp:
            photoingestion_code = fp.read()
        
        # Creation of lambda function to process new images and kick of rekognition
        photoIngestFn = lambda_.Function(
            self, "photo-ingestion",
            #code=lambda_.cfn_parameters or lambda_.bucket may need to be used if code is bigger than 4KiB
            code=lambda_.InlineCode(photoingestion_code),
            handler="index.main",
            timeout=core.Duration.seconds(150),
            runtime=lambda_.Runtime.PYTHON_3_7,
            memory_size=256
        )
        # Add environment variable for the SNS Topic
        photoIngestFn.add_environment(key='TOPIC_ARN',value=resultstopic.topic_arn)
        # Adding S3 event notification for Lambda function
        photoIngestFn.add_event_source(lambdaevents.S3EventSource(bucket,events=[s3.EventType.OBJECT_CREATED]))
        # Add permission to publish to SNS for processing results
        photoIngestFn.add_to_role_policy(iam.PolicyStatement(actions=['sns:Publish'],resources=[resultstopic.topic_arn]))
        # Add permission to get object from the bucket
        photoIngestFn.add_to_role_policy(iam.PolicyStatement(actions=['s3:GetObject'],resources=[bucket.bucket_arn]))