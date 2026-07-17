"""Tiered benchmark prompts for quant-vs-quality study."""
EASY_PROMPTS = [
    "Write a Python function to calculate the factorial of a number.",
    "Write a Python function that checks if a string is a palindrome.",
    "Write a Python function that returns the sum of a list of numbers.",
    "Write a Python function that converts Celsius to Fahrenheit.",
    "Write a Python function that counts vowels in a string.",
    "Write a Python function to find the maximum of three numbers.",
    "Write a Python function that reverses a string.",
]

MEDIUM_PROMPTS = [
    "Write a Python function that merges two sorted lists into one sorted list.",
    "Write a Python class representing a BankAccount with deposit, withdraw, and balance methods.",
    "Write a Python function using a decorator that logs function arguments and return values.",
    "Write a Python context manager that measures execution time of a code block.",
    "Write a Python function that finds all prime numbers up to N using the Sieve of Eratosthenes.",
    "Write a Python function that serializes a dictionary to JSON and writes it to a file.",
    "Write a Python generator function that yields Fibonacci numbers indefinitely.",
]

HARD_PROMPTS = [
    "Write a Python function that implements a simple LRU cache with configurable capacity.",
    "Write a Python class that implements a thread-safe singleton pattern with lazy initialization.",
    "Write a Python function that parses a CSV string and returns a list of dicts with proper type inference.",
    "Write a Python function that builds a binary search tree with insert, search, and in-order traversal.",
    "Write a Python function that implements the Levenshtein distance algorithm between two strings.",
    "Write a Python function that performs topological sort on a directed acyclic graph represented as an adjacency dict.",
]

ALL_PROMPTS = {
    "easy": EASY_PROMPTS,
    "medium": MEDIUM_PROMPTS,
    "hard": HARD_PROMPTS,
}
