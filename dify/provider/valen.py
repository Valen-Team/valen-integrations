from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from valen_client import validate_credentials


class ValenProvider(ToolProvider):
    def _validate_credentials(self, credentials):
        try:
            validate_credentials(credentials)
        except Exception as error:
            raise ToolProviderCredentialValidationError(str(error)) from error
