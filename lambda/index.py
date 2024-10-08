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
            # 使用 tastest2 数据库
            cursor.execute("USE tastest2")
            
            # 执行指定的查询
            query = """
            SELECT t.collection_id, t.candidate_session_id, s.candidate_id 
            FROM test_result_files t 
            JOIN candidate_sessions s ON s.id = t.candidate_session_id 
            WHERE t.id = "1OD_YGbrPK9aLAGJyPLC1"
            """
            cursor.execute(query)
            result = cursor.fetchone()

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Query executed successfully',
                'result': {
                    'collection_id': result[0] if result else None,
                    'candidate_session_id': result[1] if result else None,
                    'candidate_id': result[2] if result else None
                }
            }, default=str)
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to execute query',
                'error': str(e)
            })
        }
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()