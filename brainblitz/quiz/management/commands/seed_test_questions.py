"""
Load 10 approved questions per category (Python, DSA) with 4 choices each,
and two seed quizzes for local testing.

Usage:
  python manage.py seed_test_questions
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from quiz.models import Category, Choice, Question, Quiz, QuizQuestion


def _q(text, options, correct_index: int):
    """options: list of 4 strings, correct_index 0-3"""
    return {"text": text, "options": options, "correct": correct_index}


PYTHON_DATA = [
    _q(
        "What does the len() function return for a non-empty list?",
        ["The sum of elements", "The number of items", "The last index", "The first element"],
        1,
    ),
    _q(
        "Which module is commonly used to create a virtual environment?",
        ["pip", "venv", "asyncio", "os.path"],
        1,
    ),
    _q(
        "What is the value of 2 ** 3 in Python?",
        ["5", "6", "8", "9"],
        2,
    ),
    _q(
        "Which keyword is used to define a function?",
        ["function", "def", "fn", "lambda"],
        1,
    ),
    _q(
        "What is a list comprehension?",
        [
            "A way to sort lists",
            "A compact syntax to build lists from iterables",
            "A type of comment",
            "A debugger tool",
        ],
        1,
    ),
    _q(
        "What is the type of the literal None?",
        ["null", "NoneType", "undefined", "Optional"],
        1,
    ),
    _q(
        "What does the // operator perform?",
        ["Exponentiation", "Floor division", "Modulo only", "Bitwise XOR"],
        1,
    ),
    _q(
        "What does the import statement do?",
        ["Deletes modules", "Loads modules for use", "Compiles Python to C", "Runs tests"],
        1,
    ),
    _q(
        "Which statement about tuples is true (by default)?",
        [
            "Tuples are always sorted",
            "Tuples are immutable",
            "Tuples must have unique values",
            "Tuples cannot be nested",
        ],
        1,
    ),
    _q(
        "In a class, what is the purpose of __init__?",
        [
            "Import the class",
            "Initialize a new instance (constructor)",
            "Delete the class",
            "Mark the class as abstract",
        ],
        1,
    ),
]

DSA_DATA = [
    _q(
        "What is the time complexity of binary search on a sorted array of size n?",
        ["O(n)", "O(log n)", "O(n log n)", "O(1)"],
        1,
    ),
    _q(
        "A stack data structure is typically described as:",
        ["FIFO", "LIFO", "Random access", "Priority by value"],
        1,
    ),
    _q(
        "A queue data structure is typically described as:",
        ["LIFO", "FIFO", "LILO", "Stack-based only"],
        1,
    ),
    _q(
        "A singly linked list node usually contains:",
        [
            "Only a value",
            "A value and a reference to the next node",
            "A value and two children",
            "A key and a hash",
        ],
        1,
    ),
    _q(
        "Average-case time complexity of a hash table lookup (well-distributed hash):",
        ["O(n)", "O(log n)", "O(1)", "O(n^2)"],
        2,
    ),
    _q(
        "In a binary tree, each node has at most how many children?",
        ["1", "2", "3", "Unlimited"],
        1,
    ),
    _q(
        "Depth-first search (DFS) on a graph is often implemented with:",
        ["A queue only", "A stack or recursion", "A hash table only", "Sorting first"],
        1,
    ),
    _q(
        "Breadth-first search (BFS) on a graph is often implemented with:",
        ["A stack", "A queue", "A heap", "A trie"],
        1,
    ),
    _q(
        "What is the typical worst-case time complexity of merge sort?",
        ["O(n)", "O(n log n)", "O(n^2)", "O(log n)"],
        1,
    ),
    _q(
        "A tree is a connected graph with no cycles. A graph with no cycles is also called:",
        [
            "A clique",
            "A directed acyclic graph (if edges directed) or a forest of trees",
            "A complete graph",
            "A mesh",
        ],
        1,
    ),
]


class Command(BaseCommand):
    help = "Create 10 Python + 10 DSA test questions and two seed quizzes."

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        admin = User.objects.filter(is_superuser=True).first() or User.objects.first()

        cat_py, _ = Category.objects.get_or_create(name="Python")
        cat_dsa, _ = Category.objects.get_or_create(name="DSA")

        titles = ("Python Fundamentals (Seed)", "DSA Fundamentals (Seed)")
        for title in titles:
            old = Quiz.objects.filter(title=title).first()
            if old:
                q_ids = list(
                    QuizQuestion.objects.filter(quiz=old).values_list("question_id", flat=True)
                )
                old.delete()
                if q_ids:
                    Question.objects.filter(id__in=q_ids).delete()

        quiz_py = Quiz.objects.create(
            title="Python Fundamentals (Seed)",
            description="10 sample Python questions for testing.",
        )
        quiz_dsa = Quiz.objects.create(
            title="DSA Fundamentals (Seed)",
            description="10 sample DSA questions for testing.",
        )

        def build_questions(specs, category: Category, start_order: int, quiz: Quiz):
            for i, spec in enumerate(specs):
                q = Question.objects.create(
                    category=category,
                    created_by=admin,
                    text=spec["text"],
                    is_approved=True,
                )
                for j, opt in enumerate(spec["options"]):
                    Choice.objects.create(
                        question=q,
                        text=opt,
                        is_correct=(j == spec["correct"]),
                    )
                QuizQuestion.objects.create(
                    quiz=quiz,
                    question=q,
                    order_num=start_order + i,
                )

        build_questions(PYTHON_DATA, cat_py, 0, quiz_py)
        build_questions(DSA_DATA, cat_dsa, 0, quiz_dsa)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded: {quiz_py.title} ({len(PYTHON_DATA)} questions), "
                f"{quiz_dsa.title} ({len(DSA_DATA)} questions)."
            )
        )
