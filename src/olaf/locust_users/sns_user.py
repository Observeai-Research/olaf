import json
import os
import random
import time

import boto3
import botocore.config
from locust import User, events, task, constant

from src.constants import PARAMS_JSON_FILENAME
from src.olaf.custom_event_handler import add_session_dir_arg, on_test_quit
from src.olaf.datamodel import SNSUserParams

events.init_command_line_parser.add_listener(add_session_dir_arg)
events.quitting.add_listener(on_test_quit)

NAME = "sns"
REQUEST_TYPE = "sns_publish_message"


class SNSUser(User):
    wait_time = constant(0)

    def __init__(self, *args, **kwargs):
        super(SNSUser, self).__init__(*args, **kwargs)
        session_path = self.environment.parsed_options.session_dir
        with open(os.path.join(session_path, PARAMS_JSON_FILENAME)) as f:
            self.params = SNSUserParams.parse_raw(f.read())

        sns = boto3.resource('sns',
                             region_name=self.params.aws_region,
                             aws_access_key_id=self.params.access_key.get_secret_value(),
                             aws_secret_access_key=self.params.secret_key.get_secret_value(),
                             aws_session_token=self.params.session_token.get_secret_value() if self.params.session_token.get_secret_value() else None,
                             config=botocore.config.Config(read_timeout=60,
                                                           max_pool_connections=100,
                                                           retries={
                                                               'max_attempts': 4},
                                                           ))
        self.sns_topic = sns.Topic(arn=self.params.sns_arn)

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
            response = self.sns_topic.publish(Message=json.dumps(req),
                                              MessageAttributes=self.message_attributes,
                                              )
        except Exception as err:
            request_meta["exception"] = err

        request_meta["response_time"] = (time.perf_counter() - start_time) * 1000
        events.request.fire(**request_meta)
        return request_meta["response"]
