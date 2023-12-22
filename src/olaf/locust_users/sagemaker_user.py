import os
import random
import time

import botocore.config
import sagemaker
from locust import User, events, task, constant
from sagemaker.deserializers import JSONDeserializer, NumpyDeserializer
from sagemaker.pytorch import PyTorchPredictor
from sagemaker.serializers import NumpySerializer, JSONSerializer
from sagemaker.sklearn.model import SKLearnPredictor
from sagemaker.tensorflow import TensorFlowPredictor

from boto3 import Session
from src.constants import PARAMS_JSON_FILENAME
from src.olaf.custom_event_handler import add_session_dir_arg, on_test_quit
from src.olaf.datamodel import SagemakerUserParams

events.init_command_line_parser.add_listener(add_session_dir_arg)
events.quitting.add_listener(on_test_quit)


class SagemakerTensorFlowClient(TensorFlowPredictor):
    NAME = "tensorflow_predictor"
    REQUEST_TYPE = "tensorflow_predict"

    def predictEx(self, data, mme=False):
        start_time = time.perf_counter()
        request_meta = {
            "request_type": self.REQUEST_TYPE,
            "name": self.NAME,
            "response_length": 0,
            "response": None,
            "context": {},
            "exception": None,
        }
        try:
            if mme:
                raise NotImplementedError(f"{self.NAME} currently does not support multi-model inference")
            request_meta["response"] = self.predict(data)
        except Exception as err:
            request_meta["exception"] = err

        request_meta["response_time"] = (time.perf_counter() - start_time) * 1000
        events.request.fire(**request_meta)
        return request_meta["response"]


class SagemakerPyTorchClient(PyTorchPredictor):
    NAME = "pytorch_predictor"
    REQUEST_TYPE = "pytorch_predict"
    MME_REQ_DTYPE = dict
    MME_REQ_PARAMS = ["payload", "target_model"]

    def predictEx(self, data, mme=False):
        start_time = time.perf_counter()
        request_meta = {
            "request_type": self.REQUEST_TYPE,
            "name": self.NAME,
            "response_length": 0,
            "response": None,
            "context": {},
            "exception": None,
        }
        try:
            if mme:
                self.validate_mme_req(data)
                request_meta["response"] = self.predict(data["payload"], target_model=data["target_model"])
            else:
                request_meta["response"] = self.predict(data)
        except Exception as err:
            request_meta["exception"] = err

        request_meta["response_time"] = (time.perf_counter() - start_time) * 1000
        events.request.fire(**request_meta)
        return request_meta["response"]

    def validate_mme_req(self, data):
        if not isinstance(data, self.MME_REQ_DTYPE):
            raise TypeError(f"Multi-model inference expects the request of type '{self.MME_REQ_DTYPE}' "
                            f"received '{type(data)}'")
        for param in self.MME_REQ_PARAMS:
            if not param in data:
                raise KeyError(f"Param '{param}' not found in {data.keys()}")


class SagemakerSKLearnClient(SKLearnPredictor):
    NAME = "sklearn_predictor"
    REQUEST_TYPE = "sklearn_predict"
    MME_REQ_DTYPE = dict
    MME_REQ_PARAMS = ["payload", "target_model"]

    def predictEx(self, data, mme=False):
        start_time = time.perf_counter()
        request_meta = {
            "request_type": self.REQUEST_TYPE,
            "name": self.NAME,
            "response_length": 0,
            "response": None,
            "context": {},
            "exception": None,
        }
        try:
            if mme:
                self.validate_mme_req(data)
                request_meta["response"] = self.predict(data["payload"], target_model=data["target_model"])
            else:
                request_meta["response"] = self.predict(data)
        except Exception as err:
            request_meta["exception"] = err

        request_meta["response_time"] = (time.perf_counter() - start_time) * 1000
        events.request.fire(**request_meta)
        return request_meta["response"]

    def validate_mme_req(self, data):
        if not isinstance(data, self.MME_REQ_DTYPE):
            raise TypeError(f"Multi-model inference expects the request of type '{self.MME_REQ_DTYPE}' "
                            f"received '{type(data)}'")
        for param in self.MME_REQ_PARAMS:
            if not param in data:
                raise KeyError(f"Param '{param}' not found in {data.keys()}")


class SagemakerUser(User):
    wait_time = constant(0)
    predictor_class_mapping = {
        "pytorch predictor": SagemakerPyTorchClient,
        "sklearn predictor": SagemakerSKLearnClient,
        "tensorflow predictor": SagemakerTensorFlowClient,
    }

    def __init__(self, *args, **kwargs):
        super(SagemakerUser, self).__init__(*args, **kwargs)
        session_path = self.environment.parsed_options.session_dir
        with open(os.path.join(session_path, PARAMS_JSON_FILENAME)) as f:
            self.params = SagemakerUserParams.parse_raw(f.read())

        if self.params.input_serializer == "numpy":
            serializer = NumpySerializer()
        elif self.params.input_serializer == "json":
            serializer = JSONSerializer()
        else:
            raise NotImplementedError

        if self.params.output_deserializer == "numpy":
            deserializer = NumpyDeserializer()
        elif self.params.output_deserializer == "json":
            deserializer = JSONDeserializer()
        else:
            raise NotImplementedError

        boto_session = Session(aws_access_key_id=self.params.access_key.get_secret_value(),
                               aws_secret_access_key=self.params.secret_key.get_secret_value(),
                               aws_session_token=self.params.session_token.get_secret_value() if self.params.session_token.get_secret_value() else None,
                               region_name=self.params.aws_region,
                               )
        sm_runtime_client = boto_session.client("runtime.sagemaker",
                                                config=botocore.config.Config(read_timeout=60,
                                                                              max_pool_connections=100,
                                                                              retries={
                                                                                  'max_attempts': 4},
                                                                              ))
        sm_session = sagemaker.Session(boto_session=boto_session,
                                       sagemaker_runtime_client=sm_runtime_client
                                       )

        self.client = self.predictor_class_mapping[self.params.predictor_type](
            sagemaker_session=sm_session,
            endpoint_name=self.params.endpoint,
            serializer=serializer,
            deserializer=deserializer,
        )
        self.req = self.params.query_json

    @task
    def sm(self):
        if self.params.batch_mode:
            self.client.predictEx(random.choices(self.req, k=self.params.batch_value), mme=self.params.multi_model)
        else:
            self.client.predictEx(random.choice(self.req), mme=self.params.multi_model)
