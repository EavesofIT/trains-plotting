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
    aws_dynamodb as dynamo,
    aws_rds as rds
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
            self, "trainsplotting-rekognition-results",
            code=lambda_.InlineCode(rekogresults_code),
            handler="index.main",
            timeout=core.Duration.seconds(150),
            runtime=lambda_.Runtime.PYTHON_3_7,
            memory_size=256
        )

        # SNS Topic for Rekognition to publish to when completed
        rekog_results_snstopic = sns.Topic(self,'trainsplotting-rekognition-results-topic',
            display_name='rekognition-results-topic'
        )

        # Subscribe the lambda function to the SNS topic that Rekognition will use to publish finished results
        rekog_results_fn.add_event_source(lambdaevents.SnsEventSource(rekog_results_snstopic))

        proc_photo_ingestion_filepath = "lambda_handlers/photo-ingestion.py"
        with open(proc_photo_ingestion_filepath, encoding="utf8") as file_process_photo_ingestion:
            photoingestion_code = file_process_photo_ingestion.read()


        # Creation of lambda function to process new images and kick of rekognition
        photo_ingest_fn = lambda_.Function(
            self, "trainsplotting-photo-ingestion",
            #code=lambda_.cfn_parameters or lambda_.ingestion_bucket may need to be used if code is bigger than 4KiB
            code=lambda_.InlineCode(photoingestion_code),
            handler="index.main",
            timeout=core.Duration.seconds(150),
            runtime=lambda_.Runtime.PYTHON_3_7,
            memory_size=256
        )
        # Add environment variable for the SNS Topic
        photo_ingest_fn.add_environment(key='TOPIC_ARN',value=rekog_results_snstopic.topic_arn)
        # Adding S3 event notification for Lambda function
        photo_ingest_fn.add_event_source(lambdaevents.S3EventSource(ingestion_bucket,events=[s3.EventType.OBJECT_CREATED]))
        # Add permission to publish to SNS for processing results
        photo_ingest_fn.add_to_role_policy(iam.PolicyStatement(actions=['sns:Publish'],resources=[rekog_results_snstopic.topic_arn]))
        # Add permission to get object from the ingestion_bucket
        bucket_objects_path = ingestion_bucket.bucket_arn + "/*"
        photo_ingest_fn.add_to_role_policy(iam.PolicyStatement(actions=['s3:GetObject'],resources=[bucket_objects_path]))
        photo_ingest_fn.add_to_role_policy(iam.PolicyStatement(actions=['rekognition:DetectText','rekognition:DetectLabels','rekognition:DetectModerationLabels'],resources=['*']))


        # Create Aurora RDS table for recording of railcar inspection data
        # Add SSM parameter store of encrypted password
        railcar_inspection_table = rds.CfnDBCluster(
            self, "trainsplotting-railcar-inspection",
            master_username="trainsplottingadminuser",
            master_user_password="b*bsuruncl3",
            engine="aurora",
            scaling_configuration={"min_capactiy" : 1, "max_capacity" : 4},
            engine_mode="serverless",
            storage_encrypted=True,
            port=3306
        )
        #attr_endpoint_address
        #attr_endpoint_port
        #database_name

        
        # Add the environment variable with the DynamoDB name to the Rekognition results function
        rekog_results_fn.add_environment(key='database_name', value=railcar_inspection_table.database_name)


        # Create S3 bucket for Sagemaker Results storage
        sagemaker_results_bucket = s3.Bucket(self,
            "trainsplotting-sagemaker-results",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )


        # Create an SNS topic for our lambda functions to handle the inspection item processing
        inspection_event_snstopic = sns.Topic(self,'inspection_event_snstopic',
            display_name='inspection_event_snstopic'
        )
        # Add permission to publish to SNS for inspection item processing
        photo_ingest_fn.add_to_role_policy(iam.PolicyStatement(actions=['sns:Publish'],resources=[inspection_event_snstopic.topic_arn]))
        # Add environment variable for the SNS Topic
        rekog_results_fn.add_environment(key='TOPIC_ARN',value=inspection_event_snstopic.topic_arn)