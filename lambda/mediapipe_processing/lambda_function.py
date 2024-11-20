import logging
import os
import json
import boto3
import cv2
import mediapipe as mp
import numpy as np
import tempfile

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def download_from_s3(bucket, key):
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket, Key=key)
    return response['Body'].read()

def process_video(video_data):
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)
    
    # Create a temporary file with .mp4 extension
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
        temp_file.write(video_data)
        temp_file_path = temp_file.name
    
    try:
        # Open the video file
        cap = cv2.VideoCapture(temp_file_path)
        
        frame_count = 0
        all_frames_keypoints = []
        
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                break
            
            # Convert the BGR image to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Process the image
            results = hands.process(image)
            
            frame_keypoints = []
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    hand_keypoints = []
                    for landmark in hand_landmarks.landmark:
                        hand_keypoints.append({
                            'x': landmark.x,
                            'y': landmark.y,
                            'z': landmark.z
                        })
                    frame_keypoints.append(hand_keypoints)
            
            all_frames_keypoints.append({
                'frame': frame_count,
                'keypoints': frame_keypoints
            })
            
            frame_count += 1
        
        cap.release()
        return all_frames_keypoints
    
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

def upload_results_to_s3(bucket, key, data):
    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(data))

def handler(event, context):
    sqs = boto3.client('sqs')
    s3 = boto3.client('s3')
    queue_url = os.environ['SQS_QUEUE_URL']

    try:
        for record in event['Records']:
            # sqs message
            message_body = json.loads(record['body'])
            logger.info(f"Received message: {message_body}")

            # video download
            bucket = 'tastest-german'
            key = f"tastest3German/{message_body['file_name']}"
            logger.info(f"Downloading video from S3: {bucket}/{key}")
            response = s3.get_object(Bucket=bucket, Key=key)
            video_data = response['Body'].read()

            # processing
            logger.info("Processing video")
            result = process_video(video_data)

            # upload S3
            result_key = f"results/{message_body['candidate_id']}/{message_body['test_id']}_results.json"
            logger.info(f"Uploading results to S3: {bucket}/{result_key}")
            s3.put_object(Bucket=bucket, Key=result_key, Body=json.dumps(result))

            # Delete sqs messsage
            logger.info(f"Deleting message from SQS: {record['receiptHandle']}")
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=record['receiptHandle']
            )

        return {
            'statusCode': 200,
            'body': json.dumps('Processing completed successfully')
        }
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }