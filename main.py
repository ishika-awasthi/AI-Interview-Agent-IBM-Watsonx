"""
AI Interview Trainer — entry point.

Usage:
    python main.py

Requires a .env file in the project root with:
    WATSONX_API_KEY=<your IBM Cloud IAM API key>
    WATSONX_PROJECT_ID=<your WatsonX project UUID>
    WATSONX_URL=https://us-south.ml.cloud.ibm.com
"""

import logging
import sys

from dotenv import load_dotenv

from ibm_watsonx_ai.foundation_models import ModelInference

from models.watsonx_client import build_client, generate
from report.history_manager import save_interview
from utils.text_utils import clean_response, parse_feedback
from prompts.interview_prompt import (
    TOPIC_LABELS,
    build_question_prompt,
    build_evaluation_prompt,
    build_summary_prompt,
)

TOTAL_QUESTIONS = 5

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── helpers ──────────────────────────────────────────────────────────────────

def divider(char: str = "─", width: int = 60) -> None:
    """Print a horizontal rule of *width* repetitions of *char*."""
    print(char * width)


def section(title: str) -> None:
    """Print a labelled section divider to stdout."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def welcome() -> None:
    """Print the application welcome banner."""
    divider("═")
    print("  🎓  AI Interview Trainer  — powered by IBM Granite")
    divider("═")
    print()
    print("  This session will ask you 5 interview questions,")
    print("  evaluate each of your answers, and give a final summary.")
    print()


def choose_topic() -> str:
    """Prompt the user to pick a topic and return its label string."""
    print("  Select an interview topic:\n")
    for key, label in TOPIC_LABELS.items():
        print(f"    [{key}]  {label}")
    print()

    valid_keys = list(TOPIC_LABELS.keys())
    prompt_range = f"{valid_keys[0]}-{valid_keys[-1]}" if len(valid_keys) > 1 else valid_keys[0]

    while True:
        choice = input(f"  Enter {prompt_range}: ").strip()
        if choice in TOPIC_LABELS:
            return TOPIC_LABELS[choice]
        print(f"  Invalid choice — please enter {prompt_range}.")


def print_feedback(feedback: str) -> None:
    """
    Pretty-print the structured feedback block returned by Granite.
    Each labelled line gets its own visual row.

    Uses the shared parse_feedback() from utils.text_utils so the CLI parses
    Granite's structured output identically to the Streamlit app.
    """
    parsed = parse_feedback(feedback)

    # Display
    print()
    score_labels = ["Overall Score", "Technical Accuracy", "Clarity", "Completeness"]
    for lbl in score_labels:
        val = parsed.get(lbl, "—")
        print(f"  {lbl:<22} {val}")

    print()
    for lbl in ["Strengths", "Weaknesses", "Ideal Answer"]:
        val = parsed.get(lbl, "—")
        print(f"  {lbl}:")
        print(f"    {val}")
        print()


# ── main session loop ─────────────────────────────────────────────────────────

def run_session(model: ModelInference, topic: str) -> None:
    """Run one complete interview session for *topic*.

    Loops over TOTAL_QUESTIONS rounds, each of which:

    1. Asks the model to generate a fresh question.
    2. Reads the candidate's answer from stdin.
    3. Asks the model to evaluate the answer and prints feedback.

    After all rounds, generates a session summary, prints it, and saves
    the transcript to ``interview_history/``.

    Args:
        model: The authenticated ModelInference client.
        topic: Interview role/subject label (e.g. ``"Python"``).
    """
    results: list[dict[str, str]] = []
    asked_questions: list[str] = []

    for q_num in range(1, TOTAL_QUESTIONS + 1):
        section(f"Question {q_num} of {TOTAL_QUESTIONS}  —  {topic}")

        # 1. Ask Granite to generate a question
        print("\n  Generating question …\n")
        try:
            q_prompt = build_question_prompt(topic, q_num, asked_questions)
            question = clean_response(generate(model, q_prompt))
        except FileNotFoundError as exc:
            print(f"\n  ⚠️  Prompt template not found: {exc}")
            print("  Please ensure the prompts/ directory is intact.")
            return
        except RuntimeError as exc:
            print(f"\n  ⚠️  {exc}")
            return
        except Exception:
            logger.exception("Unexpected error generating question %s.", q_num)
            print("\n  ⚠️  Something went wrong. Please try again.")
            return

        asked_questions.append(question)
        print(f"  Q: {question}\n")

        # 2. Collect the candidate's answer
        print("  Your answer (press Enter twice to finish):")
        lines: list[str] = []
        while True:
            line = input("  > ")
            if line == "" and lines:
                break
            lines.append(line)
        answer = " ".join(lines).strip()

        if not answer:
            answer = "(no answer provided)"

        # 3. Evaluate the answer
        print("\n  Evaluating your answer …")
        try:
            eval_prompt = build_evaluation_prompt(topic, question, answer)
            feedback = clean_response(generate(model, eval_prompt))
        except FileNotFoundError as exc:
            print(f"\n  ⚠️  Prompt template not found: {exc}")
            print("  Please ensure the prompts/ directory is intact.")
            return
        except RuntimeError as exc:
            print(f"\n  ⚠️  {exc}")
            return
        except Exception:
            logger.exception("Unexpected error evaluating answer for Q%s.", q_num)
            print("\n  ⚠️  Something went wrong. Please try again.")
            return

        section("Feedback")
        print_feedback(feedback)

        results.append({"question": question, "answer": answer, "feedback": feedback})

    # 4. Final summary
    section("Final Session Summary")
    print("\n  Generating your overall summary …\n")
    try:
        summary_prompt = build_summary_prompt(topic, results)
        summary = clean_response(generate(model, summary_prompt))
    except FileNotFoundError as exc:
        print(f"\n  ⚠️  Prompt template not found: {exc}")
        print("  Please ensure the prompts/ directory is intact.")
        return
    except RuntimeError as exc:
        print(f"\n  ⚠️  {exc}")
        return
    except Exception:
        logger.exception("Unexpected error generating session summary.")
        print("\n  ⚠️  Something went wrong. Please try again.")
        return

    print(summary)

    try:
        saved_path = save_interview(topic, results, summary)
        print(f"\n  Session saved → {saved_path}")
    except OSError as exc:
        logger.exception("Could not save interview history.")
        print(f"\n  ⚠️  Could not save session history: {exc}")

    print()
    divider("═")
    print("  Session complete. Good luck with your interviews!")
    divider("═")


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    """Entry point: load env, prompt for topic, connect to WatsonX, run session."""
    load_dotenv()

    welcome()
    topic = choose_topic()

    print(f"\n  Topic selected: {topic}")
    print("  Connecting to IBM WatsonX …\n")
    try:
        model = build_client()
    except ValueError as exc:
        print(f"\n  ⚠️  Configuration error: {exc}")
        print("  Please set WATSONX_API_KEY, WATSONX_PROJECT_ID, and WATSONX_URL in your .env file.")
        sys.exit(1)
    except Exception:
        logger.exception("Unexpected error while connecting to WatsonX.")
        print("\n  ⚠️  Something went wrong while connecting. Please try again.")
        sys.exit(1)

    print("  Connected.\n")
    run_session(model, topic)


if __name__ == "__main__":
    main()
