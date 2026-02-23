"""
Code execution service with sandboxed Docker containers.

Runs candidate code against test cases with security restrictions.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from dataclasses import dataclass

logger = logging.getLogger("voice-poc")


@dataclass
class TestResult:
    """Result of running a single test case."""
    passed: bool
    input: dict
    expected: Any
    actual: Any | None
    error: str | None = None
    execution_time_ms: float | None = None


@dataclass
class ExecutionResult:
    """Overall execution result for all test cases."""
    success: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    test_results: list[TestResult]
    error: str | None = None


# Language runtime configurations
LANGUAGE_CONFIGS = {
    "python": {
        "image": "python:3.11-slim",
        "file_ext": "py",
        "wrapper_template": """
import json
import sys

# User's code
{code}

# Test runner
if __name__ == "__main__":
    test_input = json.loads(sys.argv[1])
    try:
        result = {function_name}(**test_input)
        print(json.dumps({{"result": result, "error": None}}))
    except Exception as e:
        print(json.dumps({{"result": None, "error": str(e)}}))
""",
    },
    "javascript": {
        "image": "node:18-slim",
        "file_ext": "js",
        "wrapper_template": """
const fs = require('fs');
const stdin = fs.readFileSync(0, 'utf-8');

// User's code
{code}

// Test runner
try {{
    const testInput = JSON.parse(stdin);
    const result = {function_name}(...Object.values(testInput));
    console.log(JSON.stringify({{result: result, error: null}}));
}} catch (e) {{
    console.log(JSON.stringify({{result: null, error: e.message}}));
}}
""",
    },
}


def extract_function_name(code: str, language: str) -> str:
    """Extract the main function name from code."""
    if language == "python":
        # Look for "def function_name("
        for line in code.split('\n'):
            line = line.strip()
            if line.startswith('def ') and '(' in line:
                func_name = line.split('def ')[1].split('(')[0].strip()
                return func_name
    elif language == "javascript":
        # Look for "function functionName(" or "const functionName ="
        for line in code.split('\n'):
            line = line.strip()
            if line.startswith('function ') and '(' in line:
                func_name = line.split('function ')[1].split('(')[0].strip()
                return func_name
            if 'const ' in line and '=' in line and '=>' in line:
                func_name = line.split('const ')[1].split('=')[0].strip()
                return func_name

    return "solution"  # Default fallback


async def run_code_in_docker(
    code: str,
    language: str,
    test_case: dict,
    timeout_seconds: int = 5
) -> TestResult:
    """
    Run code for a single test case in a Docker container.

    Uses subprocess instead of docker-py for simpler deployment.
    """
    import time

    config = LANGUAGE_CONFIGS.get(language)
    if not config:
        return TestResult(
            passed=False,
            input=test_case["input"],
            expected=test_case["expected"],
            actual=None,
            error=f"Unsupported language: {language}",
        )

    # Extract function name
    function_name = extract_function_name(code, language)

    # Wrap code with test harness
    wrapped_code = config["wrapper_template"].format(
        code=code,
        function_name=function_name
    )

    # Prepare Docker command
    test_input_json = json.dumps(test_case["input"])

    start_time = time.time()

    try:
        if language == "python":
            # Run Python code
            proc = await asyncio.create_subprocess_exec(
                "docker", "run", "--rm",
                "--network", "none",  # No network access
                "--memory", "128m",   # 128MB RAM limit
                "--cpus", "0.5",      # 50% CPU limit
                "--pids-limit", "50", # Limit processes
                "-i",                 # Interactive (for stdin)
                config["image"],
                "python", "-c", wrapped_code, test_input_json,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        elif language == "javascript":
            # Run JavaScript code (send test input via stdin)
            proc = await asyncio.create_subprocess_exec(
                "docker", "run", "--rm",
                "--network", "none",
                "--memory", "128m",
                "--cpus", "0.5",
                "--pids-limit", "50",
                "-i",
                config["image"],
                "node", "-e", wrapped_code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
            )
            # Send test input via stdin
            proc.stdin.write(test_input_json.encode('utf-8'))
            proc.stdin.close()
        else:
            raise ValueError(f"Unsupported language: {language}")

        # Wait with timeout
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            execution_time = (time.time() - start_time) * 1000
            return TestResult(
                passed=False,
                input=test_case["input"],
                expected=test_case["expected"],
                actual=None,
                error=f"Timeout after {timeout_seconds}s",
                execution_time_ms=execution_time,
            )

        execution_time = (time.time() - start_time) * 1000

        # Parse output
        output = stdout.decode('utf-8').strip()
        error_output = stderr.decode('utf-8').strip()

        if proc.returncode != 0:
            return TestResult(
                passed=False,
                input=test_case["input"],
                expected=test_case["expected"],
                actual=None,
                error=error_output or "Runtime error",
                execution_time_ms=execution_time,
            )

        # Parse JSON result
        try:
            result_data = json.loads(output)
            actual_result = result_data.get("result")
            error_msg = result_data.get("error")

            if error_msg:
                return TestResult(
                    passed=False,
                    input=test_case["input"],
                    expected=test_case["expected"],
                    actual=None,
                    error=error_msg,
                    execution_time_ms=execution_time,
                )

            # Compare result
            passed = actual_result == test_case["expected"]

            return TestResult(
                passed=passed,
                input=test_case["input"],
                expected=test_case["expected"],
                actual=actual_result,
                execution_time_ms=execution_time,
            )

        except json.JSONDecodeError:
            return TestResult(
                passed=False,
                input=test_case["input"],
                expected=test_case["expected"],
                actual=None,
                error=f"Invalid output: {output}",
                execution_time_ms=execution_time,
            )

    except Exception as e:
        logger.exception("Code execution failed")
        return TestResult(
            passed=False,
            input=test_case["input"],
            expected=test_case["expected"],
            actual=None,
            error=str(e),
        )


async def run_tests(
    code: str,
    language: str,
    test_cases: list[dict],
    timeout_per_test: int = 5
) -> ExecutionResult:
    """
    Run all test cases for the given code.

    Args:
        code: The candidate's code
        language: Programming language (python, javascript)
        test_cases: List of test cases with input/expected
        timeout_per_test: Timeout in seconds per test

    Returns:
        ExecutionResult with detailed test results
    """
    if not code or not code.strip():
        return ExecutionResult(
            success=False,
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            test_results=[],
            error="No code provided",
        )

    if language not in LANGUAGE_CONFIGS:
        return ExecutionResult(
            success=False,
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            test_results=[],
            error=f"Unsupported language: {language}. Supported: {list(LANGUAGE_CONFIGS.keys())}",
        )

    logger.info(f"Running {len(test_cases)} test cases for {language} code")

    # Run all test cases
    results = []
    for test_case in test_cases:
        result = await run_code_in_docker(code, language, test_case, timeout_per_test)
        results.append(result)
        logger.info(f"Test {'PASSED' if result.passed else 'FAILED'}: {result.input} -> {result.actual} (expected {result.expected})")

    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count

    return ExecutionResult(
        success=passed_count == len(results),
        total_tests=len(results),
        passed_tests=passed_count,
        failed_tests=failed_count,
        test_results=results,
    )
