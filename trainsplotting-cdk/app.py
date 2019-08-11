#!/usr/bin/env python3

from aws_cdk import core

from trainsplotting_cdk.trainsplotting_cdk_stack import TrainsplottingCdkStack


app = core.App()
TrainsplottingCdkStack(app, "trainsplotting-cdk", env={ account: '650457438316', 'region': 'us-east-2'})

app.synth()
