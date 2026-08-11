from collections.abc import Sequence
from typing import Any

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool
from pydantic import Field


class ScriptedToolCallingModel(BaseChatModel):
    """Deterministic chat model that emits a fixed response sequence."""

    responses: list[AIMessage]
    response_index: int = 0
    bound_tool_names: list[str] = Field(default_factory=list)
    invocations: list[list[BaseMessage]] = Field(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "scripted-tool-calling-model"

    def bind_tools(
        self,
        tools: Sequence[BaseTool | dict[str, Any] | type | Any],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> "ScriptedToolCallingModel":
        del tool_choice, kwargs
        names = []
        for candidate in tools:
            if isinstance(candidate, dict):
                names.append(
                    candidate.get("name", candidate.get("function", {}).get("name"))
                )
            else:
                names.append(
                    getattr(candidate, "name", getattr(candidate, "__name__", ""))
                )
        self.bound_tool_names = [name for name in names if name]
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        del stop, run_manager, kwargs
        self.invocations.append(messages)
        if self.response_index >= len(self.responses):
            raise AssertionError("scripted model exhausted its responses")
        response = self.responses[self.response_index]
        self.response_index += 1
        return ChatResult(generations=[ChatGeneration(message=response)])
