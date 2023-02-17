import boto3

bucket_name = 'cv-on-aws-book-nbachmei'
photo='06_ContentModeration/images/swimwear.jpg'
region_name = 'us-east-2'
rekognition = boto3.client('rekognition', region_name=region_name)

ALLOWED_SUGGESTIVE_LABELS= [
    'Female Swimwear Or Underwear',
    'Male Swimwear Or Underwear']

def contains_appropriate_attire(detect_moderation_response):
    for label in detect_moderation_response['ModerationLabels']:
        top_level = label['ParentName']
        secondary_level = label['Name']
        confidence = label['Confidence']

        if top_level == "Explicit Nudity":
            print('Explicit Nudity detected - %2.2f%%.' % confidence)
            return False

        if top_level == "Suggestive":
            if secondary_level not in ALLOWED_SUGGESTIVE_LABELS:
                print('Prohibited Suggestive[%s] detected - %2.2f%%.' % 
                    (secondary_level, confidence))
                return False
            else:                
                print('Allowed Suggestive[%s] detected - %2.2f%%.' % 
                    (secondary_level, confidence))

    return True

def contains_alcohol(detect_moderation_response):
    for label in detect_moderation_response['ModerationLabels']:
        top_level = label['ParentName']
        confidence = label['Confidence']

        if top_level == "Alcohol":
            print('Alcohol detected - %2.2f%%.' % confidence)
            return False

    return True  

def moderate_image(photo, bucket):    
    response = rekognition.detect_moderation_labels(
        Image={
            'S3Object':{
                'Bucket': bucket,
                'Name':photo
            }
        })

    if not contains_alcohol(response) and contains_appropriate_attire(response):
        return True
    return False

def main():    
    label_count=moderate_image(photo, bucket_name)
    print("Labels detected: " + str(label_count))
