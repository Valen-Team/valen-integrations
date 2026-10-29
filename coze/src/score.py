def handler(args: Args[Input]) -> Output:
    """Expected level and the most likely level among `levels` (lowest first); branch is that level."""
    i = args.input
    levels = [{"label": label, "description": description} for label, description in _lines(i.levels)]
    answers, model = _ask(args, [{"name": "q", "type": "score", "instructions": i.question, "levels": levels}])
    result = _answer(answers[0])
    return {**result, "branch": result["level"], "model": model}
