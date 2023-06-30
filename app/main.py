import json
import os
import secrets
import time
from typing import List, Literal, Iterator

import g4f
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

AUTH_TOKEN = os.getenv('TOKEN', '')
app = FastAPI()


class Message(BaseModel):
    role: Literal['user', 'assistant', 'system']
    content: str


class Args(BaseModel):
    messages: List[Message]
    model: Literal['gpt-3.5-turbo', 'gpt-4']
    provider: Literal['Lockchat', 'ChatgptLogin', 'Yqcloud'] = 'Yqcloud'
    stream: bool = False


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


def auth_by_token(token: str):
    """Auth by token, if token is None, then skip"""
    if not AUTH_TOKEN:
        return
    if token.lstrip('Bearer ') == AUTH_TOKEN:
        return
    raise HTTPException(status_code=403)


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


@app.api_route('/v1/chat/completions', methods=['GET', 'POST'])
def chat_completions(args: Args, token: str = Header(None)):
    auth_by_token(token)

    resp = g4f.ChatCompletion.create(
        model=args.model, provider=getattr(g4f.Provider, args.provider),
        messages=[m.dict() for m in args.messages], stream=args.stream)
    prompt = args.messages[-1].content if args.messages else ''
    if args.stream:
        return create_completion_stream(resp, Template('chat.completion.chunk', args.model, prompt, args.stream))
    else:
        return create_completion_json(resp, Template('chat.completion', args.model, prompt, args.stream))


if __name__ == '__main__':
    try:
        r = g4f.ChatCompletion.create(
            model='gpt-3.5-turbo', provider=getattr(g4f.Provider, 'Lockchat'),
            messages=[
                {"role": "user", "content": "Hello world"}], stream=False)
        print(r)
    except Exception as e:
        print(f'An error occurred: {e}')
