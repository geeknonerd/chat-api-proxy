from typing import List, Literal

from pydantic import BaseModel, Field, validator

import g4f


class Message(BaseModel):
    role: Literal['user', 'assistant', 'system']
    content: str


class Args(BaseModel):
    messages: List[Message]
    model: str
    stream: bool = False
    temperature: float = Field(1.0, ge=0, le=2.0)
    top_p: float = Field(1.0, ge=0, le=1.0)
    n: int = Field(1, ge=1)
    max_tokens: int = Field(None, le=4096)
    presence_penalty: float = Field(0, ge=-2.0, le=2.0)
    frequency_penalty: float = Field(0, ge=-2.0, le=2.0)

    @validator('model')
    def validate_model(cls, m):
        if m not in g4f.ModelUtils.convert.keys():
            raise ValueError(f'model not g4f models: {g4f.ModelUtils.convert.keys()}')
        return m
