import typing
from io import StringIO

import streamlit as st

from src.constants import (DEFAULT_QUERY_JSON, DEFAULT_MESSAGE_ATTRIBUTES, DEFAULT_OLAF_SCHEDULE,
                           DEFAULT_KAFKA_CONFIG, DEFAULT_KAFKA_PRODUCER_CONFIG, AWS_REGIONS,
                           SAGEMAKER_SERIALIZERS, SAGEMAKER_DESERIALIZERS, SAGEMAKER_PREDICTORS, )
from src.olaf.datamodel import (RestGetNt, MongoDbNt, RestPostNt, ElasticsearchNt,
                                SagemakerNt, S3Nt, LambdaNt, SqsNt, SnsNt, KafkaProducerNt, RedisStreamNt,
                                PineConeVectorSearchNt, RedisVectorSearchNt)


def show_core_services(test_type, is_cocktail=False, key=0) -> typing.Union[RestGetNt, RestPostNt, ElasticsearchNt,
                                                                            MongoDbNt, SagemakerNt, SqsNt, SnsNt,
                                                                            LambdaNt, S3Nt, KafkaProducerNt,
                                                                            RedisStreamNt, PineConeVectorSearchNt,
                                                                            RedisVectorSearchNt]:
    if test_type == "REST GET":
        url = st.text_input("URL", key=key)
        header_json = st.text_area("header JSON", key=key, value="{ }")
        return_args = RestGetNt(url, header_json)

    elif test_type == "REST POST":
        url = st.text_input(f"URL", key=key)
        header_json = st.text_area(f"header JSON", key=key, value="{ }")
        query_json = get_query_json_text_input(key=key)
        return_args = RestPostNt(url, header_json, query_json)

    elif test_type == "Elasticsearch":
        url = st.text_input("ES URL", key=key)
        a, b = st.columns(2)
        with a:
            access_key = st.text_input("ES username", key=key)
        with b:
            secret_key = st.text_input("ES password", type="password", key=key)
        index_name = st.text_input("ES index name", key=key)
        query_json = get_query_json_text_input(key=key)
        return_args = ElasticsearchNt(url, access_key, secret_key, index_name, query_json)

    elif test_type == "MongoDB":
        url = st.text_input("Mongo URL in SRV format", key=key)
        a, b = st.columns(2)
        with a:
            db_name = st.text_input("Database", key=key)
        with b:
            collection_name = st.text_input("Collection", key=key)
        query_json = get_query_json_text_input(key=key)
        return_args = MongoDbNt(url, db_name, collection_name, query_json)

    elif test_type == "Sagemaker":
        endpoint = st.text_input("Sagemaker endpoint", key=key)
        a, b, c = st.columns(3)

        with a:
            predictor_type = st.selectbox("Predictor type",
                                          options=SAGEMAKER_PREDICTORS,
                                          key=key,
                                          )
        with b:
            input_serializer = st.selectbox("Input Serializer",
                                            options=SAGEMAKER_SERIALIZERS,
                                            key=key,
                                            )
        with c:
            output_deserializer = st.selectbox("Output Deserializer",
                                               options=SAGEMAKER_DESERIALIZERS,
                                               key=key,
                                               )

        aws_region, access_key, secret_key, session_token = get_aws_info(key=key, )

        multi_model = st.checkbox("multi-model inference",
                                  key=key,
                                  disabled=False,
                                  help="If checked, multi-model inference will be enabled and predictor class would "
                                       "expect an additional field 'target_model' along with the payload. Refer to "
                                       "README.md for input schema")

        batch_mode = st.checkbox("enable batch mode",
                                 key=key,
                                 disabled=multi_model,
                                 help="k random sampled values with replacement will be sent in a list. Not supported "
                                      "for multi-model inference, instead provide the batch as a request payload")
        batch_value = None

        if batch_mode:
            batch_value = st.number_input("batch value", key=key,
                                          min_value=2, max_value=100, step=1)

        query_json = get_query_json_text_input(key=key)
        return_args = SagemakerNt(
            endpoint, predictor_type, input_serializer, output_deserializer,
            aws_region, access_key, secret_key, session_token,
            multi_model, batch_mode, batch_value, query_json)

    elif test_type == "SQS":
        sqs_name = st.text_input("SQS Name", key=key, )
        aws_region, access_key, secret_key, session_token = get_aws_info(key=key, )
        query_json = get_query_json_text_input(key=key, )
        message_attribute_json = get_message_attribute_input(key=key, )
        custom_load_shape_params = get_custom_load_shape_params(is_cocktail=is_cocktail, key=key, )
        return_args = SqsNt(sqs_name, aws_region, access_key, secret_key, session_token,
                            query_json, message_attribute_json, custom_load_shape_params)

    elif test_type == "SNS":
        sns_arn = st.text_input("SNS ARN")
        aws_region, access_key, secret_key, session_token = get_aws_info(key=key, )
        query_json = get_query_json_text_input(key=key, )
        message_attribute_json = get_message_attribute_input(key=key, )
        custom_load_shape_params = get_custom_load_shape_params(is_cocktail=is_cocktail, key=key, )
        return_args = SnsNt(sns_arn, aws_region, access_key, secret_key, session_token,
                            query_json, message_attribute_json, custom_load_shape_params)

    elif test_type == "Lambda":
        lambda_arn = st.text_input("Lambda ARN")
        aws_region, access_key, secret_key, session_token = get_aws_info(key=key, )
        query_json = get_query_json_text_input(key=key, )
        return_args = LambdaNt(lambda_arn, aws_region, access_key, secret_key, session_token, query_json, )

    elif test_type == "S3":
        st.error("page under development!")
        s3_bucket_name = st.text_input("S3 bucket", key=key)
        aws_region, access_key, secret_key, session_token = get_aws_info(key=key, )
        query_json = get_query_json_text_input(key=key, )
        return_args = S3Nt(s3_bucket_name, aws_region, access_key, secret_key, session_token, query_json, )

    elif test_type == "Redis Stream Producer":
        st.info("experimental feature")

        a, b, c = st.columns(3)
        with a:
            host = st.text_input("Host", key=key)
        with b:
            port = st.number_input("Port", 1, max_value=65_555, value=6379)
        with c:
            redis_type = st.selectbox("Redis Type", options=["strict", "sentinel", "cluster"])

        a, b = st.columns(2)
        with a:
            username = st.text_input("Username", key=key)
        with b:

            password = st.text_input("Password", type="password", key=key)

        stream_name = st.text_input("Stream Name", key=key)
        query_json = get_query_json_text_input(key=key)
        return_args = RedisStreamNt(redis_type, host, port, username, password, stream_name,
                                    query_json)

    elif test_type == "Kafka Producer":
        st.info("experimental feature")
        bootstrap_server = st.text_input("Boot Strap Servers", key=key)
        a, b = st.columns(2)
        with a:
            ssl_username = st.text_input("SSL Username", key=key)
            kafka_config_json = st.text_area(f"Kafka Config JSON", value=DEFAULT_KAFKA_CONFIG, key=key)
        with b:
            ssl_password = st.text_input("SSL Password", type="password", key=key)
            kafka_producer_config_json = st.text_area(f"Kafka Producer Config JSON",
                                                      value=DEFAULT_KAFKA_PRODUCER_CONFIG, key=key)
        topic_name = st.text_input("Topic Name", key=key)
        query_json = get_query_json_text_input(key=key)
        return_args = KafkaProducerNt(bootstrap_server, ssl_username, ssl_password, topic_name,
                                      kafka_config_json, kafka_producer_config_json, query_json)


    elif test_type == "PineCone Vector Search":
        st.info("experimental feature")
        a, b, c = st.columns(3)
        with a:
            api_key = st.text_input("API KEY", type="password", key=key)
        with b:
            environment_name = st.text_input("Environment Name", key=key)
        with c:
            index_name = st.text_input("Index Name", key=key)
        query_json = get_query_json_text_input(key=key)
        return_args = PineConeVectorSearchNt(api_key, environment_name, index_name, query_json)

    elif test_type == "Redis Vector Search":
        st.info("experimental feature")

        a, b, c, d = st.columns(4)
        with a:
            host = st.text_input("Host", key=key)
        with b:
            port = st.number_input("Port", 1, max_value=65_555, value=6379)
        with c:
            password = st.text_input("Password", type="password", key=key)
        with d:
            index_name = st.text_input("Index Name", key=key)

        query_json = get_query_json_text_input(key=key)
        return_args = RedisVectorSearchNt(host, port, password, index_name, query_json)

    else:
        raise AssertionError("Invalid resource type")

    return return_args


def get_query_json_text_input(key=0):
    a, b = st.columns([1, 5])

    with a:
        radio = st.radio(f"input query json", options=["type", "upload"], key=key)
    if radio == "type":
        with b:
            query_json = st.text_area(f"List of query JSON", value=DEFAULT_QUERY_JSON, key=key,
                                      help="Every element of list should be one query JSON")
    elif radio == "upload":
        with b:
            query_json = st.file_uploader(f"List of query JSON", key=key,
                                          help="Every element of list should be one query JSON")
        if query_json is not None:
            query_json = StringIO(query_json.read().decode("utf-8")).read()
    else:
        raise NotImplementedError
    return query_json


def get_message_attribute_input(name="message Attribute JSON", key=0, ):
    message_attribute_json = st.text_area(name, value=DEFAULT_MESSAGE_ATTRIBUTES, key=key,
                                          help="Dictionary like JSON for message attributes")

    return message_attribute_json


def get_aws_info(key=0):
    a, b, c = st.columns(3)

    with a:
        aws_region = st.selectbox("AWS region",
                                  options=AWS_REGIONS,
                                  key=key,
                                  )
    with b:
        access_key = st.text_input("AWS access key", key=key, )
    with c:
        secret_key = st.text_input("AWS secret key", type="password", key=key, )

    session_token = st.text_input("AWS session token", type="password", key=key, )

    return aws_region, access_key, secret_key, session_token


def get_advanced_usage_params() -> typing.Union[None, typing.Dict]:
    advanced_params = None

    advanced_usage = st.checkbox("automate run")

    if advanced_usage:
        with st.expander("", expanded=True):
            a, b = st.columns(2)

            with a:
                load_duration = st.number_input("test duration in seconds", min_value=20, max_value=10000, step=100,
                                                help="time after which to stop test")
                autostart = st.checkbox("autostart", help="load test will auto-start with set params", value=True)

            with b:
                autoquit_timeout = st.number_input("autoquit timeout after completion", min_value=1, max_value=600,
                                                   value=10, step=5,
                                                   help="seconds to wait after completion before closing session!")

            a, b = st.columns(2)
            with a:
                users = st.number_input("users to spawn", min_value=1, max_value=500, value=10, step=5,
                                        help="peak concurrency")
            with b:
                spawn_rate = st.number_input("spawn rate", min_value=0.1, max_value=500.0, value=1.0, step=0.1,
                                             help="ramp up period")

            advanced_params = {
                "autoquit_timeout": autoquit_timeout,
                "autostart": autostart,
                "users": users,
                "spawn_rate": spawn_rate,
                "load_duration": load_duration,
            }

    return advanced_params


def get_olaf_schedule_input(name="Olaf Schedule for Custom Load Shape", key=0):
    schedule_json = st.text_area(name, value=DEFAULT_OLAF_SCHEDULE, key=key,
                                 help="Every element of list should be one query JSON")
    return schedule_json


def get_custom_load_shape_params(is_cocktail=False, key=0) -> typing.Union[None, typing.Dict]:
    custom_load_shape_params = None
    if is_cocktail:
        return custom_load_shape_params
    custom_load_shape = st.checkbox("Olaf Schedule (beta)", key=key, )
    if custom_load_shape:
        with st.expander("", expanded=True):
            schedule_input = get_olaf_schedule_input(key=key)
            custom_load_shape_params = {
                "schedule": schedule_input
            }
    return custom_load_shape_params
