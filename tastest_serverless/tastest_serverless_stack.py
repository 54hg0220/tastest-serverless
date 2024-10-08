from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_s3 as s3,
    aws_sqs as sqs,
    Duration,
)
from constructs import Construct

class TastestServerlessStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Existing VPC
        vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_id="vpc-0cbbd4a88f961eb3d")

        vpc.add_interface_endpoint(
            "SQSEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SQS
        )

        # Lambda Security Group
        lambda_sg = ec2.SecurityGroup(self, "LambdaSG",
            vpc=vpc,
            description="Security group for Lambda function",
            allow_all_outbound=True
        )

        # RDS Security Group
        rds_sg = ec2.SecurityGroup.from_security_group_id(
            self, "RDSSG",
            security_group_id="sg-06db1e8fdfd836707"
        )

        # Allow Lambda to access RDS
        rds_sg.add_ingress_rule(
            peer=lambda_sg,
            connection=ec2.Port.tcp(3306),
            description="Allow Lambda to access RDS"
        )

        pymysql_layer = _lambda.LayerVersion(
            self, "PymysqlLayer",
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            code=_lambda.Code.from_asset("lambda_layer"),
            description="Layer with pymysql library"
        )
        
        # S3 Bucket
        s3_bucket = s3.Bucket.from_bucket_name(self, "ExistingS3Bucket", "tastest-german")

        # Create SQS Queue
        queue = sqs.Queue(
            self, "MediapipeProcessingQueue",
            visibility_timeout=Duration.seconds(300),  # Match with Lambda timeout
        )

        # First Lambda Function
        first_lambda = _lambda.Function(
            self, "FirstLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=_lambda.Code.from_asset("lambda"),
            vpc=vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            allow_public_subnet=True,
            environment={
                "DB_HOST": "tastest.ch26w824uzzb.eu-central-1.rds.amazonaws.com",
                "DB_NAME": "tastest2",
                "DB_USER": "admin",
                "DB_PASSWORD": "JxUFKFqhOzNe5b4oc2jf",
                "SQS_QUEUE_URL": queue.queue_url,  # Add SQS Queue URL
            },
            timeout=Duration.seconds(120),
            layers=[pymysql_layer]
        )

        # Second Lambda Function (MediaPipe Processing)
        mediapipe_lambda = _lambda.DockerImageFunction(
            self, "MediapipeLambdaFunction",
            code=_lambda.DockerImageCode.from_image_asset("lambda/mediapipe_processing"),
            vpc=vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            allow_public_subnet=True,
            timeout=Duration.seconds(300),
            memory_size=2048
        )

        # Grant permissions to Lambda functions
        s3_bucket.grant_read_write(first_lambda)
        s3_bucket.grant_read_write(mediapipe_lambda)
        queue.grant_send_messages(first_lambda)
        queue.grant_consume_messages(mediapipe_lambda)

        # Configure SQS to trigger the second Lambda
        mediapipe_lambda.add_event_source_mapping(
            "SQSTrigger",
            event_source_arn=queue.queue_arn,
            batch_size=1
        )

        first_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "rds-db:connect",
                "rds:DescribeDBInstances",
                "sqs:SendMessage",
                "sqs:GetQueueUrl",
                "sqs:GetQueueAttributes"
            ],
            resources=["*"]
        ))

        mediapipe_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "s3:GetObject",
                "s3:PutObject",
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes",
                "sqs:ChangeMessageVisibility"
            ],
            resources=[
                f"{s3_bucket.bucket_arn}/*",
                queue.queue_arn
            ]
        ))

        # Output Lambda function ARNs and SQS Queue URL
        self.output_props = {
            'first_lambda_arn': first_lambda.function_arn,
            'mediapipe_lambda_arn': mediapipe_lambda.function_arn,
            'sqs_queue_url': queue.queue_url
        }