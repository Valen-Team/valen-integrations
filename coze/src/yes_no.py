def handler(args: Args[Input]) -> Output:
    """Probability that the answer to one yes/no question is yes, and its branch (SPEC §5)."""
    i = args.input
    answers, model = _ask(args, [{"name": "q", "type": "predicate", "instructions": i.question}])
    probability = answers[0]["probability"]
    yes_at = 0.7 if getattr(i, "yes_at", None) is None else i.yes_at
    no_at = 0.3 if getattr(i, "no_at", None) is None else i.no_at
    branch = "yes" if probability >= yes_at else "no" if probability <= no_at else "unsure"
    return {"probability": probability, "branch": branch, "model": model}
