from functools import lru_cache
from typing import Literal

from pydantic import BaseSettings

__all__ = ['get_settings']


class Settings(BaseSettings):
    """Global settings by environment"""
    mode: Literal['g4f'] = 'g4f'
    auth_token: str = ''
    gpt35turbo_provider: str = 'Yqcloud'  # China: ChatgptLogin, Yqcloud, Lockchat
    gpt4_provider: str = 'Lockchat'  # China: Lockchat

    def get_generator_cnf(self) -> dict:
        default_dict = {
            'g4f': {
                'gpt-3.5-turbo': {
                    'provider': self.gpt35turbo_provider
                },
                'gpt-4': {
                    'provider': self.gpt4_provider
                }
            }
        }
        return default_dict[self.mode]


@lru_cache()
def get_settings() -> Settings:
    """cache settings"""
    return Settings()
