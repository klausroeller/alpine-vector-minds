"""Run copilot evaluation and save reports to data/evaluation-reports/."""

import argparse
import asyncio
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
MAX_CONCURRENT_REQUESTS = 5


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


async def authenticate(client: httpx.AsyncClient, base_url: str, email: str, password: str) -> str:
    """Authenticate and return the access token."""
    resp = await client.post(
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


async def _fetch_one(client: httpx.AsyncClient, base_url: str, headers: dict, index: int) -> dict:
    """Fetch a single evaluation step."""
    resp = await client.get(
        f"{base_url}/api/v1/copilot/evaluate",
        params={"index": index},
        headers=headers,
        timeout=PER_QUESTION_TIMEOUT_SECONDS,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Evaluation failed ({resp.status_code}): {resp.text}")
    return resp.json()


async def run_evaluation(
    client: httpx.AsyncClient, base_url: str, token: str, limit: int, start: int = 0
) -> list[dict]:
    """Call the per-question evaluation endpoint in concurrent batches."""
    headers = {"Authorization": f"Bearer {token}"}
    results: list[dict] = []
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    # Build list of indices to evaluate
    indices = list(range(start, start + limit))
    total_to_eval = len(indices)
    batch_size = max(1, total_to_eval // 10)

    async def _limited_fetch(idx: int) -> dict:
        async with semaphore:
            return await _fetch_one(client, base_url, headers, idx)

    for batch_start in range(0, total_to_eval, batch_size):
        batch_indices = indices[batch_start : batch_start + batch_size]
        tasks = [_limited_fetch(idx) for idx in batch_indices]
        try:
            batch_results = await asyncio.gather(*tasks)
        except RuntimeError as exc:
            print(f"\n{exc}")
            sys.exit(1)

        for step in batch_results:
            if step.get("done"):
                # Server says no more questions — stop collecting
                evaluated = len(results)
                print_progress(evaluated, evaluated)
                print()
                return results
            results.append(step)

        print_progress(len(results), total_to_eval)

    print()  # newline after progress bar
    return results


def aggregate_results(steps: list[dict]) -> dict:
    """Aggregate per-question results into the final evaluation report."""
    total = len(steps)
    correct_classifications = 0
    hit_at_1 = 0
    hit_at_5 = 0
    hit_at_10 = 0
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
            type_stats[answer_type] = {"count": 0, "hit_at_1": 0, "hit_at_5": 0}
        type_stats[answer_type]["count"] += 1

        if difficulty not in difficulty_stats:
            difficulty_stats[difficulty] = {
                "count": 0,
                "hit_at_1": 0,
                "hit_at_5": 0,
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
                hit_at_5 += 1
                hit_at_10 += 1
                type_stats[answer_type]["hit_at_1"] += 1
                type_stats[answer_type]["hit_at_5"] += 1
                difficulty_stats[difficulty]["hit_at_1"] += 1
                difficulty_stats[difficulty]["hit_at_5"] += 1
            elif s.get("hit_at_5"):
                hit_at_5 += 1
                hit_at_10 += 1
                type_stats[answer_type]["hit_at_5"] += 1
                difficulty_stats[difficulty]["hit_at_5"] += 1
            elif s.get("hit_at_10"):
                hit_at_10 += 1

    non_error = total - errors
    by_answer_type = {}
    for at, stats in type_stats.items():
        count = stats["count"]
        by_answer_type[at] = {
            "count": count,
            "hit_at_1": stats["hit_at_1"] / count if count > 0 else 0.0,
            "hit_at_5": stats["hit_at_5"] / count if count > 0 else 0.0,
        }

    by_difficulty = {}
    for diff, stats in difficulty_stats.items():
        count = stats["count"]
        by_difficulty[diff] = {
            "count": count,
            "classification_correct": stats["classification_correct"] / count if count > 0 else 0.0,
            "hit_at_1": stats["hit_at_1"] / count if count > 0 else 0.0,
            "hit_at_5": stats["hit_at_5"] / count if count > 0 else 0.0,
        }

    return {
        "total_questions": total,
        "classification_accuracy": correct_classifications / non_error if non_error > 0 else 0.0,
        "retrieval_accuracy": {
            "hit_at_1": hit_at_1 / questions_with_targets if questions_with_targets > 0 else 0.0,
            "hit_at_5": hit_at_5 / questions_with_targets if questions_with_targets > 0 else 0.0,
            "hit_at_10": hit_at_10 / questions_with_targets if questions_with_targets > 0 else 0.0,
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
        f"| Retrieval Hit@5         | {pct(ra['hit_at_5'])} |",
        f"| Retrieval Hit@10        | {pct(ra['hit_at_10'])} |",
        "",
        "## By Answer Type",
        "",
        "| Type               | Count | Hit@1 | Hit@5 |",
        "|--------------------|-------|-------|-------|",
    ]
    for answer_type, stats in sorted(data.get("by_answer_type", {}).items()):
        lines.append(
            f"| {answer_type:<18} | {stats['count']:>5} | {pct(stats['hit_at_1']):>5} | {pct(stats['hit_at_5']):>5} |"
        )
    lines.append("")

    lines.extend(
        [
            "## By Difficulty",
            "",
            "| Difficulty         | Count | Classification | Hit@1 | Hit@5 |",
            "|--------------------|-------|----------------|-------|-------|",
        ]
    )
    for difficulty, stats in sorted(data.get("by_difficulty", {}).items()):
        lines.append(
            f"| {difficulty:<18} | {stats['count']:>5} | {pct(stats['classification_correct']):>14} | {pct(stats['hit_at_1']):>5} | {pct(stats['hit_at_5']):>5} |"
        )
    lines.append("")
    return "\n".join(lines)


async def async_main() -> None:
    args = parse_args()
    base_url = resolve_base_url(args)
    email, password = resolve_credentials(args)

    print(f"Evaluating {args.env} at {base_url} (start: {args.start}, limit: {args.limit})")

    async with httpx.AsyncClient() as client:
        print("Authenticating...")
        token = await authenticate(client, base_url, email, password)

        steps = await run_evaluation(client, base_url, token, args.limit, start=args.start)

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

    # Store results in database (best-effort)
    try:
        ra = data["retrieval_accuracy"]
        payload = {
            "total_questions": data["total_questions"],
            "classification_accuracy": data["classification_accuracy"],
            "hit_at_1": ra["hit_at_1"],
            "hit_at_5": ra["hit_at_5"],
            "hit_at_10": ra["hit_at_10"],
            "by_answer_type": data.get("by_answer_type"),
            "by_difficulty": data.get("by_difficulty"),
            "errors": data.get("errors", 0),
            "evaluated_at": data["evaluated_at"],
        }
        async with httpx.AsyncClient() as post_client:
            post_token = await authenticate(post_client, base_url, email, password)
            resp = await post_client.post(
                f"{base_url}/api/v1/evaluation/results",
                json=payload,
                headers={"Authorization": f"Bearer {post_token}"},
                timeout=30,
            )
            if resp.status_code == 200:
                print("Evaluation results stored in database.")
            else:
                print(f"Warning: Failed to store results ({resp.status_code})")
    except Exception as exc:
        print(f"Warning: Could not store evaluation results: {exc}")

    # Print summary
    print()
    print(md_content)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
