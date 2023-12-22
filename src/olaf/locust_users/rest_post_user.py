import os
import random

from locust import HttpUser, task, events, constant

from src.constants import PARAMS_JSON_FILENAME
from src.olaf.custom_event_handler import add_session_dir_arg, on_test_quit
from src.olaf.datamodel import RestPostUserParams

events.init_command_line_parser.add_listener(add_session_dir_arg)
events.quitting.add_listener(on_test_quit)


class RestPostUser(HttpUser):
    wait_time = constant(0)

    def __init__(self, *args, **kwargs):
        super(RestPostUser, self).__init__(*args, **kwargs)

        session_path = self.environment.parsed_options.session_dir
        with open(os.path.join(session_path, PARAMS_JSON_FILENAME)) as f:
            self.params = RestPostUserParams.parse_raw(f.read())

        self.req = self.params.query_json

    @task
    def post_task(self):
        self.client.post("",
                         headers=self.params.header_json,
                         json=random.choice(self.req),
                         )
