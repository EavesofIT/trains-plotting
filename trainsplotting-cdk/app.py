#!/usr/bin/env python3

from aws_cdk import core

from trainsplotting_cdk.trainsplotting_cdk_stack import TrainsplottingCdkStack


app = core.App()
TrainsplottingCdkStack(app, "trainsplotting-cdk")

app.synth()
