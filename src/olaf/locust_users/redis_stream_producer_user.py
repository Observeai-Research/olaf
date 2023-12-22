import os
import random
import time
from typing import Dict
import json
from redis import StrictRedis, Sentinel, RedisCluster

from locust import User, events, task, constant

from src.constants import PARAMS_JSON_FILENAME
from src.olaf.custom_event_handler import add_session_dir_arg, on_test_quit
from src.olaf.datamodel import RedisStreamUserParams

events.init_command_line_parser.add_listener(add_session_dir_arg)
events.quitting.add_listener(on_test_quit)

NAME = "redis_stream_producer"
REQUEST_TYPE = "redis_stream_producer"


class RedisStreamProducer:

    def __init__(self, redis_type, host: str, port: int, username: str, password: str):
        if redis_type == "strict":
            self.redis_client = StrictRedis(host=host, port=port, password=password)
        # elif redis_type == "sentient":
        #     self.redis_client = Sentinel(sentinels=None)
        elif redis_type == "cluster":
            self.redis_client = RedisCluster(host=host, port=port)
        else:
            raise NotImplementedError

    def close(self):
        self.redis_client.close()

    def push_message(self, stream_name, message):
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
            self.redis_client.xadd(name=stream_name,
                                   fields=message
                                   )
        except Exception as err:
            request_meta["exception"] = err

        request_meta["response_time"] = (time.perf_counter() - start_time) * 1000
        events.request.fire(**request_meta)
        return request_meta["response"]


class RedisStreamProducerUser(User):
    wait_time = constant(0)

    def __init__(self, *args, **kwargs):
        super(RedisStreamProducerUser, self).__init__(*args, **kwargs)
        session_path = self.environment.parsed_options.session_dir
        with open(os.path.join(session_path, PARAMS_JSON_FILENAME)) as f:
            self.params = RedisStreamUserParams.parse_raw(f.read())

        self.client = RedisStreamProducer(redis_type=self.params.redis_type,
                                          host=self.params.host,
                                          port=self.params.port,
                                          username=self.params.username.get_secret_value(),
                                          password=self.params.password.get_secret_value(),

                                        )
        self.req = self.params.query_json
        self.topic = self.params.stream_name

    def on_stop(self):
        self.client.close()

    @task
    def sm(self):
        self.client.push_message(stream_name=self.topic,
                                 message=random.choice(self.req))
