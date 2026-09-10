import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv
from LLMs.llm_communicator_ABC import LLMCommunicatorABC
import time

load_dotenv()

class OpenAIAPICommunicator(LLMCommunicatorABC):
    """
    Communicator for the OpenAI API.
    """

    def __init__(self, model: str, system_prompt: Optional[str] = None, record_conversation: bool = False):
        """
        Args:
            system_prompt: Optional system prompt to seed the conversation.
        """
        super().__init__(system_prompt)
        if not os.environ.get('OPENAI_API_KEY'):
            raise RuntimeError('OPENAI_API_KEY is required for a live KubeGuard run.')
        self.client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
        self.model = model
        self.temperature = 0.0
        self.record_conversation = record_conversation

        self._last_usage = None
        self._last_latency_ms = None

    def set_model(self, model: str) -> None:
        """Change the OpenAI model at runtime."""
        self.model = model

    def send_message(self, user_message: str, temperature: float = 0) -> str:
        """
        Append a user message and get the assistant reply (as text).

        Returns:
            Assistant message content (str).
        """
        t0 = time.time()

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[self.conversation[0], {"role": "user", "content": user_message}],
            temperature=self.temperature,
            top_p=1.0
        )

        self._last_latency_ms = (time.time() - t0) * 1000.0
        if getattr(resp, "usage", None) is not None:
            pt = getattr(resp.usage, "prompt_tokens", None) or getattr(resp.usage, "input_tokens", 0) or 0
            ct = getattr(resp.usage, "completion_tokens", None) or getattr(resp.usage, "output_tokens", 0) or 0
            tt = getattr(resp.usage, "total_tokens", 0) or (pt + ct)
            self._last_usage = {
                "input_tokens": int(pt),
                "output_tokens": int(ct),
                "total_tokens": int(tt),
                "model": self.model,
            }
        else:
            self._last_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "model": self.model}

        content = resp.choices[0].message.content
        if self.record_conversation:
            self.conversation.extend([
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": content},
            ])
        return content

    def get_last_usage(self) -> dict:
        """Returns {'input_tokens', 'output_tokens', 'total_tokens', 'model'} for the most recent call."""
        return self._last_usage or {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "model": self.model}

    def get_last_latency_ms(self) -> float:
        """Returns wall-clock latency (ms) for the most recent call."""
        return float(self._last_latency_ms or 0.0)

    def get_model(self) -> str:
        return self.model

    def set_temperature(self, temperature: float):
        self.temperature = temperature
