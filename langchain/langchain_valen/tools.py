"""An agent tool with an explicit schema and standard LangChain error handling."""
from typing import Any
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.tools import BaseTool, ToolException
from .runnables import ValenEvaluator
from ._protocol import api_error_message


class DecisionInput(BaseModel):
    input: str = Field(description='Text to judge against the configured questions')


class ValenDecisionTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = 'valen_decisions'
    description: str = 'Evaluate text against configured Valen questions and return named probabilities.'
    args_schema: type[BaseModel] = DecisionInput
    evaluator: Any = Field(exclude=True, repr=False)

    def _run(self, input: str):
        try:
            return self.evaluator.invoke(input)
        except Exception as error:
            raise ToolException(api_error_message(error)) from error
