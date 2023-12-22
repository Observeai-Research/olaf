import socket

import psutil
from tinydb import TinyDB, Query

from src.olaf.user_drivers import (rest_get_driver, rest_post_driver,
                                   elasticsearch_read_driver, mongo_read_driver,
                                   sagemaker_inference_driver, aws_sqs_put_message_driver, aws_sns_put_driver,
                                   aws_lambda_driver, cocktail_driver, kafka_producer_driver,
                                   redis_stream_producer_driver, pine_cone_vector_search_driver,
                                   redis_vector_search_driver
                                   )
from src.streamlit_app.datamodel import service_config

db = TinyDB("load_test_db.json")

TEST_TYPE_TO_DRIVER_MAP = {
    "REST GET": rest_get_driver,
    "REST POST": rest_post_driver,
    "Elasticsearch": elasticsearch_read_driver,
    "MongoDB": mongo_read_driver,
    "Sagemaker": sagemaker_inference_driver,
    "SQS": aws_sqs_put_message_driver,
    "SNS": aws_sns_put_driver,
    "Lambda": aws_lambda_driver,
    "Kafka Producer": kafka_producer_driver,
    "Redis Stream Producer": redis_stream_producer_driver,
    "Cocktail": cocktail_driver,
    "PineCone Vector Search": pine_cone_vector_search_driver,
    "Redis Vector Search": redis_vector_search_driver
}


def stop_running_locust_pids():
    q = Query()
    for p in db.search(q.status == "running"):
        for pid in p.get("p_ids", []):
            try:
                proc = psutil.Process(pid)
                proc.terminate()
            except Exception as err:
                pass
    db.update({"status": "terminated"}, q.status == "running")


def prune_db_for_terminated_process():
    if len(db) > 1_000:
        q = Query()
        db.remove(q.status == "terminated")


def add_locust_pids_to_db(test_type, p_ids):
    db.insert({"resource": test_type,
               "status": "running",
               "p_ids": p_ids})
    return True


def get_log_message(log_event, message):
    return f"[OLA] [{log_event}] [{message}]"


def is_port_in_use(port=service_config.locust_config.port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0
