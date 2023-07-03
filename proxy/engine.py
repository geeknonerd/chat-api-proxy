import json
import time
from abc import ABC, abstractmethod
from typing import Iterator, Any

import requests
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from simpleeval import EvalWithCompoundTypes

import g4f
from .config import G4fProviderCnf, ApiProviderCnf
from .schema import Args
from .template import Template


class Engine(ABC):
    @abstractmethod
    def json_response(self, args: Args):
        pass

    @abstractmethod
    def stream_response(self, args: Args):
        pass

    @staticmethod
    def create_completion_json(response: str, template: Template):
        """Return text completion results in plain JSON."""
        return template.copy().msg(response, finish_reason='stop').usage().build()

    @staticmethod
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


class G4fEngine(Engine):
    """g4f generator"""

    def __init__(self, config: G4fProviderCnf):
        self.config = config

    def check_provider(self, model: str) -> Any:
        """check provider is support or not"""
        # provider
        provider_name = getattr(self.config, model) if hasattr(self.config, model) else None
        provider = getattr(g4f.Provider, provider_name) if provider_name else None
        if not provider:
            return
        if model not in getattr(provider, 'model'):
            raise HTTPException(status_code=400, detail=f'the provider of config not support the model({model})')
        return provider

    def supports_stream(self, provider) -> bool:
        """supports stream or not"""
        return getattr(provider, 'supports_stream') if provider else False

    def json_response(self, args: Args):
        """full response by json"""
        provider = self.check_provider(args.model)

        # call g4f
        resp = g4f.ChatCompletion.create(
            model=args.model, provider=provider,
            messages=[m.dict() for m in args.messages], stream=False)

        # response
        prompt = args.messages[-1].content if args.messages else ''
        return self.create_completion_json(resp, Template('chat.completion', args.model, prompt, args.stream))

    def stream_response(self, args: Args):
        """response by stream"""
        provider = self.check_provider(args.model)

        # adapting stream
        supports_stream = self.supports_stream(provider)
        # call g4f
        resp = g4f.ChatCompletion.create(
            model=args.model, provider=provider,
            messages=[m.dict() for m in args.messages], stream=True if supports_stream and args.stream else False)

        # response
        prompt = args.messages[-1].content if args.messages else ''
        if not supports_stream:
            resp = [resp]
        return self.create_completion_stream(resp, Template('chat.completion.chunk', args.model, prompt, args.stream))


class ApiEngine(Engine):
    """api generator"""

    def __init__(self, config: ApiProviderCnf):
        self.eval_engine = EvalWithCompoundTypes
        self.config = config

    def check_tpl(self, model: str, resp_type: str = 'json') -> dict:
        """check template"""
        if not hasattr(self.config, model):
            raise HTTPException(status_code=500, detail=f'model not support or not config')
        provider = getattr(self.config, model)
        if not hasattr(provider, resp_type):
            raise HTTPException(status_code=500, detail=f'model not support the response type')
        tpl = getattr(provider, resp_type)
        if not (tpl.args_tpl and tpl.resp_tpl):
            raise HTTPException(status_code=500, detail=f'model template config error')
        return tpl

    @staticmethod
    def get_prompt(args: Args) -> str:
        return args.messages[-1].content if args.messages else ''

    def get_args_by_tpl(self, args: Args, args_tpl: str) -> Any:
        prompt = self.get_prompt(args)
        return self.eval_engine(
            names={'args': args.dict(), 'prompt': prompt, 'timestamp': int(time.time() * 1000)}).eval(args_tpl)

    def get_resp_by_tpl(self, resp: requests.Response, resp_tpl: str) -> Any:
        return self.eval_engine(names={'response': resp}).eval(resp_tpl)

    def json_response(self, args: Args):
        """full response by json"""
        tpl = self.check_tpl(args.model, resp_type='json')
        prompt = self.get_prompt(args)
        kwargs = self.get_args_by_tpl(args, tpl.args_tpl)
        response = requests.request(**kwargs)
        res = self.get_resp_by_tpl(response, tpl.resp_tpl)
        return self.create_completion_json(res, Template('chat.completion', args.model, prompt, args.stream))

    def stream_response(self, args: Args):
        """response by stream"""
        # TODO: support stream
        raise HTTPException(status_code=400, detail=f'api mode not support stream now')
