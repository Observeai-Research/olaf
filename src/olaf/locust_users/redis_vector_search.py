import os
import random
import time
from typing import Dict
import json
import numpy as np
from ast import literal_eval
from redis import Redis
from redis.commands.search.query import Query

from locust import User, events, task, constant

from src.constants import PARAMS_JSON_FILENAME
from src.olaf.custom_event_handler import add_session_dir_arg, on_test_quit
from src.olaf.datamodel import RedisVectorSearchUserParams

events.init_command_line_parser.add_listener(add_session_dir_arg)
events.quitting.add_listener(on_test_quit)

NAME = "redis_vector_search"
REQUEST_TYPE = "redis_vector_search"


class RedisVectorSearch:

    def __init__(self, host: str, port: int, password: str, index_name: str):
        self.redis_client = Redis(
          host=host,
          port=port,
          password=password)
        self.index_name = index_name

    def close(self):
        self.redis_client.close()

    def vector_search(self, message):
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
            topK = message['topK']
            ITEM_KEYWORD_EMBEDDING_FIELD = message['field_name']
            RETURN_FIELDS = literal_eval(message['return_fields'])
            q = Query(f'*=>[KNN {topK} @{ITEM_KEYWORD_EMBEDDING_FIELD} $vec_param AS vector_score]').sort_by(
                'vector_score').paging(0, topK).return_fields(*RETURN_FIELDS).dialect(2)
            query_vector = np.array(literal_eval(message['embedding'])).astype(np.float32).tobytes()
            params_dict = {"vec_param": query_vector}

            # Execute the query
            self.redis_client.ft(self.index_name).search(q, query_params=params_dict)
        except Exception as err:
            request_meta["exception"] = err

        request_meta["response_time"] = (time.perf_counter() - start_time) * 1000
        events.request.fire(**request_meta)
        return request_meta["response"]


class RedisVectorSearchUser(User):
    wait_time = constant(0)

    def __init__(self, *args, **kwargs):
        super(RedisVectorSearchUser, self).__init__(*args, **kwargs)
        session_path = self.environment.parsed_options.session_dir
        with open(os.path.join(session_path, PARAMS_JSON_FILENAME)) as f:
            self.params = RedisVectorSearchUserParams.parse_raw(f.read())

        self.client = RedisVectorSearch(host=self.params.host,
                                        port=self.params.port,
                                        password=self.params.password,
                                        index_name=self.params.index_name)
        self.req = self.params.query_json

    def on_stop(self):
        self.client.close()

    @task
    def sm(self):
        self.client.vector_search(message=random.choice(self.req))
