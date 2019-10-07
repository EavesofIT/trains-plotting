from aws_cdk import (
    core,
    aws_ec2 as ec2,
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
        proc_results_filepath = "artifacts/lambda_handlers/process-rekog-results.py"
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

        proc_photo_ingestion_filepath = "artifacts/lambda_handlers/photo-ingestion.py"
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


        # Create VPC, subnets, and security groups
        trainsplotting_vpc = ec2.Vpc(self,'trainsplotting-vpc',
            cidr='10.0.0.0/21',
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                {"subnetType": ec2.SubnetType.ISOLATED,"name" : "application", "cidr_mask" : 22}
                ]
        )
        trainsplotting_sg = ec2.SecurityGroup(self,"trainsplotting-app-sg",
            vpc=trainsplotting_vpc
        )
        #trainsplotting_sg.add_ingress_rule(peer=ec2.Peer.any_ipv4, connection=railcar_inspection_table.attr_endpoint_port, description="This allows access for the Lambda to reach the RDS")
        trainsplotting_sg_connections = ec2.Connections()
        trainsplotting_sg_connections.add_security_group(trainsplotting_sg)
        #trainsplotting_sg_connections.allow_internally(port_range=ec2.Port(protocol=ec2.Protocol.TCP,string_representation="string",to_port=(railcar_inspection_table.attr_endpoint_port))
        
        
        # Create Aurora RDS table for recording of railcar inspection data
        # Add SSM parameter store of encrypted password
        db_user_name = "trainsplottingad"
        railcar_inspection_table = rds.DatabaseInstance(
            self, "trainsplotting-railcar-inspection",
            master_username=db_user_name,
            engine=rds.DatabaseInstanceEngine.MYSQL,
            instance_class=ec2.InstanceType("t2.small"),
            vpc=trainsplotting_vpc,
            allocated_storage=100,
            storage_encrypted=True,
            port=3306,
            vpc_placement=ec2.SubnetSelection(subnet_type=ec2.SubnetType.ISOLATED),
            #instance_identifier="someusefulname"
            #vpc_security_group_ids=[trainsplotting_sg.security_group_id]
        )

        # Grant read access to the lambda function to read the rds secret
        railcar_inspection_table.secret.grant_read(rekog_results_fn.role)

        # Add the environment variable with the DynamoDB name to the Rekognition results function
        #rekog_results_fn.add_environment(key='database_name', value=railcar_inspection_table.database_name)
        rekog_results_fn.add_environment(key='db_endpoint_address', value=railcar_inspection_table.db_instance_endpoint_address)
        rekog_results_fn.add_environment(key='db_endpoint_port', value=railcar_inspection_table.db_instance_endpoint_port)
        rekog_results_fn.add_environment(key='db_user_name', value=db_user_name)
        rekog_results_fn.add_environment(key='db_secret_arn', value=railcar_inspection_table.secret.secret_arn)



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
