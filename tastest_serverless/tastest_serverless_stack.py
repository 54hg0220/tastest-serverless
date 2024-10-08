from aws_cdk import (
    Stack,
    aws_lambda as aws_lambda,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_iam as iam,
)
from constructs import Construct

class TastestServerlessStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 获取现有的VPC
        vpc = ec2.Vpc.from_lookup(self, "VPC",
            vpc_id="vpc-0cbbd4a88f961eb3d"
        )

        # 创建Lambda安全组
        lambda_sg = ec2.SecurityGroup(self, "LambdaSG",
            vpc=vpc,
            description="Security group for Lambda function",
            allow_all_outbound=True
        )

        # 获取RDS安全组
        rds_sg = ec2.SecurityGroup.from_security_group_id(
            self, "RDSSG",
            security_group_id="sg-06db1e8fdfd836707"
        )

        # 允许从Lambda安全组访问RDS
        rds_sg.add_ingress_rule(
            peer=lambda_sg,
            connection=ec2.Port.tcp(3306),
            description="Allow Lambda to access RDS"
        )

        pymysql_layer = aws_lambda.LayerVersion(
            self, "PymysqlLayer",
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_9],
            code=aws_lambda.Code.from_asset("lambda_layer"),
            description="Layer with pymysql library"
        )

        # Lambda 创建
        lambda_function = aws_lambda.Function(
            self, "RDSAccessFunction",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=aws_lambda.Code.from_asset("lambda"),
            vpc=vpc,
            security_groups=[lambda_sg],
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            allow_public_subnet=True,
            environment={
                "DB_HOST": "tastest.ch26w824uzzb.eu-central-1.rds.amazonaws.com",
                "DB_NAME": "tastest2",
                "DB_USER": "admin",
                "DB_PASSWORD": "JxUFKFqhOzNe5b4oc2jf"
            },
            layers=[pymysql_layer] #Lambda layer
        )

        # 添加RDS访问权限
        lambda_function.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "rds-db:connect",
                "rds:DescribeDBInstances"
            ],
            resources=["*"]
        ))

        # 输出Lambda函数的ARN
        self.output_props = {
            'lambda_arn': lambda_function.function_arn
        }