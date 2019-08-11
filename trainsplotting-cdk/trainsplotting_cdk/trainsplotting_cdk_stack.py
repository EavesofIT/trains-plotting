from aws_cdk import (
    aws_s3 as s3,
    aws_events as events,
    aws_lambda as lambda_,
    aws_events_targets as targets,
    core
)


class TrainsplottingCdkStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        bucket = s3.Bucket(self, 
            "trainsplotting-ingestion",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )

        with open("lambda_handlers/photo-ingestion.py", encoding="utf8") as fp:
            photoingestion_code = fp.read()
        
        lambdaFn = lambda_.Function(
            self, "photo-ingestion",
            code=lambda_.InlineCode(photoingestion_code),
            handler="index.main",
            timeout=core.Duration.seconds(300),
            runtime=lambda_.Runtime.PYTHON_3_7,
        )
        