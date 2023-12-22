import os
import typing
from functools import lru_cache

import cryptocode
import hiyapyco
from pydantic import BaseModel, conint, confloat, validator, SecretStr
from pydantic import BaseSettings, Extra

from src.constants import CONFIG_PATH


class ServiceSettings(BaseSettings):
    ENCRYPTION_KEY: typing.Optional[str]
    ENVIRONMENT: typing.Optional[str]

    class Config:
        extra = Extra.ignore


service_settings = ServiceSettings()


class RootConfig(BaseModel):
    @validator('*', pre=True, allow_reuse=True)
    def decrypt_config(cls, v):
        if isinstance(v, str) and v.startswith("enc(") and service_settings.ENCRYPTION_KEY:
            v = v[4:-1]
            v = cryptocode.decrypt(v, service_settings.ENCRYPTION_KEY)
        return v


class AWSConfig(RootConfig):
    key: SecretStr
    secret: SecretStr


class S3Config(RootConfig):
    region: str
    bucket_name: str
    base_path: str


class LocustConfig(RootConfig):
    port: int


class ServiceConfig(BaseModel):
    locust_config: LocustConfig
    aws_config: AWSConfig
    s3_config: S3Config


class OlafAdvancedParams(BaseModel):
    autostart: typing.Literal[True]
    autoquit_timeout: conint(ge=1, le=600)
    users: conint(ge=1, le=500)
    spawn_rate: confloat(ge=0.1, le=500)
    load_duration: conint(ge=20, le=10000)

    class Config:
        extra = Extra.ignore


@lru_cache(1)
def load_service_config() -> ServiceConfig:
    paths = [os.path.join(CONFIG_PATH, "config.yaml")]
    if service_settings.ENVIRONMENT:
        paths.append(os.path.join(CONFIG_PATH, f"config-{service_settings.ENVIRONMENT}.yaml"))
    merged_yaml = hiyapyco.load(*paths)
    service_config_object = ServiceConfig(**merged_yaml)
    return service_config_object


service_config = load_service_config()
