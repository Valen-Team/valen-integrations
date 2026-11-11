def handler(args: Args[Input]) -> Output:
    """The box around what `question` describes in the image, as fractions of its width and height (SPEC §5)."""
    answers, model = _ask(args, [single_question("bbox", args.input.question)])
    return {**_answer(answers[0]), "model": model}
