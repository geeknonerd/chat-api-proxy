import secrets
import time


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
