# lambda/index.py

import os
import pymysql
import json

def handler(event, context):
    try:
        conn = pymysql.connect(
            host=os.environ['DB_HOST'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            database=os.environ['DB_NAME']
        )

        with conn.cursor() as cursor:
            cursor.execute("SELECT NOW() as current_time")
            result = cursor.fetchone()

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully connected to RDS',
                'current_time': str(result[0])
            })
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to connect to RDS',
                'error': str(e)
            })
        }
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()