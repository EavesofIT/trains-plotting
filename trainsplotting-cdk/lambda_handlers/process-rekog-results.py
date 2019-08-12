def main(event, context):
    print("I'm running!")
    print("Add code to process Rekognition results and tag pictures!")
    print(event)
    # Remove spaces from the text when validating regex to see if it is the serial number
    # regex = \w{1,4}\W\d{4,6}