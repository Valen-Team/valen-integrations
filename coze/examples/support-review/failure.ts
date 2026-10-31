// Bind errorBody to the plugin's errorBody Object, not its normal branch output.
// Coze's Code node supplies Args and Output. Declare result as Object.
async function main({ params }: Args): Promise<Output> {
  return {
    result: {
      destination: "request_failure",
      input: params.input,
      error: params.errorBody,
    },
  };
}
