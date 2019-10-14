import sys
import pymysql
import boto3
import botocore
import json
import random
import time
import os
from botocore.exceptions import ClientError

# rds settings
rds_host = os.environ['db_endpoint_address']
name = os.environ['db_user_name']
db_name = os.environ['RDS_DB_NAME']


secret_name = os.environ['db_secret_arn']
my_session = boto3.session.Session()
region_name = my_session.region_name
conn = None


def openConnection():
    print("In Open connection")
    global conn
    password = "None"
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.
    
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        print(get_secret_value_response)
    except ClientError as e:
        print(e)
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            j = json.loads(secret)
            password = j['password']
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            print("password binary:" + decoded_binary_secret)
            password = decoded_binary_secret.password    
    
    try:
        if(conn is None):
            conn = pymysql.connect(
                rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
        elif (not conn.open):
            # print(conn.open)
            conn = pymysql.connect(
                rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)

    except Exception as e:
        print (e)
        print("ERROR: Unexpected error: Could not connect to MySql instance.")
        raise e


def main(event, context):
    print("I'm running!")
    print("Add code to process Rekognition results and tag pictures!")
    print(event)
    print("Message below")
    print(event['Records'][0]['Sns']['Message'])
    textdata = event['Records'][0]['Sns']['Message']
    splittextdata = textdata.split(';')
    serialnumber = ""
    for text in splittextdata:
        print(text)
        serialtext = text.replace(" ","")
        p = re.compile('[a-zA-Z]{2,4}\d{4,6}\\b')
        m = p.search(serialtext)
        if m is not None:
            print(m[0])
            serialnumber = m[0]
            # Also check the confidence and ensure about 66

            # Need to handle the use case where there are more than one, they will currently overwrite
    print ("Serial Below")
    print(serialnumber)








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
