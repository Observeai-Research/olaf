import os
import random
import time
from typing import Dict
import json
import numpy as np
from ast import literal_eval

import pinecone

from locust import User, events, task, constant
from src.constants import PARAMS_JSON_FILENAME
from src.olaf.custom_event_handler import add_session_dir_arg, on_test_quit
from src.olaf.datamodel import PineConeVectorSearchUserParams

events.init_command_line_parser.add_listener(add_session_dir_arg)
events.quitting.add_listener(on_test_quit)

NAME = 'pinecone_vector_search'
REQUEST_TYPE = 'pinecone_vector_search'

class PineConeVectorSearch:

    def __init__(self, api_key: str, environment_name: str, index_name: str):
        pinecone.init(
            api_key=api_key,
            environment=environment_name
        )
        self.index = pinecone.Index(index_name)

    def close(self):
        pass

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
            top_k = message['top_k']
            include_metadata = message['include_metadata']
            query_vectors = message.get('query_vectors', None)
            namespace = message.get('namespace', None)
            if query_vectors is not None:
                # Execute the query
                self.index.query(queries=query_vectors, top_k=top_k,
                                 include_metadata=include_metadata, namespace=namespace)
            else:
                dense = message.get('vector', None)
                sparse = message.get('sparse_vector', None)
                self.index.query(top_k=top_k, include_metadata=include_metadata,
                                 vector=dense, sparse_vector=sparse, namespace=namespace)
        except Exception as err:
            request_meta["exception"] = err

        request_meta["response_time"] = (time.perf_counter() - start_time) * 1000
        events.request.fire(**request_meta)
        return request_meta["response"]

class PineConeVectorSearchUser(User):
    wait_time = constant(0)

    def __init__(self, *args, **kwargs):
        super(PineConeVectorSearchUser, self).__init__(*args, **kwargs)
        session_path = self.environment.parsed_options.session_dir
        with open(os.path.join(session_path, PARAMS_JSON_FILENAME)) as f:
            self.params = PineConeVectorSearchUserParams.parse_raw(f.read())
        self.client = PineConeVectorSearch(api_key=self.params.api_key,
                                           environment_name=self.params.environment_name,
                                           index_name=self.params.index_name)
        self.req = self.params.query_json

    def on_stop(self):
        pass

    @task
    def sm(self):
        self.client.vector_search(message=random.choice(self.req))
