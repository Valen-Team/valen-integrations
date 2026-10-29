def handler(args: Args[Input]) -> Output:
    """The most likely option among `options`, with every option's probability; branch is the choice."""
    i = args.input
    choices = [{"value": value, "description": description} for value, description in _lines(i.options)]
    answers, model = _ask(args, [{"name": "q", "type": "choice", "instructions": i.question, "choices": choices}])
    result = _answer(answers[0])
    return {**result, "branch": result["choice"], "model": model}
