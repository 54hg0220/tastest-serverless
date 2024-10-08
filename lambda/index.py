import os
import json
import time
import logging
import boto3
import pymysql

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def connect_to_db():
    return pymysql.connect(
        host=os.environ['DB_HOST'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        database=os.environ['DB_NAME']
    )

def query_db(conn):
    with conn.cursor() as cursor:
        query = """
        SELECT t.collection_id, t.candidate_session_id, s.candidate_id, t.test_id, t.type, t.id as file_name
        FROM test_result_files t 
        JOIN candidate_sessions s ON s.id = t.candidate_session_id 
        WHERE t.id = "1OD_YGbrPK9aLAGJyPLC1"
        """
        cursor.execute(query)
        return cursor.fetchone()

def send_message_to_sqs(payload):
    sqs = boto3.client('sqs')
    queue_url = os.environ['SQS_QUEUE_URL']
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(payload)
    )
    return response

def handler(event, context):
    start_time = time.time()
    try:
        # 记录数据库连接时间
        db_connect_start = time.time()
        conn = connect_to_db()
        db_connect_time = time.time() - db_connect_start
        logger.info(f"Database connection time: {db_connect_time:.2f} seconds")
        
        # 记录数据库查询时间
        query_start = time.time()
        result = query_db(conn)
        query_time = time.time() - query_start
        logger.info(f"Database query time: {query_time:.2f} seconds")
        
        query_result = {
            'collection_id': result[0] if result else None,
            'candidate_session_id': result[1] if result else None,
            'candidate_id': result[2] if result else None,
            'test_id': result[3] if result else None,
            'file_type': result[4] if result else None,
            'file_name': result[5] if result else None
        }
        
        # 记录发送SQS消息的时间
        sqs_start = time.time()
        sqs_response = send_message_to_sqs(query_result)
        sqs_time = time.time() - sqs_start
        logger.info(f"SQS message send time: {sqs_time:.2f} seconds")
        
        total_time = time.time() - start_time
        logger.info(f"Total execution time: {total_time:.2f} seconds")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Processing initiated successfully',
                'result': query_result,
                'sqs_message_id': sqs_response['MessageId'],
                'execution_times': {
                    'db_connect': db_connect_time,
                    'db_query': query_time,
                    'sqs_send': sqs_time,
                    'total': total_time
                }
            }, default=str)
        }
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to process request',
                'error': str(e)
            })
        }
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()