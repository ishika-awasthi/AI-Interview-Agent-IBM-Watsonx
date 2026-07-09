from datetime import datetime
from pathlib import Path

# Anchor to the project root (parent of this report/ package) rather than
# the current working directory, so history files land in a predictable
# place regardless of where `python main.py` is invoked from.
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent


def save_interview(
    role: str,
    results: list[dict[str, str]],
    summary: str,
) -> Path:
    """Save a completed interview session to a timestamped text file.

    Args:
        role:     The interview topic/role label (e.g. ``"Python"``).
        results:  List of dicts with keys ``'question'``, ``'answer'``,
                  and ``'feedback'``.
        summary:  The overall session summary text.

    Returns:
        The :class:`~pathlib.Path` of the saved file.

    Raises:
        OSError: When the history directory or file cannot be created/written.
    """
    history_dir = PROJECT_ROOT / "interview_history"
    history_dir.mkdir(exist_ok=True)

    filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.txt")
    filepath = history_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"Interview Type: {role}\n\n")

        for i, item in enumerate(results, start=1):
            f.write(f"Question {i}\n")
            f.write(item["question"] + "\n\n")

            f.write("Answer\n")
            f.write(item["answer"] + "\n\n")

            f.write("Feedback\n")
            f.write(item["feedback"] + "\n\n")

            f.write("-" * 70 + "\n\n")

        f.write("FINAL SUMMARY\n\n")
        f.write(summary)

    return filepath
