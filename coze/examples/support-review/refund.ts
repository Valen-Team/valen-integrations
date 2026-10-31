// Coze's Code node supplies the Args and Output types. Declare result as Object.
async function main({ params }: Args): Promise<Output> {
  const result = {
    destination: "refund",
    input: params.input,
    branch: params.branch,
    probability: params.probability,
    model: params.model,
  };
  return { result };
}
