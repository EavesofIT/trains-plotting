from aws_cdk import (
    core,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_events as events,
    aws_lambda as lambda_,
    aws_events_targets as targets,
    aws_lambda_event_sources as lambdaevents,
    aws_sns as sns
)


class TrainsplottingCdkStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        bucket = s3.Bucket(self, 
            "trainsplotting-ingestion",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        #**********#
        # Could add another bucket here and add the zip of the code to use in Lambda functions
        #**********#

        with open("lambda_handlers/photo-ingestion.py", encoding="utf8") as fp:
            photoingestion_code = fp.read()
        
        lambdaFn = lambda_.Function(
            self, "photo-ingestion",
            #code=lambda_.cfn_parameters or lambda_.bucket may need to be used if code is bigger than 4KiB
            code=lambda_.InlineCode(photoingestion_code),
            handler="index.main",
            timeout=core.Duration.seconds(300),
            runtime=lambda_.Runtime.PYTHON_3_7,
        )
        
        lambdaFn.add_event_source(lambdaevents.S3EventSource(bucket,events=[s3.EventType.OBJECT_CREATED]))
        #bucket.add_event_notification(s3.EventType.OBJECT_CREATED,s3n.LambdaDestination(lambdaFn))
        #ingestiontopic.add_subscription()
        #lambdaevents.S3EventSource(bucket,) ------ Runs, doesn't work
        #bucket.addEventNotification(s3.EventType.OBJECT_CREATED,) ----- Closeish, can't get the second or third object references to work
        #rule.add_target(targets.LambdaFunction(lambdaFn))
        #bucket.add_target(targets.LambdaFunction(lambdaFn))
        #bucket.add_event_notification(s3.EventType.OBJECT_CREATED,'photo-ingestion','*')
        #bucket.addEventNotification(s3.EventType.OBJECT_CREATED_PUT, s3n.LambdaDestination(topic)) https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_s3_notifications.html
