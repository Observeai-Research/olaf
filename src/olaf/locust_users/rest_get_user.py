import os

from locust import HttpUser, task, events, constant

from src.constants import PARAMS_JSON_FILENAME
from src.olaf.custom_event_handler import add_session_dir_arg, on_test_quit
from src.olaf.datamodel import RestGetUserParams

events.init_command_line_parser.add_listener(add_session_dir_arg)
events.quitting.add_listener(on_test_quit)


class RestGetUser(HttpUser):
    wait_time = constant(0)

    def __init__(self, *args, **kwargs):
        super(RestGetUser, self).__init__(*args, **kwargs)

        session_path = self.environment.parsed_options.session_dir
        with open(os.path.join(session_path, PARAMS_JSON_FILENAME)) as f:
            self.params = RestGetUserParams.parse_raw(f.read())

    @task
    def get_task(self):
        self.client.get("", headers=self.params.header_json)
