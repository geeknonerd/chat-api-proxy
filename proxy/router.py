import json
import secrets
import time
from typing import List, Literal, Iterator, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, validator

import g4f
from .config import get_settings

router = APIRouter()

config = get_settings().get_generator_cnf()


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


class Template:
    def __init__(self, obj: str, model: str, prompt: str = '', stream: bool = False):
        self._data = {
            "id": f"chatcmpl-{secrets.token_hex(12)}",
            "object": obj,
            "created": round(time.time()),
            "model": model,
            "choices": [],
        }
        self.prompt = prompt
        self.stream = stream
        self._cur_data = None

    def copy(self):
        """Start make data"""
        self._cur_data = self._data.copy()
        return self

    @staticmethod
    def make_choice(text: str, index: int = 0, finish_reason: str = None, **kwargs):
        """Make json response dict"""
        return {
            "index": index,
            "message": {"role": "assistant", "content": text},
            "finish_reason": finish_reason,
            # "logprobs": None,
        }

    @staticmethod
    def make_stream_choice(text: str, index: int = 0, finish_reason: str = None, role: str = None):
        """Make stream dict"""
        data = {
            "index": index,
            "delta": {"content": text} if finish_reason is None else {},
            "finish_reason": finish_reason,
        }
        if role:
            data["delta"]["role"] = role
        return data

    @staticmethod
    def make_usage():
        """Make token usage info"""
        return {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

    def msg(self, text: str, finish_reason: str = None, role: str = None):
        """Add message"""
        make_func = self.make_stream_choice if self.stream else self.make_choice
        self._cur_data["choices"] = [make_func(text, finish_reason=finish_reason, role=role)]
        return self

    def usage(self):
        """Add token usage info"""
        self._cur_data["usage"] = self.make_usage()
        return self

    def stream_end_msg(self, stream_content: str):
        """Add the end data of stream"""
        self._cur_data = {
            'prompt_content': self.prompt,
            'stream_content': stream_content,
        }
        return self

    def build(self):
        """Build current data dict"""
        cur_data = self._cur_data
        self._cur_data = None
        return cur_data


def check_provider(provider: Any, args: Args):
    if not provider:
        return
    if args.model not in getattr(provider, 'model'):
        raise HTTPException(status_code=400, detail=f'the provider of config not support the model({args.model})')


def create_completion_json(response: str, template: Template):
    """Return text completion results in plain JSON."""
    return template.copy().msg(response, finish_reason='stop').usage().build()


def create_completion_stream(response: Iterator[str], template: Template):
    """Return text completion results in event stream."""

    # Serialize data for event stream.
    def serialize(data: dict):
        data = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        return f"data: {data}\n\n"

    def stream():
        buffers = []
        role = 'assistant'
        for buffer in response:
            if buffer:
                buffers.append(buffer)
                yield serialize(template.copy().msg(buffer, role=role).build())
            if role:
                role = None

        yield serialize(template.copy().msg('', finish_reason='stop').build())
        yield "data: [DONE]\n\n"

        yield json.dumps(template.stream_end_msg(''.join(buffers)).usage().build(), ensure_ascii=False,
                         separators=(",", ":"))

    return StreamingResponse(stream(), media_type='text/event-stream')


@router.api_route('/v1/chat/completions', methods=['GET', 'POST'])
async def chat_completions(args: Args):
    # provider
    provider_name = config.get(args.model, {}).get('provider')
    provider = getattr(g4f.Provider, provider_name) if provider_name else None
    check_provider(provider, args)

    # adapting stream
    supports_stream = getattr(provider, 'supports_stream') if provider else False
    # call g4f
    resp = g4f.ChatCompletion.create(
        model=args.model, provider=provider,
        messages=[m.dict() for m in args.messages], stream=True if supports_stream and args.stream else False)

    # response
    prompt = args.messages[-1].content if args.messages else ''
    if args.stream:
        if not supports_stream:
            resp = [resp]
        return create_completion_stream(resp, Template('chat.completion.chunk', args.model, prompt, args.stream))
    else:
        return create_completion_json(resp, Template('chat.completion', args.model, prompt, args.stream))
