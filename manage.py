import os
import sys

from settings.conf import BLOG_ENV_ID


def main() -> None:
    settings_module = f"settings.env.{BLOG_ENV_ID}"
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()