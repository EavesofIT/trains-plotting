import re
import sys
import pymysql
import boto3
import botocore
import json
import random
import time
import os
from botocore.exceptions import ClientError
from datetime import datetime

# rds settings
rds_host = os.environ['db_endpoint_address']
name = os.environ['db_user_name']
db_name = os.environ['db_name']


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
    
    print("Region Name")
    print(region_name)
    try:
        print("Trying to get secret")
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        print("Secret response below")
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
    drop_initial_textdata = textdata[textdata.find('Text Detected : ')+len('Text Detected : '):]
    splittextdata = drop_initial_textdata.split(',')
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
            # Confidence is showing up as the same value
            
            # Need to handle the use case where there are more than one, they will currently overwrite
            break
    print ("Serial Below")
    print(serialnumber)

    strtest = textdata
    object_name = strtest[strtest.find('object "')+len('object "'):strtest.find('" from bucket')]
    bucket_name = strtest[strtest.find('from bucket "')+len('from bucket "'):strtest.find('" at 2')]

    
    # Connect to RDS DB here
    
    item_count = 0
    try:
        openConnection()
        with conn.cursor() as cur:
            #cur.execute("select * from trainsPlotting_carimage")
            serialinsertsql = ("select * from trainsPlotting_railcar where rail_car_id=%s")
            select_railcarid = cur.execute(serialinsertsql, (serialnumber))
            print("Railcar ID below")
            print(select_railcarid)
            rowid = None
            if select_railcarid == 0:
                print("No Records Found, insertting")
                serialinsertsql = ("INSERT INTO `trainsPlotting_railcar` (rail_car_id,car_type) VALUES (%s,%s)")
                cur.execute(serialinsertsql, (serialnumber,'rail_car'))
                rowid = cur.lastrowid
            else:
                print("Railcar ID")
                rowid = cur.fetchone()[0]
                print(rowid)
            object_path = "https://{}.s3.{}.amazonaws.com/{}".format(bucket_name,region_name,object_name)
            sql = ("INSERT INTO `trainsPlotting_carimage` (source_key,rail_car_id,image_date,notes) VALUES (%s,%s,%s,%s)")
            cur.execute(sql, (object_path, rowid, str(datetime.now()), 'test',))
            for row in cur:
                item_count += 1
                print(row)
                # print(row)
    except Exception as e:
        # Error while opening connection or processing
        print(e)
    finally:
        print("Closing Connection")
        if(conn is not None and conn.open):
            conn.commit()
            conn.close()

    content =  "Selected %d items from RDS MySQL table" % (item_count)
    response = {
        "statusCode": 200,
        "body": content,
        "headers": {
            'Content-Type': 'text/html',
        }
    }
    return response    


    # 
    # Send the event to the next lambda which should start the deeper analysis for inspection points, after successfully storing in DynamoDB
    #
