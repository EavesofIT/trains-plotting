import re
import boto3

def main(event, context):
    print("I'm running!")
    print("Add code to process Rekognition results and tag pictures!")
    print(event)
    #
    # Put the event over to the DynamoDB
    #

    # Remove spaces from the text when validating regex to see if it is the serial number
    # txtAARMarkTextPrepped = txtAARMarkText.replace(" ","")
    # regex = \w{1,4}\W\d{4,6}
    # p = re.compile('(\w{1,4})(\d{4,6})')
    # m = p.search(txtAARMarkTextPrepped)
    # Search value = SHQX50757
    # m.group(0) = SHQX50757
    # m.group(1) = SHQX
    # m.group(2) = 50757
    # m.group(2)[1] = 0

    dynamodb = boto3.client('dynamodb')
    dynamodb.put_item(
        TableName='',
        Item={}
    )
    
    # 
    # Send the event to the next lambda which should start the deeper analysis for inspection points, after successfully storing in DynamoDB
    #