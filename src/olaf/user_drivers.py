import os
import typing
from datetime import datetime
from subprocess import Popen
from urllib.parse import quote_plus

import randomname
from jinja2 import Template

from src.constants import ROOT_PATH, PARAMS_JSON_FILENAME, SESSION_CREATION_PATH, USER_TEMPLATE_PATH, USER_CONCRETE_PATH
from src.olaf.datamodel import (ElasticsearchUserParams, MongoDBUserParams, RestGetUserParams, LambdaUserParams,
                                RestPostUserParams, CocktailUserParams, KafkaProducerUserParams,
                                SagemakerUserParams, SessionDirectory, SQSUserParams, SNSUserParams,
                                RedisStreamUserParams, RedisVectorSearchUserParams, PineConeVectorSearchUserParams)
from src.olaf.datamodel import (RestGetNt, MongoDbNt, RestPostNt, ElasticsearchNt,
                                SagemakerNt, LambdaNt, SqsNt, SnsNt, KafkaProducerNt, RedisStreamNt, RedisVectorSearchNt,
                                PineConeVectorSearchNt)
from src.streamlit_app.datamodel import OlafAdvancedParams, LocustConfig


def create_session_dir_name(fields) -> str:
    fields.append(datetime.now())
    fields = map(str, fields)
    fields = map(quote_plus, fields)
    return "__".join(fields)


def write_session_params(data, path):
    with open(path, "w") as f:
        f.write(data)


def render_custom_load_template(template_name, **template_kwargs):
    src_template_path = USER_TEMPLATE_PATH / f"{template_name}_template.py.j2"
    dst_template_path = USER_CONCRETE_PATH / f"{template_name}_custom.py"
    assert src_template_path.exists()
    with src_template_path.open("r") as f:
        python_file = f.read()
    tm = Template(python_file)
    python_file = tm.render(**template_kwargs)

    with dst_template_path.open("w") as f:
        f.write(python_file)

    return dst_template_path


def start_locust(args,
                 locust_config: LocustConfig,
                 has_custom_load_shape: bool = False,
                 mode="multi_proc",
                 num_slaves=os.cpu_count() - 1,
                 advanced_params: OlafAdvancedParams = None,
                 ):
    p_ids = []
    args = ["nohup", "locust"] + ["--loglevel", "WARNING"] + args
    if mode == "single_proc":
        p = Popen(args)
        p_ids.append(p.pid)
    elif mode == "multi_proc":
        assert num_slaves is not None

        worker_args = args + ["--worker"]
        for n in range(num_slaves):
            p = Popen(worker_args)
            p_ids.append(p.pid)

        master_args = args + ["--master"] \
                      + ["--web-port", str(locust_config.port)] \
                      + ["--stop-timeout", "1"]
        if advanced_params:
            master_args += ["--autostart"]
            if not has_custom_load_shape:
                master_args += ["--run-time", str(advanced_params.load_duration)]
                master_args += ["--autoquit", str(advanced_params.autoquit_timeout)]
                master_args += ["--users", str(advanced_params.users)]
                master_args += ["--spawn-rate", str(advanced_params.spawn_rate)]

        p = Popen(master_args)
        p_ids.append(p.pid)

    else:
        raise NotImplementedError
    return p_ids


def rest_get_driver(resource_args: RestGetNt,
                    locust_config: LocustConfig,
                    advanced_params: OlafAdvancedParams,
                    load_session_name: str,
                    ):
    params = RestGetUserParams(**resource_args._asdict())
    session_dir = create_session_dir_name([params.kind,
                                           load_session_name,
                                           params.url.host,
                                           params.url.path
                                           ])

    params.cur_session_dir = SessionDirectory(session_dir=SESSION_CREATION_PATH / session_dir).session_dir

    write_session_params(params.json(), os.path.join(params.cur_session_dir, PARAMS_JSON_FILENAME))

    args = [
        "-f",
        os.path.join(ROOT_PATH, "olaf/locust_users/rest_get_user.py"),
        "--host", params.url,
        "--session_dir", params.cur_session_dir,
    ]
    p_ids = start_locust(args,
                         locust_config=locust_config,
                         advanced_params=advanced_params)
    return p_ids


def rest_post_driver(resource_args: RestPostNt,
                     locust_config: LocustConfig,
                     advanced_params: OlafAdvancedParams,
                     load_session_name: str,
                     ):
    params = RestPostUserParams(**resource_args._asdict())

    session_dir = create_session_dir_name([params.kind,
                                           load_session_name,
                                           params.url.host,
                                           params.url.path
                                           ])

    params.cur_session_dir = SessionDirectory(session_dir=SESSION_CREATION_PATH / session_dir).session_dir

    write_session_params(params.json(), os.path.join(params.cur_session_dir, PARAMS_JSON_FILENAME))

    args = [
        "-f",
        os.path.join(ROOT_PATH, "olaf/locust_users/rest_post_user.py"),
        "--host", params.url,
        "--session_dir", params.cur_session_dir,
    ]
    p_ids = start_locust(args,
                         locust_config=locust_config,
                         advanced_params=advanced_params)
    return p_ids


def elasticsearch_read_driver(resource_args: ElasticsearchNt,
                              locust_config: LocustConfig,
                              advanced_params: OlafAdvancedParams,
                              load_session_name: str, ):
    params = ElasticsearchUserParams(**resource_args._asdict())

    session_dir = create_session_dir_name([params.kind,
                                           load_session_name,
                                           params.index_name,
                                           params.url.host,
                                           ])

    params.cur_session_dir = SessionDirectory(session_dir=SESSION_CREATION_PATH / session_dir).session_dir

    write_session_params(params.json(), os.path.join(params.cur_session_dir, PARAMS_JSON_FILENAME))

    args = [
        "-f",
        os.path.join(ROOT_PATH, "olaf/locust_users/elasticsearch_user.py"),
        "--host", f"elasticsearch_{params.index_name}",
        "--session_dir", params.cur_session_dir,
    ]
    p_ids = start_locust(args,
                         locust_config=locust_config,
                         advanced_params=advanced_params)
    return p_ids


def mongo_read_driver(resource_args: MongoDbNt,
                      locust_config: LocustConfig,
                      advanced_params: OlafAdvancedParams,

                      load_session_name: str, ):
    params = MongoDBUserParams(**resource_args._asdict())

    session_dir = create_session_dir_name([params.kind,
                                           load_session_name,
                                           params.db_name,
                                           params.collection_name
                                           ])

    params.cur_session_dir = SessionDirectory(session_dir=SESSION_CREATION_PATH / session_dir).session_dir

    write_session_params(params.json(), os.path.join(params.cur_session_dir, PARAMS_JSON_FILENAME))

    args = [
        "-f",
        os.path.join(ROOT_PATH, "olaf/locust_users/mongo_user.py"),
        "--host", f"mongodb_{params.db_name}_{params.collection_name}",
        "--session_dir", params.cur_session_dir,
    ]
    p_ids = start_locust(args,
                         locust_config=locust_config,
                         advanced_params=advanced_params)
    return p_ids


def sagemaker_inference_driver(resource_args: SagemakerNt,
                               locust_config: LocustConfig,
                               advanced_params: OlafAdvancedParams,
                               load_session_name: str, ):
    params = SagemakerUserParams(**resource_args._asdict())

    session_dir = create_session_dir_name([params.kind,
                                           load_session_name,
                                           params.endpoint,
                                           params.aws_region
                                           ])

    params.cur_session_dir = SessionDirectory(session_dir=SESSION_CREATION_PATH / session_dir).session_dir

    write_session_params(params.json(), os.path.join(params.cur_session_dir, PARAMS_JSON_FILENAME))

    args = [
        "-f",
        os.path.join(ROOT_PATH, "olaf/locust_users/sagemaker_user.py"),
        "--host", params.endpoint,
        "--session_dir", params.cur_session_dir,
    ]

    p_ids = start_locust(args,
                         locust_config=locust_config,
                         advanced_params=advanced_params)
    return p_ids


def aws_sqs_put_message_driver(resource_args: SqsNt,
                               locust_config: LocustConfig,
                               advanced_params: OlafAdvancedParams,
                               load_session_name: str, ):
    params = SQSUserParams(**resource_args._asdict())

    session_dir = create_session_dir_name([params.kind,
                                           load_session_name,
                                           params.sqs_name,
                                           params.aws_region
                                           ])

    params.cur_session_dir = SessionDirectory(session_dir=SESSION_CREATION_PATH / session_dir).session_dir

    write_session_params(params.json(), os.path.join(params.cur_session_dir, PARAMS_JSON_FILENAME))
    user_path = os.path.join(ROOT_PATH, "olaf/locust_users/sqs_user.py")
    custom_load_shape_params = params.custom_load_shape_params
    has_custom_load_shape = False

    if custom_load_shape_params:
        user_path = render_custom_load_template("sqs_user", **custom_load_shape_params.dict())
        has_custom_load_shape = True

    args = [
        "-f",
        user_path,
        "--host", params.sqs_name,
        "--session_dir", params.cur_session_dir,
    ]
    p_ids = start_locust(args,
                         has_custom_load_shape=has_custom_load_shape,
                         locust_config=locust_config,
                         advanced_params=advanced_params)
    return p_ids


def aws_sns_put_driver(resource_args: SnsNt,
                       locust_config: LocustConfig,
                       advanced_params: OlafAdvancedParams,
                       load_session_name: str, ):
    params = SNSUserParams(**resource_args._asdict())

    session_dir = create_session_dir_name([params.kind,
                                           load_session_name,
                                           params.sns_arn,
                                           params.aws_region
                                           ])

    params.cur_session_dir = SessionDirectory(session_dir=SESSION_CREATION_PATH / session_dir).session_dir

    write_session_params(params.json(), os.path.join(params.cur_session_dir, PARAMS_JSON_FILENAME))
    user_path = os.path.join(ROOT_PATH, "olaf/locust_users/sns_user.py")
    custom_load_shape_params = resource_args.custom_load_shape_params
    has_custom_load_shape = False

    if custom_load_shape_params:
        user_path = render_custom_load_template("sns_user", **custom_load_shape_params.dict())
        has_custom_load_shape = True

    args = [
        "-f",
        user_path,
        "--host", params.sns_arn,
        "--session_dir", params.cur_session_dir,
    ]
    p_ids = start_locust(args,
                         has_custom_load_shape=has_custom_load_shape,
                         locust_config=locust_config,
                         advanced_params=advanced_params)
    return p_ids


def aws_lambda_driver(resource_args: LambdaNt,
                      locust_config: LocustConfig,
                      advanced_params: OlafAdvancedParams,
                      load_session_name: str, ):
    params = LambdaUserParams(**resource_args._asdict())

    session_dir = create_session_dir_name([params.kind,
                                           load_session_name,
                                           params.lambda_arn,
                                           params.aws_region
                                           ])

    params.cur_session_dir = SessionDirectory(session_dir=SESSION_CREATION_PATH / session_dir).session_dir

    write_session_params(params.json(), os.path.join(params.cur_session_dir, PARAMS_JSON_FILENAME))
    user_path = os.path.join(ROOT_PATH, "olaf/locust_users/lambda_user.py")
    has_custom_load_shape = False

    args = [
        "-f",
        user_path,
        "--host", params.lambda_arn,
        "--session_dir", params.cur_session_dir,
    ]
    p_ids = start_locust(args,
                         has_custom_load_shape=has_custom_load_shape,
                         locust_config=locust_config,
                         advanced_params=advanced_params)
    return p_ids


def kafka_producer_driver(resource_args: KafkaProducerNt,
                          locust_config: LocustConfig,
                          advanced_params: OlafAdvancedParams,
                          load_session_name: str, ):
    params = KafkaProducerUserParams(**resource_args._asdict())

    session_dir = create_session_dir_name([params.kind,
                                           load_session_name,
                                           params.topic_name,
                                           ])

    params.cur_session_dir = SessionDirectory(session_dir=SESSION_CREATION_PATH / session_dir).session_dir

    write_session_params(params.json(), os.path.join(params.cur_session_dir, PARAMS_JSON_FILENAME))

    user_path = os.path.join(ROOT_PATH, "olaf/locust_users/kafka_producer_user.py")

    has_custom_load_shape = False

    args = [
        "-f",
        user_path,
        "--host", params.topic_name,
        "--session_dir", params.cur_session_dir,
    ]
    p_ids = start_locust(args,
                         has_custom_load_shape=has_custom_load_shape,
                         locust_config=locust_config,
                         advanced_params=advanced_params)
    return p_ids


def redis_stream_producer_driver(resource_args: RedisStreamNt,
                                 locust_config: LocustConfig,
                                 advanced_params: OlafAdvancedParams,
                                 load_session_name: str, ):
    params = RedisStreamUserParams(**resource_args._asdict())

    session_dir = create_session_dir_name([params.kind,
                                           load_session_name,
                                           params.stream_name,
                                           ])

    params.cur_session_dir = SessionDirectory(session_dir=SESSION_CREATION_PATH / session_dir).session_dir

    write_session_params(params.json(), os.path.join(params.cur_session_dir, PARAMS_JSON_FILENAME))

    user_path = os.path.join(ROOT_PATH, "olaf/locust_users/redis_stream_producer_user.py")

    has_custom_load_shape = False

    args = [
        "-f",
        user_path,
        "--host", params.stream_name,
        "--session_dir", params.cur_session_dir,
    ]
    p_ids = start_locust(args,
                         has_custom_load_shape=has_custom_load_shape,
                         locust_config=locust_config,
                         advanced_params=advanced_params)
    return p_ids

def pine_cone_vector_search_driver(resource_args: PineConeVectorSearchNt,
                                   locust_config: LocustConfig,
                                   advanced_params: OlafAdvancedParams,
                                   load_session_name: str,):
    params = PineConeVectorSearchUserParams(**resource_args._asdict())
    session_dir = create_session_dir_name([params.kind,
                                           load_session_name,
                                           params.index_name,
                                           ])
    params.cur_session_dir = SessionDirectory(session_dir=SESSION_CREATION_PATH / session_dir).session_dir
    write_session_params(params.json(), os.path.join(params.cur_session_dir, PARAMS_JSON_FILENAME))
    user_path = os.path.join(ROOT_PATH, "olaf/locust_users/pinecone_vector_search.py")
    has_custom_load_shape = False
    args = [
        "-f",
        user_path,
        "--host", params.index_name,
        "--session_dir", params.cur_session_dir,
    ]
    p_ids = start_locust(args,
                         has_custom_load_shape=has_custom_load_shape,
                         locust_config=locust_config,
                         advanced_params=advanced_params)
    return p_ids


def redis_vector_search_driver(resource_args: RedisVectorSearchNt,
                        locust_config: LocustConfig,
                        advanced_params: OlafAdvancedParams,
                        load_session_name: str,):
    params = RedisVectorSearchUserParams(**resource_args._asdict())
    session_dir = create_session_dir_name([params.kind,
                                           load_session_name,
                                           params.host,
                                           params.index_name
                                           ])
    params.cur_session_dir = SessionDirectory(session_dir=SESSION_CREATION_PATH / session_dir).session_dir

    write_session_params(params.json(), os.path.join(params.cur_session_dir, PARAMS_JSON_FILENAME))
    user_path = os.path.join(ROOT_PATH, "olaf/locust_users/redis_vector_search.py")

    has_custom_load_shape = False
    args = [
        "-f",
        user_path,
        "--host", params.host,
        "--session_dir", params.cur_session_dir,
    ]
    p_ids = start_locust(args,
                         has_custom_load_shape=has_custom_load_shape,
                         locust_config=locust_config,
                         advanced_params=advanced_params)
    return p_ids


def cocktail_driver(resource_args: typing.List,
                    locust_config: LocustConfig,
                    advanced_params: OlafAdvancedParams,
                    load_session_name: str, ):
    resource_args = list(map(lambda x: x._asdict(), filter(lambda x: x[0], resource_args)))
    params = CocktailUserParams(user_resources=resource_args)

    jinja_args = {}
    for ndx, p in enumerate(params.user_resources):
        l = jinja_args.get(p.kind, list())
        l.append(ndx)
        jinja_args[p.kind] = l

    session_dir = create_session_dir_name([params.kind,
                                           load_session_name,
                                           ])

    params.cur_session_dir = SessionDirectory(session_dir=SESSION_CREATION_PATH / session_dir).session_dir

    write_session_params(params.json(), os.path.join(params.cur_session_dir, PARAMS_JSON_FILENAME))
    user_path = render_custom_load_template("cocktail_user", **jinja_args)
    has_custom_load_shape = False

    args = [
        "-f",
        user_path,
        "--host", load_session_name or randomname.get_name(),
        "--session_dir", params.cur_session_dir,
    ]
    p_ids = start_locust(args,
                         has_custom_load_shape=has_custom_load_shape,
                         locust_config=locust_config,
                         advanced_params=advanced_params)
    return p_ids
