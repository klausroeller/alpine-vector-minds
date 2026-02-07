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

EVALUATE_TIMEOUT_SECONDS = 1800  # 30 minutes — 1,000 LLM calls


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


def run_evaluation(client: httpx.Client, base_url: str, token: str) -> dict:
    """Call the evaluation endpoint and return the JSON response."""
    resp = client.get(
        f"{base_url}/api/v1/copilot/evaluate",
        headers={"Authorization": f"Bearer {token}"},
        timeout=EVALUATE_TIMEOUT_SECONDS,
    )
    if resp.status_code != 200:
        print(f"ERROR: Evaluation failed ({resp.status_code}): {resp.text}")
        sys.exit(1)
    return resp.json()


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
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    base_url = resolve_base_url(args)
    email, password = resolve_credentials(args)

    print(f"Evaluating {args.env} at {base_url}")

    with httpx.Client() as client:
        print("Authenticating...")
        token = authenticate(client, base_url, email, password)

        print("Running evaluation (this may take a while)...")
        data = run_evaluation(client, base_url, token)

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
