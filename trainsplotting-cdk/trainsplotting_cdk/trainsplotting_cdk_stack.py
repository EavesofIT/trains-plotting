from aws_cdk import (
    aws_s3 as s3,
    core
)


class TrainsplottingCdkStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        bucket = s3.Bucket(self, 
            "trainsplotting-ingestion",
            bucket_name="trainsplotting-ingestion",
            encryption=s3.BucketEncryption.S3_MANAGED,
        )
