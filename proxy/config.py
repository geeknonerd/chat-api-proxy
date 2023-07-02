from functools import lru_cache
from typing import Literal

from pydantic import BaseSettings

__all__ = ['get_settings']


class Settings(BaseSettings):
    """Global settings by environment"""
    mode: Literal['g4f', 'api'] = 'g4f'
    auth_token: str = ''
    gpt35turbo_provider: str = ''
    gpt4_provider: str = ''

    def get_cnf(self, gpt35turbo='', gpt4=''):
        """get config"""
        return {
            'gpt-3.5-turbo': {
                'provider': self.gpt35turbo_provider or gpt35turbo
            },
            'gpt-4': {
                'provider': self.gpt4_provider or gpt4
            }
        }

    def get_generator_cnf(self) -> dict:
        """get generator config"""
        if self.mode == 'api':
            return self.get_cnf()
        return self.get_cnf(gpt35turbo='Yqcloud', gpt4='Lockchat')  # China: ChatgptLogin, Yqcloud, Lockchat


@lru_cache()
def get_settings() -> Settings:
    """cache settings"""
    return Settings()
