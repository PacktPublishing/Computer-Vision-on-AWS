import boto3

region_name = 'us-east-2'
bucket_name = 'ch04-hotel-use2'
collection_id="HotelCollection"
rekognition = boto3.client('rekognition',region_name=region_name)

def print_faces(faces):
    counter=0
    for face in faces['FaceDetails']:
        counter+=1
        age_range = face['AgeRange']
        gender = face['Gender']
        emotions = face['Emotions']

        age = (age_range['High'] + age_range['Low'])/2
        emotions.sort(key=lambda x: x['Confidence'], reverse=True)
        top_emotion = emotions[0]

        print('Person %d is %s(%2.2f%%) around %d age and %s(%2.2f%%) state.' % (
            counter,
            gender['Value'],
            gender['Confidence'],
            age,
            top_emotion['Type'],
            top_emotion['Confidence']
        ))

def has_only_one_face(faces):
    if len(faces['FaceDetails']) == 1:
       return True
    return False

def is_facing_forward(face):
    for dimension in ['Pitch','Roll','Yaw']:
        value = face['Pose'][dimension]
        if not (-45 < value and value < 45):
            return False
    return True

def has_sunglasses(face):
    sunglasses = face['Sunglasses']['Value']
    return sunglasses

def is_well_lit(face):
    if face['Quality']['Brightness'] < 25:
        return False    
    return True

def check_faces(faces):
    if not has_only_one_face(faces):
        print('Incorrect face count.')
        return False

    user_face = faces['FaceDetails'][0]
    if not is_facing_forward(user_face):
        print('Customer not facing forward')
        return False

    if has_sunglasses(user_face):
        print('Please take off sunglasses.')
        return False

    if not is_well_lit(user_face):
        print('The image is blurry')
        return False

def print_search_results(search_response):
    for match in search_response['FaceMatches']:
        externalImageId = match['Face']['ExternalImageId']
        confidence = match['Face']['Confidence']

        print('This image is %s (%2.2f%% confidence)' % (
            externalImageId,
            confidence
        ))

def top_search_result(search_response):
    top_result = None
    top_confidence = 0
    for match in search_response['FaceMatches']:
        externalImageId = match['Face']['ExternalImageId']
        confidence = match['Face']['Confidence']

        if confidence > top_confidence:
            top_result = externalImageId
    return top_result

def print_header(text):
    print('=======================')
    print(text)
    print('=======================')

if __name__ == "__main__":
    
    alias = 'nbachmei'
    image_name = 'images/Nate-Bachmeier.png'
    search_image = 'images/SearchFacesByImageExample.jpg'

    print_header('Detecting Faces...')
    faces = rekognition.detect_faces(
        Attributes=['ALL'],
        Image={
        'S3Object':{
            'Bucket': bucket_name,
            'Name': image_name
        }})

    if not check_faces(faces):
        print("Unable to use the image.")
        exit(1)

    print_header("Finding existing image...")
    response = rekognition.search_faces_by_image(
        CollectionId=collection_id,
        Image={
            'S3Object':{
                'Bucket': bucket_name,
                'Name': image_name
            }
        })

    existing_user = top_search_result(response)
    if existing_user is None:
        print_header("User doesn't exist indexing....")
        rekognition.index_faces(
        CollectionId = collection_id,
        ExternalImageId=alias,
        Image={
            'S3Object':{
                'Bucket': bucket_name,
                'Name': image_name
            }
        })

    print_header("Searching with alternative image....")
    response = rekognition.search_faces_by_image(
        CollectionId=collection_id,
        Image={
            'S3Object':{
                'Bucket': bucket_name,
                'Name': search_image
            }
        })
    
    user_name = top_search_result(response)
    print('Alias of second image is %s' % user_name)
