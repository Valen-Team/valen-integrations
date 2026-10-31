import asyncio
import importlib.util
import sys
from pathlib import Path
import pytest
from langchain_valen import ValenEvaluator, ValenRouter, ValenDecisionTool
from langchain_core.tools import ToolException
from langchain_core.runnables import RunnablePassthrough
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

ROOT=Path(__file__).resolve().parents[1]
Q={'name':'urgent','type':'predicate','instructions':'The customer needs urgent help.'}


def test_evaluator_real_sdk_transport(api):
    evaluator=ValenEvaluator([Q],base_url=api['url'],api_key='synthetic-key')
    value=evaluator.invoke({'input':{'工单':'你好'},'image':b'\x89PNG\r\n\x1a\nfixture'})
    assert value=={'answers':{'urgent':{'probability':.5}},'model':'valen-fixture'}
    sent=api['requests'][0]
    assert sent['path']=='/v1/decisions'
    assert sent['headers']['Authorization']=='Bearer synthetic-key'
    assert sent['body']['input'][0]['content'][0]['text']=='{\n  "工单": "你好"\n}'
    assert sent['body']['input'][0]['content'][1]['image_url'].startswith('data:image/png;base64,')


def test_lcel_and_async(api):
    router=ValenRouter(Q,base_url=api['url'])
    chain=RunnablePassthrough.assign(branch=router)
    assert chain.invoke({'input':'hello'})['branch']=='unsure'
    assert asyncio.run(router.ainvoke('hello'))=='unsure'


def test_real_langgraph_conditional_edges(api):
    class State(TypedDict):
        input: str
        branch: str
    router=ValenRouter(Q,base_url=api['url'])
    builder=StateGraph(State)
    builder.add_node('judge',lambda state:state);builder.add_edge(START,'judge')
    builder.add_conditional_edges('judge',router,{'yes':'yes','no':'no','unsure':'review'})
    for node in ('yes','no','review'):
        builder.add_node(node,lambda state,node=node:{'branch':node});builder.add_edge(node,END)
    assert builder.compile().invoke({'input':'hello'})['branch']=='review'


def test_tool_errors_use_langchain_policy(api):
    tool=ValenDecisionTool(evaluator=ValenEvaluator([Q],base_url=api['url'],max_retries=0))
    assert tool.invoke({'input':'hello'})['model']=='valen-fixture'
    api.update(status=400,response={'detail':'Invalid question'})
    with pytest.raises(RuntimeError,match='HTTP 400: Invalid question.*fixture-123'):
        tool.evaluator.invoke('hello')
    with pytest.raises(ToolException,match='HTTP 400: Invalid question.*fixture-123'): tool.invoke({'input':'hello'})
    tool.handle_tool_error=True
    assert 'Invalid question' in tool.invoke({'input':'hello'})


def test_malformed_response_and_bad_config(api):
    with pytest.raises(ValueError,match='Thresholds'): ValenRouter(Q,yes_at=.2,no_at=.7)
    api['response']={'model':'v','answers':[]}
    with pytest.raises(ValueError,match='incomplete'): ValenEvaluator([Q],base_url=api['url']).invoke('hello')


def test_server_owns_hosted_question_limit(api):
    asked=[dict(Q,name=f'q{i}') for i in range(9)]
    api.update(status=400,response={'detail':'At most 8 questions'})
    with pytest.raises(RuntimeError,match='HTTP 400: At most 8 questions.*fixture-123'):
        ValenEvaluator(asked,base_url=api['url']).invoke('synthetic ticket')
    assert api['requests'][0]['body']['questions']==asked


def test_dify_sdk_registration():
    # The Dify runtime monkey-patches networking; keep it out of the LangChain host.
    import subprocess
    code = "from dify_plugin import DifyPluginEnv; from dify_plugin.core.plugin_registration import PluginRegistration; r=PluginRegistration(DifyPluginEnv()); assert set(r.tools_mapping['valen'][2]) == {'yes_no','choice','score','evaluate'}"
    subprocess.run([sys.executable, '-c', code], cwd=ROOT/'dify', check=True, capture_output=True)


def test_dify_actual_sdk_and_declared_variables(api):
    from types import SimpleNamespace
    sys.path.insert(0,str(ROOT/'dify'))
    from valen_client import invoke,validate_credentials
    credentials={'base_url':api['url']}
    validate_credentials(credentials)
    result=invoke(credentials,'yes_no',{'input':'hello','question':'Urgent?'})
    assert result=={'probability':.5,'branch':'unsure','model':'valen-fixture'}
    result=invoke(credentials,'evaluate',{'input':'hello','questions':[Q]})
    assert result['answers']['urgent']['probability']==.5
    before=len(api['requests'])
    with pytest.raises(ValueError,match='PNG, JPEG or WebP'):
        invoke(credentials,'yes_no',{'input':'hello','question':'Urgent?',
            'image':SimpleNamespace(mime_type='image/gif',blob=b'GIF89a')})
    assert len(api['requests'])==before
    api.update(status=400,response={'detail':'Invalid question'})
    with pytest.raises(RuntimeError,match='HTTP 400: Invalid question.*fixture-123'):
        invoke(credentials,'yes_no',{'input':'hello','question':'Urgent?'})
