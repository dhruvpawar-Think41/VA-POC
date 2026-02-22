"""
Problem bank for the coding interview assistant.

Each problem is a dict with:
  id, title, difficulty, description, examples, hints, follow_up
"""

PROBLEMS = [
    {
        "id": "two-sum",
        "title": "Two Sum",
        "difficulty": "easy",
        "description": (
            "Given an array of integers nums and an integer target, return the "
            "indices of the two numbers that add up to target.\n\n"
            "You may assume that each input has exactly one solution, and you "
            "may not use the same element twice."
        ),
        "examples": [
            "Input: nums = [2, 7, 11, 15], target = 9\nOutput: [0, 1]\nExplanation: nums[0] + nums[1] = 2 + 7 = 9",
            "Input: nums = [3, 2, 4], target = 6\nOutput: [1, 2]",
        ],
        "hints": [
            "Think about what value you need to find for each element to reach the target.",
            "A hash map can store values you've already seen and let you look them up in O(1).",
            "For each number, check if (target - number) exists in your hash map before inserting the current number.",
        ],
        "follow_up": "Can you solve it in one pass through the array?",
    },
    {
        "id": "valid-anagram",
        "title": "Valid Anagram",
        "difficulty": "easy",
        "description": (
            "Given two strings s and t, return true if t is an anagram of s, "
            "and false otherwise.\n\n"
            "An anagram is a word formed by rearranging the letters of another "
            "word, using all the original letters exactly once."
        ),
        "examples": [
            "Input: s = \"anagram\", t = \"nagaram\"\nOutput: true",
            "Input: s = \"rat\", t = \"car\"\nOutput: false",
        ],
        "hints": [
            "What property must two strings share if one is an anagram of the other?",
            "Try counting the frequency of each character in both strings.",
            "You can use a single hash map: increment for s, decrement for t, then check all counts are zero.",
        ],
        "follow_up": "What if the inputs contain Unicode characters? How does that affect your approach?",
    },
    {
        "id": "max-subarray",
        "title": "Maximum Subarray",
        "difficulty": "medium",
        "description": (
            "Given an integer array nums, find the subarray with the largest "
            "sum, and return its sum.\n\n"
            "A subarray is a contiguous non-empty sequence of elements within "
            "the array."
        ),
        "examples": [
            "Input: nums = [-2, 1, -3, 4, -1, 2, 1, -5, 4]\nOutput: 6\nExplanation: The subarray [4, -1, 2, 1] has the largest sum 6.",
            "Input: nums = [5, 4, -1, 7, 8]\nOutput: 23",
        ],
        "hints": [
            "Think about whether extending the current subarray is better than starting a new one at each position.",
            "This is a classic dynamic programming problem known as Kadane's algorithm.",
            "Keep track of the current sum. If it drops below zero, reset it. Track the maximum sum seen so far.",
        ],
        "follow_up": "Can you also return the start and end indices of the maximum subarray?",
    },
    {
        "id": "invert-binary-tree",
        "title": "Invert Binary Tree",
        "difficulty": "easy",
        "description": (
            "Given the root of a binary tree, invert the tree and return its "
            "root.\n\n"
            "Inverting a binary tree means swapping every left child with its "
            "corresponding right child, for all nodes in the tree."
        ),
        "examples": [
            "Input: root = [4, 2, 7, 1, 3, 6, 9]\nOutput: [4, 7, 2, 9, 6, 3, 1]",
            "Input: root = [2, 1, 3]\nOutput: [2, 3, 1]",
        ],
        "hints": [
            "Start from the root and think recursively. What's the base case?",
            "For each node, you need to swap its left and right children, then do the same for each child.",
            "You can also solve this iteratively using a queue (BFS) or a stack (DFS).",
        ],
        "follow_up": "Solve it both recursively and iteratively. What are the trade-offs?",
    },
    {
        "id": "climbing-stairs",
        "title": "Climbing Stairs",
        "difficulty": "easy",
        "description": (
            "You are climbing a staircase. It takes n steps to reach the top.\n\n"
            "Each time you can either climb 1 or 2 steps. In how many distinct "
            "ways can you climb to the top?"
        ),
        "examples": [
            "Input: n = 2\nOutput: 2\nExplanation: 1+1 or 2. Two ways.",
            "Input: n = 3\nOutput: 3\nExplanation: 1+1+1, 1+2, or 2+1. Three ways.",
        ],
        "hints": [
            "Think about how you could reach step n. You either came from step n-1 or step n-2.",
            "This is a Fibonacci-like recurrence: ways(n) = ways(n-1) + ways(n-2).",
            "You can optimize space by only keeping track of the last two values instead of a full array.",
        ],
        "follow_up": "What if you could climb 1, 2, or 3 steps at a time?",
    },
]


def get_problems_by_difficulty(difficulty: str) -> list[dict]:
    """Return problems matching the given difficulty (easy/medium/hard)."""
    return [p for p in PROBLEMS if p["difficulty"] == difficulty.lower()]


def get_problem_by_id(problem_id: str) -> dict | None:
    """Return a single problem by its id, or None."""
    for p in PROBLEMS:
        if p["id"] == problem_id:
            return p
    return None
