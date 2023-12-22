import os
import random
import time
from typing import Dict
import json
from kafka import KafkaProducer

from locust import User, events, task, constant

from src.constants import PARAMS_JSON_FILENAME
from src.olaf.custom_event_handler import add_session_dir_arg, on_test_quit
from src.olaf.datamodel import KafkaProducerUserParams

events.init_command_line_parser.add_listener(add_session_dir_arg)
events.quitting.add_listener(on_test_quit)

NAME = "kafka_producer"
REQUEST_TYPE = "kafka_producer"


class KafkaProducerImpl(KafkaProducer):

    def __init__(self, bootstrap_servers: str, sasl_username: str, sasl_password: str,
                 kafka_config: Dict, kafka_producer_config: Dict):
        config = kafka_config
        config.update(kafka_producer_config)
        config["bootstrap_servers"] = bootstrap_servers
        config["sasl_plain_username"] = sasl_username
        config["sasl_plain_password"] = sasl_password

        super().__init__(**config)

    def push_message(self, topic, message):
        start_time = time.perf_counter()
        request_meta = {
            "request_type": REQUEST_TYPE,
            "name": NAME,
            "response_length": 0,
            "response": None,
            "context": {},
            "exception": None,
        }
        try:
            self.send(topic=topic, key=None,
                      value=json.dumps(message).encode('utf-8'),
                      )
            self.flush()
        except Exception as err:
            request_meta["exception"] = err

        request_meta["response_time"] = (time.perf_counter() - start_time) * 1000
        events.request.fire(**request_meta)
        return request_meta["response"]


class KafkaProducerUser(User):
    wait_time = constant(0)

    def __init__(self, *args, **kwargs):
        super(KafkaProducerUser, self).__init__(*args, **kwargs)
        session_path = self.environment.parsed_options.session_dir
        with open(os.path.join(session_path, PARAMS_JSON_FILENAME)) as f:
            self.params = KafkaProducerUserParams.parse_raw(f.read())

        self.client = KafkaProducerImpl(bootstrap_servers=self.params.bootstrap_server,
                                        sasl_username=self.params.ssl_username.get_secret_value(),
                                        sasl_password=self.params.ssl_password.get_secret_value(),
                                        kafka_config=self.params.kafka_config,
                                        kafka_producer_config=self.params.kafka_producer_config,
                                        )
        self.req = self.params.query_json
        self.topic = self.params.topic_name

    def on_stop(self):
        self.client.close(timeout=5)

    @task
    def sm(self):
        self.client.push_message(topic=self.topic,
                                 message=random.choice(self.req))
