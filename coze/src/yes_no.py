def handler(args: Args[Input]) -> Output:
    """Probability that the answer to one yes/no question is yes, and its branch (SPEC §5)."""
    i = args.input
    yes_at = 0.7 if getattr(i, "yes_at", None) is None else i.yes_at
    no_at = 0.3 if getattr(i, "no_at", None) is None else i.no_at
    thresholds(yes_at, no_at)
    answers, model = _ask(args, [single_question("predicate", i.question)])
    probability = answers[0]["probability"]
    branch = "yes" if probability >= yes_at else "no" if probability <= no_at else "unsure"
    return {"probability": probability, "branch": branch, "model": model}
