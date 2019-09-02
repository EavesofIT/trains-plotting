from aws_cdk import (
    core,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_events as events,
    aws_lambda as lambda_,
    aws_events_targets as targets,
    aws_lambda_event_sources as lambdaevents,
    aws_sns as sns,
    aws_iam as iam,
    aws_dynamodb as dynamo
)


class TrainsplottingCdkStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create ingestion_bucket for image uploads
        ingestion_bucket = s3.Bucket(self,
            "trainsplotting-ingestion",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )

        #**********#
        # Could add another ingestion_bucket here and add the zip of the code to use in Lambda functions
        #**********#

        # Read code for processing rekognition results
        proc_results_filepath = "lambda_handlers/process-rekog-results.py"
        with open(proc_results_filepath, encoding="utf8") as file_process_results_process:
            rekogresults_code = file_process_results_process.read()

        # Creation of lambda function to process results of rekognition
        rekog_results_fn = lambda_.Function(
            self, "rekognition-results",
            code=lambda_.InlineCode(rekogresults_code),
            handler="index.main",
            timeout=core.Duration.seconds(150),
            runtime=lambda_.Runtime.PYTHON_3_7,
            memory_size=256
        )

        # SNS Topic for Rekognition to publish to when completed
        results_topic = sns.Topic(self,'rekognition-results-topic',
            display_name='rekognition-results-topic'
        )

        # Subscribe the lambda function to the SNS topic that Rekognition will use to publish finished results
        rekog_results_fn.add_event_source(lambdaevents.SnsEventSource(results_topic))

        proc_photo_ingestion_filepath = "lambda_handlers/photo-ingestion.py"
        with open(proc_photo_ingestion_filepath, encoding="utf8") as file_process_photo_ingestion:
            photoingestion_code = file_process_photo_ingestion.read()

        # Creation of lambda function to process new images and kick of rekognition
        photo_ingest_fn = lambda_.Function(
            self, "photo-ingestion",
            #code=lambda_.cfn_parameters or lambda_.ingestion_bucket may need to be used if code is bigger than 4KiB
            code=lambda_.InlineCode(photoingestion_code),
            handler="index.main",
            timeout=core.Duration.seconds(150),
            runtime=lambda_.Runtime.PYTHON_3_7,
            memory_size=256
        )
        # Add environment variable for the SNS Topic
        photo_ingest_fn.add_environment(key='TOPIC_ARN',value=results_topic.topic_arn)
        # Adding S3 event notification for Lambda function
        photo_ingest_fn.add_event_source(lambdaevents.S3EventSource(ingestion_bucket,events=[s3.EventType.OBJECT_CREATED]))
        # Add permission to publish to SNS for processing results
        photo_ingest_fn.add_to_role_policy(iam.PolicyStatement(actions=['sns:Publish'],resources=[results_topic.topic_arn]))
        # Add permission to get object from the ingestion_bucket
        bucket_objects_path = ingestion_bucket.bucket_arn + "/*"
        photo_ingest_fn.add_to_role_policy(iam.PolicyStatement(actions=['s3:GetObject'],resources=[bucket_objects_path]))
        photo_ingest_fn.add_to_role_policy(iam.PolicyStatement(actions=['rekognition:DetectText','rekognition:DetectLabels','rekognition:DetectModerationLabels'],resources=['*']))

        # Create DynamoDB table to contain JSON body returned by Rekognition
        partion_key_serial_number = dynamo.Attribute(
            name="serial_number",
            type=dynamo.AttributeType.STRING
        )
        rekog_results_table = dynamo.Table(self, "rekogitionResultsDB",
            partition_key=partion_key_serial_number
        )
        
        # Add permission for the Lambda function to putitems in the DynamoDB used to store the results from Rekog
        rekog_results_fn.add_to_role_policy(iam.PolicyStatement(
            actions=[
                #"dynamodb:BatchGetItem",
                #"dynamodb:GetItem",
                #"dynamodb:Query",
                #"dynamodb:Scan",
                "dynamodb:BatchWriteItem",
                "dynamodb:PutItem"
                #"dynamodb:UpdateItem"
            ],
            resources=[rekog_results_fn.function_arn])
        )

        rekog_results_fn.add_environment(key='DYNAMODB_NAME', value=rekog_results_table.table_name)
