import os
from pathlib import Path

import boto3

from src.streamlit_app.datamodel import service_config


def upload_session_dir(session_dir_path: Path):
    if not service_config.aws_config.key.get_secret_value() or not service_config.aws_config.secret.get_secret_value():
        return
    s3_client = boto3.client('s3',
                             aws_access_key_id=service_config.aws_config.key.get_secret_value(),
                             aws_secret_access_key=service_config.aws_config.secret.get_secret_value(), )
    dir_name = session_dir_path.stem.replace("__", "/")
    prefix_path = service_config.s3_config.base_path
    s3_upload_path = os.path.join(prefix_path, dir_name)
    for fname in os.listdir(session_dir_path):
        s3_client.upload_file(Filename=os.path.join(session_dir_path, fname),
                              Bucket=service_config.s3_config.bucket_name,
                              Key=os.path.join(s3_upload_path, fname)
                              )
