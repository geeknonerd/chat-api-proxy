import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal, Any

import yaml
from pydantic import BaseSettings

__all__ = ['get_settings', 'G4fProviderCnf', 'ApiProviderCnf', 'ApiExtTpl']

logger = logging.getLogger('uvicorn.error')


class Settings(BaseSettings):
    """Global settings by environment"""
    mode: Literal['g4f', 'api'] = 'g4f'
    auth_token: str = ''
    gpt35turbo_provider: str = ''
    gpt4_provider: str = ''
    gpt35turbo_stream_provider: str = ''
    gpt4_stream_provider: str = ''

    def get_generator_cnf(self) -> Any:
        """get generator config"""
        if self.mode == 'api':
            return ApiProviderCnf(
                gpt35turbo=ApiArgs(json=self.gpt35turbo_provider or 'aitianhu.yaml',
                                   stream=self.gpt35turbo_stream_provider or 'aitianhu.yaml'),
                gpt4=ApiArgs(json=self.gpt4_provider, stream=self.gpt4_stream_provider))
        return G4fProviderCnf(
            gpt35turbo=self.gpt35turbo_provider, gpt4=self.gpt4_provider)  # China: ChatgptLogin, Yqcloud, Lockchat


@lru_cache()
def get_settings() -> Settings:
    """cache settings"""
    return Settings()


@dataclass()
class G4fProviderCnf:
    gpt35turbo: str = 'Yqcloud'
    gpt4: str = 'Lockchat'

    def __init__(self, gpt35turbo=None, gpt4=None):
        logger.info(f'G4fProviderCnf: {gpt35turbo=}, {gpt4}')
        if gpt35turbo:
            self.gpt35turbo = gpt35turbo
        if gpt4:
            self.gpt4 = gpt4

    def __getattribute__(self, item):
        item = item.replace('-', '').replace('.', '')
        return object.__getattribute__(self, item)


@dataclass()
class ApiArgs:
    json: str = ''
    stream: str = ''


@dataclass()
class ApiExtTpl:
    models: list
    args_tpl: str
    resp_way: str
    resp_tpl: str


@dataclass()
class ApiProvider:
    json: ApiExtTpl
    stream: ApiExtTpl


@dataclass()
class ApiProviderCnf:
    gpt35turbo: ApiProvider
    gpt4: ApiProvider

    def __init__(self, gpt35turbo: ApiArgs = None, gpt4: ApiArgs = None):
        logger.info(f'ApiProviderCnf: {gpt35turbo=}, {gpt4=}')
        if gpt35turbo:
            self.gpt35turbo = self.load_provider(gpt35turbo)
        if gpt4:
            self.gpt4 = self.load_provider(gpt4)

    @staticmethod
    def load_provider(args: ApiArgs):
        """load provider for ext dir"""
        if not args:
            return
        json_tpl = None
        stream_tpl = None
        if args.json:
            tpl = ApiExtTpl(**ApiProviderCnf.load_yaml(f"ext/{args.json}"))
            if tpl.resp_way in ['once', 'octet-stream']:
                json_tpl = tpl
        if args.stream:
            tpl = ApiExtTpl(**ApiProviderCnf.load_yaml(f"ext/{args.stream}"))
            if tpl.resp_way in ['once', 'octet-stream', 'event-stream']:
                stream_tpl = tpl
        provider = ApiProvider(json=json_tpl, stream=stream_tpl)
        return provider

    @staticmethod
    def load_yaml(path: str) -> dict:
        with open(path) as file:
            data = yaml.safe_load(file)
        return data

    def __getattribute__(self, item):
        item = item.replace('-', '').replace('.', '')
        return object.__getattribute__(self, item)
