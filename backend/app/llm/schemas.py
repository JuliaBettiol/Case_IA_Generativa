from dataclasses import dataclass, field

@dataclass
class LLMUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }

@dataclass
class LLMToolCall:
    id: str
    name: str
    arguments: str

@dataclass
class LLMMessage:
    content: str | None = None
    tool_calls: list[LLMToolCall] = field(
        default_factory=list
    )

@dataclass
class LLMResponse:
    message: LLMMessage
    usage: LLMUsage | None = None