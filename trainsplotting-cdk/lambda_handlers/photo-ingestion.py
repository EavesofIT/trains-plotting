import json
import urllib.parse
import boto3
import os

def main(event, context):
    print("I'm running!")
    print("I'll update to run code that will process an image through Rekognition!")

    #
    # Below this is default code from a demo SAM AWS provides. We should tinker with it to get the actual data we need.
    # Ideally, we will only need to pull the serial and not EVERY bit of text that's found
    #

    msg = ""
    # Log event data received
    print("Received event: " + json.dumps(event, indent=2))
    # create S3 client
    s3 = boto3.client('s3')
    # create rekognition client
    rekog_client = boto3.client('rekognition')
    # Get bucket name
    bucket = event['Records'][0]['s3']['bucket']['name']
    # Get the object key
    object_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    # Get event name
    event_name = event['Records'][0]['eventName']
    event_time = event['Records'][0]['eventTime']
    # Get event region
    event_region = event['Records'][0]['awsRegion']

    sns_response = ""    
    # list to store image labels
    all_labels = list()
    all_texts = list()
    all_mod = list()
    if event_name.split(':')[0] != 'ObjectRemoved':
        try:
            msg = 'Event {0} triggered for object \"{1}\" from bucket \"{2}\" at {3} in region {4}'.format(event_name, object_key, bucket, event_time,event_region)
            response = s3.get_object(Bucket=bucket, Key=object_key)
            if response['ContentType'].split('/')[0] == 'image':

                response_labels = rekog_client.detect_labels(
                    Image={'S3Object': {'Bucket': bucket,'Name': object_key}                    
                    })

                response_text = rekog_client.detect_text(
                    Image={'S3Object': {'Bucket': bucket,'Name': object_key}                    
                    })

                for label in response_labels['Labels']:
                    all_labels.append("Name= " + label['Name'] + "; Confidence= " + str(label['Confidence']) )

                for txt in response_text['TextDetections']:
                    all_texts.append("Text= " + txt['DetectedText'] + "; Confidence= " + str(label['Confidence']) )

                image_type = str.lower(response['ContentType'].split('/')[1].strip())
                
                # only JPG ad PNG is supported by Detect Moderation
                if image_type in ['jpg', 'jpeg', 'png']:
                    print('Getting Moderation Labels')
                    for item in rekog_client.detect_moderation_labels(Image={'S3Object': {'Bucket': bucket,'Name': object_key}}, MinConfidence=30)['ModerationLabels']:
                        all_mod.append("Label= " + item['Name'] + "; Confidence= " + str(item['Confidence']) + "; ParentName= " + item['ParentName'])


                labels_string = ",".join(all_labels)
                text_string = ",".join(all_texts)
                
                msg = msg + "\nImage : {0} , Labels Count : {1} , Labels Detected : {2} ".format(object_key, len(all_labels),labels_string )
                msg = msg + "\nText Count: {0} , Text Detected : {1} ".format(len(all_texts), text_string)
                msg = msg + "\nModeration Label: {0}".format(",".join(all_mod))
                
                # log the output
                print(msg)
                
                # Create SNS Client
                sns_client = boto3.client('sns')
                # Publish Message to the Topic
                if msg != "":
                    sns_response = sns_client.publish(
                        TopicArn=os.environ['TOPIC_ARN'],
                        Message=msg,
                        MessageStructure='string')

        except Exception as exc:
            print('{0} Error getting object {1} from bucket {2} .'.format(exc.args[0], object_key, bucket))    
            
    return sns_response