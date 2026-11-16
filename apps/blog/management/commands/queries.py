from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.blog.queries import QUERIES

QUERY_ARGS = {
    4: {"slug": "science"},
    7: {"page": 1},
    8: {"word": "movement"},
    9: {"domain": "example"},
    11: {"slugs": ["environment", "letter"]},
    12: {"year": 2026, "month": 5},
    13: {"days": 1},
    14: {"start": date(2026, 1, 1), "end": date.today()},
    15: {"email": "john"},
    16: {"tag_slug": "Python"},
    17: {"category_slug": ""},
    21: {"first_slug": "python", "second_slug": "django"},
    22: {"text": "gaming"},
    34: {"min_posts": 1},
    37: {"text": "john"},
    40: {"name": "Test"},
    41: {"days": 30},
    42: {"category_slug": "technology", "tag_slug": "django"},
    43: {"source_slug": "science", "target_slug": "technology"},
}


class Command(BaseCommand):
    help = "Run blog ORM queries"

    def add_arguments(self, parser):
        parser.add_argument(
            "--number",
            type=int,
            help="Run a specific query by number",
        )
        parser.add_argument(
            "--sql",
            action="store_true",
            help="Display generated SQL",
        )

    def handle(self, *args, **options):
        number = options["number"]
        show_sql = options["sql"]

        if number is not None:
            if number not in QUERIES:
                raise CommandError(f"Query {number} does not exist")

            query_numbers = [number]
        else:
            query_numbers = [
                n for n in QUERIES if n not in range(40, 45)
            ]

        for query_number in query_numbers:
            self.run_query(query_number, show_sql)

    def run_query(self, number, show_sql):
        query_function = QUERIES[number]
        arguments = QUERY_ARGS.get(number, {})

        with CaptureQueriesContext(connection) as queries:
            result = query_function(**arguments)

            if hasattr(result, "query"):
                result = list(result)

        self.stdout.write(f"Query {number}: {query_function.__name__}")
        self.stdout.write(f"SQL queries: {len(queries)}")

        if show_sql:
            for query in queries:
                self.stdout.write(query["sql"])

        if isinstance(result, (list, tuple)):
            self.stdout.write(f"Total rows: {len(result)}")

            for row in result[:5]:
                if hasattr(row, "__dict__"):
                    row = {
                        key: value
                        for key , value in row.__dict__.items()
                        if not key.startswith("_")
                    }
                self.stdout.write(str(row))

        else:
            self.stdout.write(f"Result: {result}")