"""Runnable integrations, with routing rules kept outside the model."""
import os
from copy import deepcopy
from typing import Any

from langchain_core.runnables import Runnable, RunnableConfig
from valen_sdk import Valen
from valen_sdk.errors import ValenAPIError

from ._protocol import api_error_message, endpoint, evidence, map_answers, route_answer, thresholds, validate_questions


class ValenEvaluator(Runnable[Any, dict]):
    """Ask a fixed question set. Input is text or {input, image?: bytes}.

    Use ``{input: {...}}`` for structured evidence. A supplied client is caller-owned;
    otherwise each invocation opens and closes a remote SDK client. ``ainvoke`` uses
    LangChain's default executor bridge, leaving the event loop free.
    """

    name = "valen_evaluator"

    def __init__(self, questions, *, base_url='https://api.valen-team.workers.dev', api_key=None,
                 model='valen-2b', timeout=120.0, max_retries=2, client=None):
        self.questions = deepcopy(validate_questions(questions))
        self.base_url = endpoint(base_url)
        self.api_key = api_key if api_key is not None else os.environ.get('VALEN_API_KEY')
        self.model, self.timeout, self.max_retries = model, timeout, max_retries
        self.client = client

    def invoke(self, input, config: RunnableConfig | None = None, **kwargs):
        if isinstance(input, dict) and 'input' in input:
            value, image = input['input'], input.get('image')
        else:
            value, image = input, None
        payload = {'input': evidence(value, image), 'questions': deepcopy(self.questions), 'model': self.model}
        try:
            if self.client is not None:
                result = self.client.predict(payload)
            else:
                with Valen.remote(self.base_url, api_key=self.api_key, model=self.model,
                                  timeout=self.timeout, max_retries=self.max_retries,
                                  headers={'User-Agent': 'valen-langchain/0.1.0'}) as client:
                    result = client.predict(payload)
        except ValenAPIError as error:
            raise RuntimeError(api_error_message(error)) from error
        return map_answers(result, self.questions)


class ValenRouter(Runnable[Any, str]):
    """Return one branch key for LCEL or LangGraph conditional edges.

    Yes/No yields yes/no/unsure. Choice yields a candidate value; Score yields the
    most likely level (earlier level on ties), not rounded expected score.
    """

    name = "valen_router"

    def __init__(self, question, *, yes_at=0.7, no_at=0.3, **kwargs):
        self.yes_at, self.no_at = thresholds(yes_at, no_at)
        self.evaluator = ValenEvaluator([question], **kwargs)
        self.question = self.evaluator.questions[0]

    def invoke(self, input, config: RunnableConfig | None = None, **kwargs):
        result = self.evaluator.invoke(input, config=config)
        answer = result['answers'][self.question['name']]
        return route_answer(answer, self.question['type'], self.yes_at, self.no_at)['branch']
