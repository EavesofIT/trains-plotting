import re
import boto3
import json

def main(event, context):
    print("I'm running!")
    print("Add code to process Rekognition results and tag pictures!")
    print(event)
    print("Message below")
    print(event['Records'][0]['Sns']['Message'])
    
    #
    # Sort Rekognition results by confidence
    # We are looking for a 1-4 letter by 4-6 number "word" or two separate values with high confidence(>90)
    #

    # Remove spaces from the text when validating regex to see if it is the serial number
    # txtAARMarkTextPrepped = txtAARMarkText.replace(" ","")
    # regex = [a-zA-Z]{2,4}\d{4,6}\b
    # regex = \w{1,4}\W\d{4,6}
    # p = re.compile('(\w{1,4})(\d{4,6})')
    # m = p.search(txtAARMarkTextPrepped)
    # Search value = SHQX50757
    # m.group(0) = SHQX50757
    # m.group(1) = SHQX
    # m.group(2) = 50757
    # m.group(2)[1] = 0

    # Connect to RDS DB here

    # 
    # Send the event to the next lambda which should start the deeper analysis for inspection points, after successfully storing in DynamoDB
    #
