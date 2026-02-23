"""
Tool (function-calling) schema definitions for the coding interviewer.

These are passed to GeminiLiveLLMService so the LLM can call them during
the interview.
"""

from pipecat.adapters.schemas.tools_schema import ToolsSchema, FunctionSchema

TOOLS = ToolsSchema(
    standard_tools=[
        FunctionSchema(
            name="select_problem",
            description=(
                "Pick a coding problem for the candidate. Call this after "
                "introductions to present a problem. Returns the problem text "
                "and sends it to the candidate's screen."
            ),
            properties={
                "difficulty": {
                    "type": "string",
                    "enum": ["easy", "medium", "hard"],
                    "description": "Desired difficulty level.",
                },
            },
            required=["difficulty"],
        ),
        FunctionSchema(
            name="run_tests",
            description=(
                "Execute the candidate's code against the problem's test cases. "
                "Call this when the candidate says they're done or when you want "
                "to check if their solution works. Returns test results showing "
                "which test cases passed or failed."
            ),
            properties={},
            required=[],
        ),
        FunctionSchema(
            name="start_timer",
            description=(
                "Start a countdown timer visible to the candidate. Call this "
                "right after presenting the problem."
            ),
            properties={
                "minutes": {
                    "type": "integer",
                    "description": "Timer duration in minutes (e.g. 15, 20, 25).",
                },
            },
            required=["minutes"],
        ),
        FunctionSchema(
            name="give_hint",
            description=(
                "Give the candidate a hint for the current problem. Use this "
                "when the candidate is stuck. Hints are numbered starting at 1."
            ),
            properties={
                "hint_number": {
                    "type": "integer",
                    "description": "Which hint to reveal (1, 2, 3, ...).",
                },
            },
            required=["hint_number"],
        ),
        FunctionSchema(
            name="end_interview",
            description=(
                "End the interview and provide feedback. Call this when the "
                "candidate has finished or time is up."
            ),
            properties={
                "feedback": {
                    "type": "string",
                    "description": "Constructive feedback summarising strengths and areas to improve.",
                },
                "score": {
                    "type": "string",
                    "enum": ["strong_hire", "hire", "lean_hire", "lean_no_hire", "no_hire"],
                    "description": "Overall assessment.",
                },
            },
            required=["feedback", "score"],
        ),
        FunctionSchema(
            name="review_code",
            description=(
                "Read the candidate's current code from the editor. Call this "
                "when you want to see what they have written so far in order "
                "to evaluate correctness, style, or give feedback."
            ),
            properties={
                "focus": {
                    "type": "string",
                    "description": (
                        "Optional aspect to focus on when reviewing, e.g. "
                        "'correctness', 'edge cases', 'time complexity', 'style'."
                    ),
                },
            },
            required=["focus"],
        ),
    ]
)
