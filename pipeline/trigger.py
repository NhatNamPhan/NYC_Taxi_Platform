"""Trigger the monthly DAG without shell-specific JSON escaping."""
import json
import subprocess

from pipeline.config import month_arguments


def main(argv=None):
    args = month_arguments(__doc__, argv)
    configuration = json.dumps({"start_month": args.start_month, "end_month": args.end_month})
    subprocess.run(["airflow", "dags", "unpause", "nyc_taxi_pipeline"], check=True)
    subprocess.run(["airflow", "dags", "trigger", "nyc_taxi_pipeline", "--conf", configuration], check=True)


if __name__ == "__main__":
    main()
