import json
import os
import random
import time

import boto3
import botocore.config
from locust import User, events, task, constant

from src.constants import PARAMS_JSON_FILENAME
from src.olaf.custom_event_handler import add_session_dir_arg, on_test_quit
from src.olaf.datamodel import SQSUserParams

events.init_command_line_parser.add_listener(add_session_dir_arg)
events.quitting.add_listener(on_test_quit)

NAME = "sqs"
REQUEST_TYPE = "sqs_send_message"


class SQSUser(User):
    wait_time = constant(0)

    def __init__(self, *args, **kwargs):
        super(SQSUser, self).__init__(*args, **kwargs)
        session_path = self.environment.parsed_options.session_dir
        with open(os.path.join(session_path, PARAMS_JSON_FILENAME)) as f:
            self.params = SQSUserParams.parse_raw(f.read())

        sqs = boto3.resource('sqs',
                             region_name=self.params.aws_region,
                             aws_access_key_id=self.params.access_key.get_secret_value(),
                             aws_secret_access_key=self.params.secret_key.get_secret_value(),
                             aws_session_token=self.params.session_token.get_secret_value() if self.params.session_token.get_secret_value() else None,
                             config=botocore.config.Config(read_timeout=60,
                                                           max_pool_connections=100,
                                                           retries={
                                                               'max_attempts': 4},
                                                           ))

        self.queue = sqs.get_queue_by_name(QueueName=self.params.sqs_name)

        self.req = self.params.query_json
        self.message_attributes = self.params.message_attribute_json

    @task
    def sm(self):
        req = random.choice(self.req)
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
            response = self.queue.send_message(MessageBody=json.dumps(req),
                                               MessageAttributes=self.message_attributes
                                               )
        except Exception as err:
            request_meta["exception"] = err

        request_meta["response_time"] = (time.perf_counter() - start_time) * 1000
        events.request.fire(**request_meta)
        return request_meta["response"]
