"""
Function-call handlers for the coding interviewer tools.

Each handler is a factory that returns an async handler function, accepting
the webrtc_connection and session dict via closure. This keeps main.py clean
and makes the handlers independently testable.
"""

from __future__ import annotations

import random
import logging
from typing import Any

from problems import PROBLEMS, get_problems_by_difficulty
from code_runner import run_tests as execute_tests

logger = logging.getLogger("voice-poc")


def make_select_problem_handler(webrtc_connection, session: dict):
    """Return a handler that picks a problem and pushes it to the browser."""

    async def handle(params):
        difficulty = params.arguments.get("difficulty", "easy")
        candidates = get_problems_by_difficulty(difficulty)
        if not candidates:
            candidates = PROBLEMS  # fallback to all

        problem = random.choice(candidates)
        session["current_problem"] = problem
        session["hints_given"] = 0

        webrtc_connection.send_app_message({
            "type": "problem",
            "id": problem["id"],
            "title": problem["title"],
            "difficulty": problem["difficulty"],
            "description": problem["description"],
            "examples": problem["examples"],
            "starter_code": problem.get("starter_code", {}),
        })

        problem_text = (
            f"Problem: {problem['title']} ({problem['difficulty']})\n\n"
            f"{problem['description']}\n\n"
            f"Examples:\n" + "\n".join(problem["examples"])
        )
        await params.result_callback({"status": "ok", "problem": problem_text})

    return handle


def make_start_timer_handler(webrtc_connection, session: dict):
    """Return a handler that starts a countdown timer on the frontend."""

    async def handle(params):
        minutes = params.arguments.get("minutes", 20)
        webrtc_connection.send_app_message({
            "type": "timer",
            "minutes": minutes,
        })
        await params.result_callback({
            "status": "ok",
            "message": f"Timer started for {minutes} minutes.",
        })

    return handle


def make_give_hint_handler(webrtc_connection, session: dict):
    """Return a handler that reveals a hint to the candidate."""

    async def handle(params):
        hint_number = params.arguments.get("hint_number", 1)
        problem = session.get("current_problem")

        if not problem:
            await params.result_callback({
                "status": "error",
                "message": "No problem selected yet.",
            })
            return

        hints = problem.get("hints", [])
        idx = hint_number - 1  # 1-indexed → 0-indexed

        if idx < 0 or idx >= len(hints):
            await params.result_callback({
                "status": "error",
                "message": f"Hint {hint_number} does not exist. Available: 1-{len(hints)}.",
            })
            return

        hint_text = hints[idx]
        session["hints_given"] = max(session["hints_given"], hint_number)

        webrtc_connection.send_app_message({
            "type": "hint",
            "hint_number": hint_number,
            "text": hint_text,
        })

        await params.result_callback({
            "status": "ok",
            "hint_number": hint_number,
            "hint_text": hint_text,
        })

    return handle


def make_end_interview_handler(webrtc_connection, session: dict):
    """Return a handler that ends the interview and sends feedback."""

    async def handle(params):
        feedback = params.arguments.get("feedback", "")
        score = params.arguments.get("score", "")

        webrtc_connection.send_app_message({
            "type": "end",
            "feedback": feedback,
            "score": score,
        })

        await params.result_callback({
            "status": "ok",
            "message": "Interview ended. Feedback sent to candidate.",
        })

    return handle


def make_review_code_handler(code_store: dict, pc_id: str):
    """Return a handler that reads the candidate's latest code from the store."""

    async def handle(params):
        code = code_store.get(pc_id, "")
        if not code:
            await params.result_callback({
                "status": "ok",
                "code": "No code submitted yet.",
            })
        else:
            await params.result_callback({
                "status": "ok",
                "code": code,
            })

    return handle


def make_run_tests_handler(webrtc_connection, session: dict, code_store: dict, pc_id: str, language_store: dict):
    """Return a handler that executes code against test cases."""

    async def handle(params):
        problem = session.get("current_problem")

        if not problem:
            await params.result_callback({
                "status": "error",
                "message": "No problem selected yet. Please select a problem first.",
            })
            return

        code = code_store.get(pc_id, "")
        if not code or not code.strip():
            await params.result_callback({
                "status": "error",
                "message": "No code submitted yet. The candidate needs to write some code first.",
            })
            return

        test_cases = problem.get("test_cases")
        if not test_cases:
            await params.result_callback({
                "status": "error",
                "message": "No test cases available for this problem.",
            })
            return

        # Get language from language store (default to python)
        language = language_store.get(pc_id, "python")

        logger.info(f"Running tests for problem {problem['id']} with {len(test_cases)} test cases")

        # Execute tests
        result = await execute_tests(code, language, test_cases, timeout_per_test=5)

        # Send results to frontend
        webrtc_connection.send_app_message({
            "type": "test_results",
            "success": result.success,
            "total": result.total_tests,
            "passed": result.passed_tests,
            "failed": result.failed_tests,
            "results": [
                {
                    "passed": tr.passed,
                    "input": tr.input,
                    "expected": tr.expected,
                    "actual": tr.actual,
                    "error": tr.error,
                    "execution_time_ms": tr.execution_time_ms,
                }
                for tr in result.test_results
            ],
        })

        # Return summary to LLM
        if result.success:
            summary = f"All {result.total_tests} test cases passed! The solution is correct."
        else:
            summary = (
                f"{result.passed_tests}/{result.total_tests} test cases passed. "
                f"{result.failed_tests} failed. "
            )
            # Add details about first failure
            first_failure = next((tr for tr in result.test_results if not tr.passed), None)
            if first_failure:
                summary += (
                    f"First failure: Input {first_failure.input} "
                    f"expected {first_failure.expected} but got {first_failure.actual}. "
                )
                if first_failure.error:
                    summary += f"Error: {first_failure.error}"

        await params.result_callback({
            "status": "ok",
            "success": result.success,
            "total_tests": result.total_tests,
            "passed_tests": result.passed_tests,
            "failed_tests": result.failed_tests,
            "summary": summary,
        })

    return handle


def register_all_handlers(
    llm, webrtc_connection, session: dict,
    code_store: dict | None = None, pc_id: str | None = None,
    language_store: dict | None = None,
) -> None:
    """Register every tool handler on the LLM service."""
    llm.register_function(
        "select_problem",
        make_select_problem_handler(webrtc_connection, session),
    )
    llm.register_function(
        "start_timer",
        make_start_timer_handler(webrtc_connection, session),
    )
    llm.register_function(
        "give_hint",
        make_give_hint_handler(webrtc_connection, session),
    )
    llm.register_function(
        "end_interview",
        make_end_interview_handler(webrtc_connection, session),
    )
    if code_store is not None and pc_id is not None:
        llm.register_function(
            "review_code",
            make_review_code_handler(code_store, pc_id),
        )
        if language_store is not None:
            llm.register_function(
                "run_tests",
                make_run_tests_handler(webrtc_connection, session, code_store, pc_id, language_store),
            )
