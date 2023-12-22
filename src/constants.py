import os
from pathlib import Path


def create_path(p: Path):
    if not p.exists():
        os.makedirs(p)


ROOT_PATH = Path(__file__).absolute().parent
CONFIG_PATH = ROOT_PATH / 'config'
SESSION_CREATION_PATH = ROOT_PATH.parent / "olaf_sessions"
USER_TEMPLATE_PATH = ROOT_PATH / 'olaf' / 'locust_user_template'
USER_CONCRETE_PATH = ROOT_PATH / 'olaf' / 'locust_users'

MAX_COCKTAIL_ENDPOINTS = 5

assert ROOT_PATH.exists()
assert CONFIG_PATH.exists()
assert USER_TEMPLATE_PATH.exists()
assert USER_CONCRETE_PATH.exists()
create_path(SESSION_CREATION_PATH)

PARAMS_JSON_FILENAME = "params.json"

CORE_SERVICES = ["REST GET",
                 "REST POST",
                 "Elasticsearch",
                 "Lambda",
                 "MongoDB",
                 "Sagemaker",
                 "SQS",
                 "SNS",
                 ]

EXPERIMENTAL_SERVICES = ["Kafka Producer", "S3", "Cocktail", "Redis Stream Producer",
                         "PineCone Vector Search", "Redis Vector Search"]

HIDE_ST_STYLE = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""

DEFAULT_QUERY_JSON = """[
    {  }
]
"""

DEFAULT_MESSAGE_ATTRIBUTES = """{
        "attributeName": {
            "StringValue": "AttributeValue",
            "DataType": "String"
        }
    }
"""

DEFAULT_OLAF_SCHEDULE = """[
    {"duration": 300, "users": 3, "spawn_rate": 3, "rps": 1}
]
"""

AWS_REGIONS = ["us-east-1", "us-east-2", "us-west-1", "us-west-2",
               "af-south-1",
               "ap-east-1", "ap-south-1",
               "ap-southeast-1", "ap-southeast-2", "ap-southeast-3",
               "ap-northeast-1", "ap-northeast-2", "ap-northeast-3",
               "ca-central-1",
               "eu-west-1", "eu-west-2", "eu-west-3",
               "eu-central-1", "eu-south-1", "eu-north-1",
               "me-south-1",
               "sa-east-1",
               ]

SAGEMAKER_PREDICTORS = [
    "pytorch predictor",
    "sklearn predictor",
    "tensorflow predictor",
]
SAGEMAKER_SERIALIZERS = ["numpy",
                         "json",
                         ]
SAGEMAKER_DESERIALIZERS = ["numpy",
                           "json",
                           ]


DEFAULT_KAFKA_CONFIG = """{
    "sasl_mechanism": "PLAIN",
    "security_protocol": "SASL_SSL",
    "connections_max_idle_ms": 540000,
    "max_in_flight_requests_per_connection": 5
  }"""


DEFAULT_KAFKA_PRODUCER_CONFIG = """{
    "retries": 5,
    "batch_size": 16384,
    "linger_ms": 0,
    "request_timeout_ms": 30000,
    "acks": -1,
    "retry_backoff_ms": 100
  }"""



