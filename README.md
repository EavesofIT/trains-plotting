# trains-plotting

## Hackathon Ideas

1. Identify Railcar serial numbers
    1. Push a bunch of good and bad images of railcars to the S3 bucket for analysis
        1. Ensure we can identify serials in good images and bad ones
            1. If we can't identify bad ones, alert some other process
2. Integration with a CMMS
    1. Push notifications to CMMS when a railcar image is added to S3
3. Count number of railcars added into S3
    1. Ensure we have all railcars accounted for by our process
4. Do a very basic estimation if there is railcar damage
    1. Obviously stuff, missing wheels etc

## Inspection Points

1. The tank car shows of abrasion, corrosion, cracks, dents, distortions, defects in welds, or any other condition that may make the tank car unsafe for transportation
2. The tank car was in an accident and shows evidence of damage to an extent that may adversely affect its capability to retain its contents or to otherwise remain railworthy
3. The tank bears evidence of damage caused by fire

<https://www.law.cornell.edu/cfr/text/49/180.509>

## Design Pattern

1. Add image to S3 bucket
2. Notify Lambda function upon addition of image
3. Lambda funs rekognition analysis
    1. It should find a value of 2-4 letters and 5-6 numbers
    2. Ensure Confidence is over 9000(95%)!
4. Lambda selects the "Detected Text"
5. Lambda tags an image with the tag "railcar_serial" : "DetectedText Value"
6. Alert/Notify off of the tagging update (if possible only for "DetectedText")
    1. Run Lambda function to alert a CMMS (dumby api)
