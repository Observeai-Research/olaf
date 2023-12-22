import json
import os
from typing import Optional, Literal, List, Dict, Union
from collections import namedtuple
from datetime import datetime
from pathlib import Path

import cryptocode
from pydantic import BaseModel, HttpUrl, Json, validator, SecretStr, conint, confloat, Field

from src.constants import SESSION_CREATION_PATH
from src.streamlit_app.datamodel import service_settings


def validate_empty_query_json(query_json):
    if len(query_json) == 0:
        return [{}]
    return query_json


def validate_message_attribute_json(message_attribute_json: Json):
    if len(message_attribute_json) == 0:
        message_attribute_json = "{}"
    return json.loads(message_attribute_json)


def validate_empty_string(some_string: str):
    some_string = some_string.strip()
    assert some_string != ""
    return some_string


def json_serialize_params(parsed_json):
    if not isinstance(parsed_json, str):
        parsed_json = json.dumps(parsed_json)
    return parsed_json


class SessionDirectory(BaseModel):
    session_dir: Path

    @validator("session_dir", pre=True, allow_reuse=True)
    def create_dir(cls, p):
        p = p or SESSION_CREATION_PATH / str(datetime.now())
        os.makedirs(p, exist_ok=True)
        return p


class UserBaseParams(BaseModel):
    cur_session_dir: Path = None

    @validator('*', pre=True, allow_reuse=True)
    def decrypt_config(cls, v):
        if isinstance(v, str) and v.startswith("enc("):
            v = v[4:-1]
            v = cryptocode.decrypt(v, service_settings.ENCRYPTION_KEY)
        return v

    class Config:
        json_encoders = {
            SecretStr: lambda v: f"enc({cryptocode.encrypt(v.get_secret_value(), service_settings.ENCRYPTION_KEY)})"
        }
        extra = "forbid"


ElasticsearchNt = namedtuple("ElasticsearchNt", "url access_key secret_key index_name query_json")


class ElasticsearchUserParams(UserBaseParams):
    kind: Literal["elasticsearch"] = "elasticsearch"
    url: HttpUrl
    access_key: SecretStr
    secret_key: SecretStr
    index_name: str
    query_json: Json[List]

    validate_json = validator(*["query_json"], allow_reuse=True, pre=True)(json_serialize_params)
    _validate_string = validator(*["index_name"], allow_reuse=True)(validate_empty_string)


MongoDbNt = namedtuple("MongoDbNt", "mongo_url, db_name, collection_name, query_json")


class MongoDBUserParams(UserBaseParams):
    kind: Literal["mongo_db"] = "mongo_db"
    mongo_url: SecretStr
    db_name: str
    collection_name: str
    query_json: Json[List]

    validate_json = validator(*["query_json"], allow_reuse=True, pre=True)(json_serialize_params)
    _validate_query_json = validator("query_json", allow_reuse=True)(validate_empty_query_json)
    _validate_string = validator(*["mongo_url", "db_name", "collection_name"], allow_reuse=True)(validate_empty_string)


RestGetNt = namedtuple("RestGetNt", "url header_json")


class RestGetUserParams(UserBaseParams):
    kind: Literal["rest_get"] = "rest_get"
    url: HttpUrl
    header_json: Json[Dict]

    _validate_json = validator(*["header_json"], allow_reuse=True, pre=True)(json_serialize_params)


RestPostNt = namedtuple("RestPostNt", "url header_json query_json")


class RestPostUserParams(UserBaseParams):
    kind: Literal["rest_post"] = "rest_post"
    url: HttpUrl
    header_json: Json[Dict]
    query_json: Json[List]

    _validate_json = validator(*["query_json", "header_json"], allow_reuse=True, pre=True)(json_serialize_params)
    _validate_query_json = validator("query_json", allow_reuse=True)(validate_empty_query_json)


SagemakerNt = namedtuple("SagemakerNt", "endpoint, predictor_type, input_serializer, output_deserializer, aws_region, "
                                        "access_key, secret_key, session_token, multi_model, batch_mode, batch_value, query_json")


class SagemakerUserParams(UserBaseParams):
    kind: Literal["sagemaker"] = "sagemaker"
    endpoint: str
    access_key: SecretStr
    secret_key: SecretStr
    session_token: Optional[SecretStr] = ""
    aws_region: str  # todo enum

    predictor_type: str  # todo enum
    query_json: Json[List]
    multi_model: bool
    batch_mode: bool
    batch_value: conint(ge=2, le=100) = None
    input_serializer: str
    output_deserializer: str

    _validate_json = validator(*["query_json"], allow_reuse=True, pre=True)(json_serialize_params)
    _validate_query_json = validator("query_json", allow_reuse=True)(validate_empty_query_json)
    _validate_string = validator(*["access_key", "secret_key", "aws_region",
                                   "endpoint", "predictor_type"
                                   ], pre=True, allow_reuse=True)(validate_empty_string)


class SingleLoadConfig(BaseModel):
    duration: conint(strict=True, ge=1, le=10000)
    users: conint(ge=1, le=500)
    spawn_rate: confloat(ge=0.1, le=500)
    rps: confloat(ge=0.1, le=500)


class OlafScheduleParams(BaseModel):
    schedule: List[SingleLoadConfig]

    @validator('schedule', pre=True, allow_reuse=True)
    def name_must_be_json(cls, v):
        if isinstance(v, str):
            v = json.loads(v)
        return v

    class Config:
        extra = "ignore"


SqsNt = namedtuple("SqsNt", "sqs_name, aws_region, access_key, secret_key, session_token,"
                            "query_json, message_attribute_json, custom_load_shape_params")


class SQSUserParams(UserBaseParams):
    kind: Literal["sqs"] = "sqs"
    access_key: SecretStr
    secret_key: SecretStr
    aws_region: str  # todo enum
    session_token: Optional[SecretStr] = ""
    sqs_name: str
    query_json: Json[List]
    message_attribute_json: Dict
    custom_load_shape_params: Union[None, OlafScheduleParams]

    _validate_json = validator(*["query_json", "message_attribute_json"], allow_reuse=True, pre=True) \
        (json_serialize_params)
    _validate_query_json = validator("query_json", allow_reuse=True) \
        (validate_empty_query_json)
    _validate_message_attribute_json = validator("message_attribute_json", allow_reuse=True, pre=True) \
        (validate_message_attribute_json)
    _validate_string = validator(*["access_key", "secret_key", "aws_region", "sqs_name",
                                   ], pre=True, allow_reuse=True)(validate_empty_string)


SnsNt = namedtuple("SnsNt", "sns_arn, aws_region, access_key, secret_key, session_token,"
                            "query_json, message_attribute_json, custom_load_shape_params")


class SNSUserParams(UserBaseParams):
    kind: Literal["sns"] = "sns"
    access_key: SecretStr
    secret_key: SecretStr
    session_token: Optional[SecretStr] = ""
    aws_region: str  # todo enum
    sns_arn: str
    query_json: Json[List]
    message_attribute_json: Dict
    custom_load_shape_params: Union[None, OlafScheduleParams]

    _validate_json = validator(*["query_json", "message_attribute_json"], allow_reuse=True, pre=True)(
        json_serialize_params)
    _validate_query_json = validator("query_json", allow_reuse=True)(validate_empty_query_json)
    _validate_message_attribute_json = validator("message_attribute_json", allow_reuse=True, pre=True) \
        (validate_message_attribute_json)
    _validate_string = validator(*["access_key", "secret_key", "aws_region", "sns_arn",
                                   ], pre=True, allow_reuse=True)(validate_empty_string)


LambdaNt = namedtuple("LambdaNt", "lambda_arn, aws_region, access_key, secret_key, session_token, "
                                  "query_json")


class LambdaUserParams(UserBaseParams):
    kind: Literal["lambda"] = "lambda"
    access_key: SecretStr
    secret_key: SecretStr
    session_token: Optional[SecretStr] = ""
    aws_region: str  # todo enum
    lambda_arn: str
    query_json: Json[List]

    _validate_json = validator(*["query_json"], allow_reuse=True, pre=True) \
        (json_serialize_params)
    _validate_query_json = validator("query_json", allow_reuse=True) \
        (validate_empty_query_json)
    _validate_string = validator(*["access_key", "secret_key", "aws_region", "lambda_arn",
                                   ], pre=True, allow_reuse=True)(validate_empty_string)


S3Nt = namedtuple("S3Nt", "s3_bucket_name, aws_region, access_key, secret_key, session_token, "
                          "query_json")


class S3UserParams(UserBaseParams):
    pass


KafkaProducerNt = namedtuple("KafkaProducerNt", "bootstrap_server, ssl_username, ssl_password, topic_name, "
                                                "kafka_config, kafka_producer_config, query_json")


class KafkaProducerUserParams(UserBaseParams):
    kind: Literal["kafka_producer"] = "kafka_producer"
    bootstrap_server: str
    ssl_username: SecretStr
    ssl_password: SecretStr
    topic_name: str
    kafka_config: Json[Dict]
    kafka_producer_config: Json[Dict]
    query_json: Json[List]

    _validate_json = validator(*["query_json", "kafka_config", "kafka_producer_config"], allow_reuse=True, pre=True) \
        (json_serialize_params)
    _validate_query_json = validator("query_json", allow_reuse=True) \
        (validate_empty_query_json)
    _validate_string = validator(*["bootstrap_server", "ssl_username", "ssl_password", "topic_name",
                                   ], pre=True, allow_reuse=True)(validate_empty_string)


RedisStreamNt = namedtuple("RedisStreamNt", "redis_type, host, port, username, password, stream_name, "
                                            "query_json")


class RedisStreamUserParams(UserBaseParams):
    kind: Literal["redis_stream"] = "redis_stream"
    redis_type: Literal['strict', 'sentinel', 'cluster']
    host: str
    port: int
    username: SecretStr = ""
    password: SecretStr = ""
    stream_name: str
    query_json: Json[List]

    _validate_json = validator(*["query_json",], allow_reuse=True, pre=True) \
        (json_serialize_params)
    _validate_query_json = validator("query_json", allow_reuse=True) \
        (validate_empty_query_json)
    _validate_string = validator(*["host",  "stream_name",
                                   ], pre=True, allow_reuse=True)(validate_empty_string)

PineConeVectorSearchNt = namedtuple("PineConeVectorSearchNt", "api_key, environment_name, index_name, query_json")

class PineConeVectorSearchUserParams(UserBaseParams):
    kind: Literal['pinecone_vector_search'] = 'pinecone_vector_search'
    api_key: str
    environment_name: str
    index_name: str
    query_json: Json[List]

    _validate_json = validator(*["query_json", ], allow_reuse=True, pre=True) \
        (json_serialize_params)
    _validate_string = validator(*["environment_name", "index_name"], allow_reuse=True, pre=True) \
        (validate_empty_string)

class CocktailUserParams(UserBaseParams):
    kind: Literal["cocktail"] = "cocktail"
    user_resources: List[Union[
        ElasticsearchUserParams, MongoDBUserParams, RestGetUserParams, RestPostUserParams,
        SagemakerUserParams, SQSUserParams, SNSUserParams, LambdaUserParams
    ]]

RedisVectorSearchNt = namedtuple("RedisVectorSearchNt", "host, port, password, index_name, query_json")


class RedisVectorSearchUserParams(UserBaseParams):
    kind: Literal["redis_vector_search"] = "redis_vector_search"
    host: str
    port: int
    password: str
    index_name: str
    query_json: Json[List]

    _validate_json = validator(*["query_json", ], allow_reuse=True, pre=True) \
        (json_serialize_params)
    _validate_query_json = validator("query_json", allow_reuse=True) \
        (validate_empty_query_json)
    _validate_string = validator(*["host", "index_name"], allow_reuse=True, pre=True) \
        (validate_empty_string)