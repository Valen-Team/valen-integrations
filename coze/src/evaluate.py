def handler(args: Args[Input]) -> Output:
    """Several questions about one input, in the Decisions `questions` format; answers keyed by name (SPEC §4)."""
    answers, model = _ask(args, json.loads(args.input.questions))
    return {"answers": {answer["name"]: _answer(answer) for answer in answers}, "model": model}
