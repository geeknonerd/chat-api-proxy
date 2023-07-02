from typing import List, Literal

from pydantic import BaseModel, validator

import g4f


class Message(BaseModel):
    role: Literal['user', 'assistant', 'system']
    content: str


class Args(BaseModel):
    messages: List[Message]
    model: str
    stream: bool = False

    @validator('model')
    def validate_model(cls, m):
        if m not in g4f.ModelUtils.convert.keys():
            raise ValueError(f'model not g4f models: {g4f.ModelUtils.convert.keys()}')
        return m
