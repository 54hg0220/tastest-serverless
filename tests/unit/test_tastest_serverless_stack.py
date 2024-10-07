import aws_cdk as core
import aws_cdk.assertions as assertions

from tastest_serverless.tastest_serverless_stack import TastestServerlessStack

# example tests. To run these tests, uncomment this file along with the example
# resource in tastest_serverless/tastest_serverless_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = TastestServerlessStack(app, "tastest-serverless")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
