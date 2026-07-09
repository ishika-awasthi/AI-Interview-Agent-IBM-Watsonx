"""
Prompt builders — single source of truth for both CLI (main.py) and
Streamlit (app.py) interfaces.

Exports:
  TOPIC_LABELS               -> dict mapping menu choice -> role label
  build_question_prompt(topic, q_num, asked_questions, total=None)
  build_evaluation_prompt(topic, question, answer)
  build_summary_prompt(topic, results)
"""

import re
from pathlib import Path

# ── Prompt file paths ─────────────────────────────────────────────────────────

PROMPTS_DIR: Path = Path(__file__).resolve().parent

QUESTION_PROMPT: Path = PROMPTS_DIR / "question_prompt.txt"
EVALUATION_PROMPT: Path = PROMPTS_DIR / "evaluation_prompt.txt"
SUMMARY_PROMPT: Path = PROMPTS_DIR / "summary_prompt.txt"

# ── Topic menu ─────────────────────────────────────────────────────────────
#
# Single source of truth for both interfaces: main.py (CLI) builds its
# numbered menu from this dict, and app.py (Streamlit) builds its radio
# labels from it too (see app.py's TOPIC_OPTIONS, which maps display text
# with emoji to these same role strings). Keeping both driven off this one
# dict prevents the two interfaces from silently drifting out of sync.
TOPIC_LABELS: dict[str, str] = {
    "1": "Python",
    "2": "Machine Learning",
    "3": "HR",
    "4": "Cloud and DevOps",
    "5": "Data Structures and Algorithms",
}


def build_question_prompt(
    topic: str,
    q_num: int,
    asked_questions: list[str],
    total: int | None = None,
) -> str:
    """Build a prompt that asks the model to generate one interview question.

    Injects *topic* into the template and appends a position label
    (``"question 2 of 5"`` when *total* is given, ``"question 2"`` otherwise).
    When *asked_questions* is non-empty the prompt instructs the model to
    avoid repeating them.

    Args:
        topic:           The interview role/subject (e.g. ``"Python"``).
        q_num:           1-based position of this question in the session.
        asked_questions: List of questions already asked; may be empty.
        total:           Total number of questions in the session, or ``None``
                         to omit the ``"of N"`` context.

    Returns:
        The fully-assembled prompt string ready to send to the model.

    Raises:
        FileNotFoundError: When ``question_prompt.txt`` does not exist.
    """
    with open(QUESTION_PROMPT, "r", encoding="utf-8") as f:
        template = f.read()

    prompt = template.replace("{role}", topic)

    q_label = (
        f"question {q_num} of {total}"
        if total is not None
        else f"question {q_num}"
    )

    if asked_questions:
        previous = "\n".join(f"- {q}" for q in asked_questions)
        prompt += (
            f"\n\nThis is {q_label}. "
            f"Do NOT repeat any of these previously asked questions:\n{previous}"
        )
    else:
        prompt += f"\n\nThis is {q_label}."

    return prompt


def build_evaluation_prompt(topic: str, question: str, answer: str) -> str:
    """Build a prompt that asks the model to evaluate a candidate's answer.

    Injects *topic*, *question*, and *answer* into the evaluation template.

    Args:
        topic:    The interview role/subject (e.g. ``"Python"``).
        question: The interview question that was posed.
        answer:   The candidate's answer to evaluate.

    Returns:
        The fully-assembled evaluation prompt string.

    Raises:
        FileNotFoundError: When ``evaluation_prompt.txt`` does not exist.
    """
    with open(EVALUATION_PROMPT, "r", encoding="utf-8") as f:
        template = f.read()

    # Substitute all three placeholders in a single simultaneous pass over the
    # ORIGINAL template, rather than chaining .replace() calls on a growing
    # string. Chaining is unsafe here: {question} and {answer} come from the
    # model / the candidate and are not sanitised, so if either one happens
    # to contain the literal text "{answer}" (or "{role}"), a later .replace()
    # call would incorrectly rewrite that inserted content too. A single
    # combined pass only ever matches placeholders in the template itself.
    replacements = {"{role}": topic, "{question}": question, "{answer}": answer}
    pattern = re.compile("|".join(re.escape(k) for k in replacements))
    return pattern.sub(lambda m: replacements[m.group(0)], template)


def build_summary_prompt(topic: str, results: list[dict[str, str]]) -> str:
    """Build a prompt that asks the model to produce a full session summary.

    Formats the complete interview transcript (all questions, answers, and
    per-question feedback) and injects it into the summary template.

    Args:
        topic:   The interview role/subject (e.g. ``"Python"``).
        results: List of result dicts, each with keys
                 ``'question'``, ``'answer'``, and ``'feedback'``.

    Returns:
        The fully-assembled summary prompt string.

    Raises:
        FileNotFoundError: When ``summary_prompt.txt`` does not exist.
    """
    with open(SUMMARY_PROMPT, "r", encoding="utf-8") as f:
        template = f.read()

    transcript_parts = []
    for i, item in enumerate(results, start=1):
        transcript_parts.append(
            f"Question {i}: {item['question']}\n"
            f"Answer {i}: {item['answer']}\n"
            f"Feedback {i}: {item['feedback']}"
        )
    transcript = "\n\n".join(transcript_parts)

    return (
        f"Interview Role: {topic}\n\n"
        f"{template}\n\n"
        f"Here is the full interview transcript to base your report on:\n\n"
        f"{transcript}"
    )
