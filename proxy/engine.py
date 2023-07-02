import json
from abc import ABC, abstractmethod
from typing import Iterator, Any

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

import g4f
from .schema import Args
from .template import Template


class Engine(ABC):
    @abstractmethod
    def json_response(self, args: Args):
        pass

    @abstractmethod
    def stream_response(self, args: Args):
        pass


class G4fEngine(Engine):
    """g4f generator"""

    def __init__(self, config: dict):
        self.config = config

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

    def check_provider(self, model: str) -> Any:
        """check provider is support or not"""
        # provider
        provider_name = self.config.get(model, {}).get('provider')
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

    def __init__(self, config: dict):
        self.config = config

    def json_response(self, args: Args):
        """full response by json"""
        pass

    def stream_response(self, args: Args):
        """response by stream"""
        pass
