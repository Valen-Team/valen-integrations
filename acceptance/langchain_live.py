"""Verify an installed wheel with synthetic real-API image, tool, async and routing calls."""
import asyncio
import hashlib
import json
import os
import zipfile
from pathlib import Path
import langchain_valen
from langchain_valen import ValenEvaluator, ValenDecisionTool
from langchain_valen.example import graph

ROOT = Path(__file__).resolve().parents[1]


def main():
    wheel = Path(os.environ['VALEN_ACCEPTANCE_WHEEL'])
    installed = Path(langchain_valen.__file__).parent
    assert installed.resolve() != (ROOT/'langchain/langchain_valen').resolve(), 'Use a clean wheel environment'
    with zipfile.ZipFile(wheel) as archive:
        for name in archive.namelist():
            if name.startswith('langchain_valen/') and name.endswith('.py'):
                assert archive.read(name) == (installed/name.split('/', 1)[1]).read_bytes(), name
    image = (ROOT/'tests/assets/red-square.png').read_bytes()
    image_result = ValenEvaluator([{'name': 'red', 'type': 'predicate',
                                   'instructions': 'The image shows a red square.'}]).invoke({
                                       'input': 'Inspect the image.', 'image': image})
    assert image_result['answers']['red']['probability'] >= .7
    refund = ValenEvaluator([{'name': 'refund', 'type': 'predicate',
                             'instructions': 'The customer requests a refund.'}])
    tool_result = ValenDecisionTool(evaluator=refund).invoke({'input': 'Please refund the duplicate charge.'})
    async_result = asyncio.run(refund.ainvoke('Please refund the duplicate charge.'))
    assert tool_result['answers']['refund']['probability'] >= .7
    assert async_result['answers']['refund']['probability'] >= .7
    destinations = []
    for ticket, expected in [('I was charged twice. Please help.', 'billing'),
                             ('The app crashes.', 'technical'),
                             ('Can you recommend a birthday gift?', 'review')]:
        result = graph.invoke({'input': ticket})
        assert result['team'] == expected, result
        destinations.append(result)
    asked = [{'name': f'q{i}', 'type': 'predicate', 'instructions': 'A synthetic judgment.'} for i in range(9)]
    try:
        ValenEvaluator(asked).invoke('Synthetic limit test')
    except RuntimeError as error:
        limit_error = str(error)
        assert 'HTTP 400' in limit_error and '8' in limit_error and 'request ID:' in limit_error, limit_error
    else:
        raise AssertionError('Hosted service unexpectedly accepted nine questions')
    report = {'installed_from': 'wheel in a separate environment',
              'wheel_sha256': hashlib.sha256(wheel.read_bytes()).hexdigest(),
              'installed_python_files_match_final_wheel': True,
              'image': image_result, 'tool': tool_result, 'async': async_result,
              'destinations': destinations, 'limit_error': limit_error}
    (ROOT/'validation/langchain-live.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Image, tool, async, three graph destinations and hosted limit: passed', flush=True)


if __name__ == '__main__':
    main()
