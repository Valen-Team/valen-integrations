from dify_plugin import Tool
from valen_client import invoke


class ValenTool(Tool):
    def _invoke(self, tool_parameters):
        result = invoke(self.runtime.credentials, 'evaluate', tool_parameters)
        for key, value in result.items():
            yield self.create_variable_message(key, value)
        yield self.create_json_message(result)
