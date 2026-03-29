"""
Connect Stack - AWS Connect IVR
Creates the Connect instance and Lambda integration.
Contact flow is created via the Console visual builder after deployment.
"""

import json
import hashlib
from aws_cdk import (
    Stack,
    aws_connect as connect,
    aws_iam as iam,
    CfnOutput,
)
from constructs import Construct
from stacks.api_stack import ApiStack


class ConnectStack(Stack):
    def __init__(
        self, scope: Construct, id: str, api_stack: ApiStack, **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        region = self.region
        account = self.account
        alias_suffix = hashlib.md5(account.encode()).hexdigest()[:6]

        orchestrator_lambda = api_stack.orchestrator_lambda

        # ============================================================
        # 1. Create AWS Connect Instance
        # ============================================================
        instance = connect.CfnInstance(
            self,
            "ConnectInstance",
            identity_management_type="CONNECT_MANAGED",
            attributes=connect.CfnInstance.AttributesProperty(
                inbound_calls=True,
                outbound_calls=False,
            ),
            instance_alias=f"rva311-bridge-{alias_suffix}",
        )

        # ============================================================
        # 2. Integrate Lambda with Connect
        # ============================================================
        lambda_integration = connect.CfnIntegrationAssociation(
            self,
            "LambdaIntegration",
            instance_id=instance.attr_arn,
            integration_type="LAMBDA_FUNCTION",
            integration_arn=orchestrator_lambda.function_arn,
        )

        # Grant Connect permission to invoke Lambda
        orchestrator_lambda.add_permission(
            "ConnectInvoke",
            principal=iam.ServicePrincipal("connect.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=f"arn:aws:connect:{region}:{account}:instance/*",
        )

        # Phone number is claimed manually via Connect Console
        # (auto-claim via CloudFormation is unreliable with DID availability)

        # ============================================================
        # Outputs
        # ============================================================
        CfnOutput(self, "ConnectInstanceArn",
                  value=instance.attr_arn,
                  description="AWS Connect Instance ARN")

        CfnOutput(self, "ConnectInstanceAlias",
                  value=f"rva311-bridge-{alias_suffix}",
                  description="Connect instance alias")

        CfnOutput(self, "ConnectConsoleURL",
                  value=f"https://rva311-bridge-{alias_suffix}.my.connect.aws",
                  description="Connect admin console URL")

        CfnOutput(self, "LambdaFunctionArn",
                  value=orchestrator_lambda.function_arn,
                  description="Lambda ARN integrated with Connect")

        CfnOutput(self, "NextSteps",
                  value="1) Open Connect Console  2) Create contact flow  3) Assign phone number to flow",
                  description="Manual steps to complete IVR setup")
