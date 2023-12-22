import os
import random
import time

from locust import User, events, task, constant
from pymongo import MongoClient

from src.constants import PARAMS_JSON_FILENAME
from src.olaf.custom_event_handler import add_session_dir_arg, on_test_quit
from src.olaf.datamodel import MongoDBUserParams

events.init_command_line_parser.add_listener(add_session_dir_arg)
events.quitting.add_listener(on_test_quit)

NAME = "mongodb_find_one"
REQUEST_TYPE = "mongo_find_one_query"


class MongoReadClient(MongoClient):

    def query(self, db_name, collection_name, body):

        db = self.get_database(db_name)
        collection = db.get_collection(collection_name)

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
            request_meta["response"] = collection.find_one(body)
        except Exception as err:
            request_meta["exception"] = err

        request_meta["response_time"] = (time.perf_counter() - start_time) * 1000
        events.request.fire(**request_meta)
        return request_meta["response"]


class MongoReadUser(User):
    wait_time = constant(0)

    def __init__(self, *args, **kwargs):
        super(MongoReadUser, self).__init__(*args, **kwargs)

        session_path = self.environment.parsed_options.session_dir
        with open(os.path.join(session_path, PARAMS_JSON_FILENAME)) as f:
            self.params = MongoDBUserParams.parse_raw(f.read())

        self.client = MongoReadClient(host=self.params.mongo_url.get_secret_value())
        self.req = self.params.query_json

    @task
    def sm(self):
        self.client.query(db_name=self.params.db_name,
                          collection_name=self.params.collection_name,
                          body=random.choice(self.req))
