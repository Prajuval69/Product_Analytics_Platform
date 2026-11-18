import argparse
import logging

from platform_app.config import Settings
from platform_app.pipeline import execute_task, run


def main():
    parser = argparse.ArgumentParser(description="Local synthetic product analytics pipeline")
    parser.add_argument(
        "command",
        choices=[
            "pipeline",
            "generate",
            "load",
            "quality",
            "dbt-parse",
            "dbt-build",
            "dbt-staging",
            "dbt-intermediate",
            "dbt-marts",
            "dbt-test",
            "dbt-docs",
            "features",
            "ml",
            "export",
            "verify",
        ],
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = Settings.from_env()
    if args.command == "pipeline":
        run(settings)
    else:
        execute_task(settings, args.command)


if __name__ == "__main__":
    main()
