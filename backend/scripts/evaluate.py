"""Run copilot evaluation and save reports to data/evaluation-reports/."""

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "evaluation-reports"

DEV_BASE_URL = "http://localhost:8000"
PROD_BASE_URL = "https://alpine-vector-minds.de"

DEV_EMAIL = "dev@example.com"
DEV_PASSWORD = "dev"

PER_QUESTION_TIMEOUT_SECONDS = 120


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run copilot evaluation")
    parser.add_argument(
        "--env",
        choices=["dev", "prod"],
        default="dev",
        help="Target environment (default: dev)",
    )
    parser.add_argument("--base-url", help="Override the base URL")
    parser.add_argument("--email", help="Login email")
    parser.add_argument("--password", help="Login password")
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of questions to evaluate (default: 100)",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="0-based question index to start evaluation from (default: 0)",
    )
    return parser.parse_args()


def resolve_base_url(args: argparse.Namespace) -> str:
    if args.base_url:
        return args.base_url.rstrip("/")
    return DEV_BASE_URL if args.env == "dev" else PROD_BASE_URL


def resolve_credentials(args: argparse.Namespace) -> tuple[str, str]:
    email = args.email or os.environ.get("DEFAULT_USER_EMAIL")
    password = args.password or os.environ.get("DEFAULT_USER_PASSWORD")

    if email and password:
        return email, password

    if args.env == "dev":
        return email or DEV_EMAIL, password or DEV_PASSWORD

    print("ERROR: Credentials required for prod. Use --email/--password or env vars.")
    sys.exit(1)


def authenticate(client: httpx.Client, base_url: str, email: str, password: str) -> str:
    """Authenticate and return the access token."""
    resp = client.post(
        f"{base_url}/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    if resp.status_code != 200:
        print(f"ERROR: Authentication failed ({resp.status_code}): {resp.text}")
        sys.exit(1)
    return resp.json()["access_token"]


def print_progress(index: int, total: int) -> None:
    """Print an in-place progress bar."""
    bar_width = 30
    filled = int(bar_width * index / total) if total > 0 else 0
    bar = "\u2588" * filled + "\u2591" * (bar_width - filled)
    pct = index / total * 100 if total > 0 else 0
    sys.stdout.write(f"\rEvaluating: [{bar}] {index}/{total} ({pct:.1f}%)")
    sys.stdout.flush()


def run_evaluation(
    client: httpx.Client, base_url: str, token: str, limit: int, start: int = 0
) -> list[dict]:
    """Call the per-question evaluation endpoint in a loop, returning all step results."""
    headers = {"Authorization": f"Bearer {token}"}
    results = []
    index = start
    end = start + limit

    while index < end:
        resp = client.get(
            f"{base_url}/api/v1/copilot/evaluate",
            params={"index": index},
            headers=headers,
            timeout=PER_QUESTION_TIMEOUT_SECONDS,
        )
        if resp.status_code != 200:
            print(f"\nERROR: Evaluation failed ({resp.status_code}): {resp.text}")
            sys.exit(1)

        step = resp.json()

        if step.get("done"):
            total = step["total"]
            evaluated = min(total, end) - start
            print_progress(evaluated, evaluated)
            break

        results.append(step)
        print_progress(index - start + 1, min(step["total"] - start, limit))
        index += 1

    print()  # newline after progress bar
    return results


def aggregate_results(steps: list[dict]) -> dict:
    """Aggregate per-question results into the final evaluation report."""
    total = len(steps)
    correct_classifications = 0
    hit_at_1 = 0
    hit_at_3 = 0
    hit_at_5 = 0
    questions_with_targets = 0
    errors = 0

    type_stats: dict[str, dict] = {}
    difficulty_stats: dict[str, dict] = {}

    for s in steps:
        if s.get("error"):
            errors += 1
            continue

        answer_type = s.get("answer_type") or "UNKNOWN"
        difficulty = s.get("difficulty") or "UNKNOWN"

        if answer_type not in type_stats:
            type_stats[answer_type] = {"count": 0, "hit_at_1": 0, "hit_at_3": 0}
        type_stats[answer_type]["count"] += 1

        if difficulty not in difficulty_stats:
            difficulty_stats[difficulty] = {
                "count": 0,
                "hit_at_1": 0,
                "hit_at_3": 0,
                "classification_correct": 0,
            }
        difficulty_stats[difficulty]["count"] += 1

        if s.get("classification_correct"):
            correct_classifications += 1
            difficulty_stats[difficulty]["classification_correct"] += 1

        if s.get("target_id"):
            questions_with_targets += 1
            if s.get("hit_at_1"):
                hit_at_1 += 1
                hit_at_3 += 1
                hit_at_5 += 1
                type_stats[answer_type]["hit_at_1"] += 1
                type_stats[answer_type]["hit_at_3"] += 1
                difficulty_stats[difficulty]["hit_at_1"] += 1
                difficulty_stats[difficulty]["hit_at_3"] += 1
            elif s.get("hit_at_3"):
                hit_at_3 += 1
                hit_at_5 += 1
                type_stats[answer_type]["hit_at_3"] += 1
                difficulty_stats[difficulty]["hit_at_3"] += 1
            elif s.get("hit_at_5"):
                hit_at_5 += 1

    non_error = total - errors
    by_answer_type = {}
    for at, stats in type_stats.items():
        count = stats["count"]
        by_answer_type[at] = {
            "count": count,
            "hit_at_1": stats["hit_at_1"] / count if count > 0 else 0.0,
            "hit_at_3": stats["hit_at_3"] / count if count > 0 else 0.0,
        }

    by_difficulty = {}
    for diff, stats in difficulty_stats.items():
        count = stats["count"]
        by_difficulty[diff] = {
            "count": count,
            "classification_correct": stats["classification_correct"] / count if count > 0 else 0.0,
            "hit_at_1": stats["hit_at_1"] / count if count > 0 else 0.0,
            "hit_at_3": stats["hit_at_3"] / count if count > 0 else 0.0,
        }

    return {
        "total_questions": total,
        "classification_accuracy": correct_classifications / non_error if non_error > 0 else 0.0,
        "retrieval_accuracy": {
            "hit_at_1": hit_at_1 / questions_with_targets if questions_with_targets > 0 else 0.0,
            "hit_at_3": hit_at_3 / questions_with_targets if questions_with_targets > 0 else 0.0,
            "hit_at_5": hit_at_5 / questions_with_targets if questions_with_targets > 0 else 0.0,
        },
        "by_answer_type": by_answer_type,
        "by_difficulty": by_difficulty,
        "errors": errors,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def generate_markdown(data: dict, env: str, base_url: str) -> str:
    ra = data["retrieval_accuracy"]
    lines = [
        f"# Evaluation Report — {env}",
        "",
        f"**Date**: {data['evaluated_at']}",
        f"**Target**: {base_url}",
        f"**Total questions**: {data['total_questions']}",
        "",
        "## Overall Accuracy",
        "",
        "| Metric                  | Score  |",
        "|-------------------------|--------|",
        f"| Classification Accuracy | {pct(data['classification_accuracy'])} |",
        f"| Retrieval Hit@1         | {pct(ra['hit_at_1'])} |",
        f"| Retrieval Hit@3         | {pct(ra['hit_at_3'])} |",
        f"| Retrieval Hit@5         | {pct(ra['hit_at_5'])} |",
        "",
        "## By Answer Type",
        "",
        "| Type               | Count | Hit@1 | Hit@3 |",
        "|--------------------|-------|-------|-------|",
    ]
    for answer_type, stats in sorted(data.get("by_answer_type", {}).items()):
        lines.append(
            f"| {answer_type:<18} | {stats['count']:>5} | {pct(stats['hit_at_1']):>5} | {pct(stats['hit_at_3']):>5} |"
        )
    lines.append("")

    lines.extend([
        "## By Difficulty",
        "",
        "| Difficulty         | Count | Classification | Hit@1 | Hit@3 |",
        "|--------------------|-------|----------------|-------|-------|",
    ])
    for difficulty, stats in sorted(data.get("by_difficulty", {}).items()):
        lines.append(
            f"| {difficulty:<18} | {stats['count']:>5} | {pct(stats['classification_correct']):>14} | {pct(stats['hit_at_1']):>5} | {pct(stats['hit_at_3']):>5} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    base_url = resolve_base_url(args)
    email, password = resolve_credentials(args)

    print(f"Evaluating {args.env} at {base_url} (start: {args.start}, limit: {args.limit})")

    with httpx.Client() as client:
        print("Authenticating...")
        token = authenticate(client, base_url, email, password)

        steps = run_evaluation(client, base_url, token, args.limit, start=args.start)

    if not steps:
        print("No questions evaluated.")
        return

    data = aggregate_results(steps)

    # Save reports
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d-%H-%M")
    stem = f"eval-{args.env}-{timestamp}"

    json_path = REPORTS_DIR / f"{stem}.json"
    json_path.write_text(json.dumps(data, indent=2))
    print(f"JSON report saved to {json_path}")

    md_path = REPORTS_DIR / f"{stem}.md"
    md_content = generate_markdown(data, args.env, base_url)
    md_path.write_text(md_content)
    print(f"Markdown report saved to {md_path}")

    # Print summary
    print()
    print(md_content)


if __name__ == "__main__":
    main()
