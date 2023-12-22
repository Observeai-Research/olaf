import os
import random
import time

from elasticsearch import Elasticsearch
from locust import User, events, task, constant

from src.constants import PARAMS_JSON_FILENAME
from src.olaf.custom_event_handler import add_session_dir_arg, on_test_quit
from src.olaf.datamodel import ElasticsearchUserParams

events.init_command_line_parser.add_listener(add_session_dir_arg)
events.quitting.add_listener(on_test_quit)

NAME = "elasticsearch_search"
REQUEST_TYPE = "elasticsearch_query"


class ElasticsearchClient(Elasticsearch):

    def query(self, index, body):
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
            request_meta["response"] = self.search(index=index,
                                                   body=body,
                                                   request_cache=False
                                                   )
        except Exception as err:
            request_meta["exception"] = err

        request_meta["response_time"] = (time.perf_counter() - start_time) * 1000
        events.request.fire(**request_meta)
        return request_meta["response"]


class ElasticsearchUser(User):
    wait_time = constant(0)

    def __init__(self, *args, **kwargs):
        super(ElasticsearchUser, self).__init__(*args, **kwargs)
        session_path = self.environment.parsed_options.session_dir
        with open(os.path.join(session_path, PARAMS_JSON_FILENAME)) as f:
            self.params = ElasticsearchUserParams.parse_raw(f.read())

        self.client = ElasticsearchClient(self.params.url, http_auth=(self.params.access_key.get_secret_value(),
                                                                      self.params.secret_key.get_secret_value()
                                                                      ))
        self.req = self.params.query_json

    @task
    def sm(self):
        self.client.query(index=self.params.index_name, body=random.choice(self.req))
