#!/usr/bin/env python3
import os

import aws_cdk as cdk

from tastest_serverless.tastest_serverless_stack import TastestServerlessStack


app = cdk.App()
TastestServerlessStack(app, "TastestServerlessStack",
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
)

app.synth()
