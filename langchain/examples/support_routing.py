"""Run with a real Valen endpoint, or point VALEN_BASE_URL at a local fixture server."""
import os
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_valen import ValenRouter


class State(TypedDict):
    input: str
    team: str


router = ValenRouter({
    'name': 'team', 'type': 'choice', 'instructions': 'Which team should handle this ticket?',
    'choices': [
        {'value': 'billing', 'description': 'Payments, duplicate charges and refunds'},
        {'value': 'technical', 'description': 'Software bugs and crashes'},
        {'value': 'review', 'description': 'Outside billing and technical support, or too little information'},
    ],
}, base_url=os.environ.get('VALEN_BASE_URL', 'https://api.valen-team.workers.dev'))

builder = StateGraph(State)
builder.add_node('judge', lambda state: state)
builder.add_edge(START, 'judge')
builder.add_conditional_edges('judge', router, {k: k for k in ('billing', 'technical', 'review')})
for team in ('billing', 'technical', 'review'):
    builder.add_node(team, lambda state, team=team: {'team': team})
    builder.add_edge(team, END)
graph = builder.compile()

if __name__ == '__main__':
    for text in ('I was charged twice. Please help.', 'The app crashes.', 'Can you recommend a birthday gift?'):
        print(graph.invoke({'input': text}))
