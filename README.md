# trains-plotting

Hackathon Ideas:
1 - Identify Railcar serial numbers
    Push a bunch of good and bad images of railcars to the S3 bucket for analysis
        Ensure we can identify serials in good images and bad ones
            If we can't identify bad ones, alert some other process
2 - Integration with a CMMS
    Push notifications to CMMS when a railcar image is added to S3
3 - Count number of railcars added into S3
    Ensure we have all railcars accounted for by our process
4 - Do a very basic estimation if there is railcar damage
    Obviously stuff, missing wheels etc

Inspection Points:
1 - The tank car shows of abrasion, corrosion, cracks, dents, distortions, defects in welds, or any other condition that may make the tank car unsafe for transportation
2 - The tank car was in an accident and shows evidence of damage to an extent that may adversely affect its capability to retain its contents or to otherwise remain railworthy
3 - The tank bears evidence of damage caused by fire

https://www.law.cornell.edu/cfr/text/49/180.509


Design Pattern:
Add image to S3 bucket
Notify Lambda function upon addition of image
Lambda funs rekognition analysis
    It should find a value of 2-4 letters and 5-6 numbers
    Ensure Confidence is over 9000(95%)!
Lambda selects the "Detected Text"
Lambda tags an image with the tag "railcar_serial" : "DetectedText Value"
Alert/Notify off of the tagging update (if possible only for "DetectedText")
    Run Lambda function to alert a CMMS (dumby api)
