import argparse
from pathlib import Path
from impact.config import load_config
from impact.inference.runner import ExperimentRunner


def main():
    parser = argparse.ArgumentParser(description="IMPACT Execution Harness")
    parser.add_argument(
        "--config",
        type=str,
        default="configs/pilot.yaml",
        help="Path to YAML configuration file",
    )
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="Path to existing run directory to resume",
    )

    args = parser.parse_args()
    config_path = Path(args.config)
    config = load_config(config_path)

    resume_dir = Path(args.resume) if args.resume else None
    runner = ExperimentRunner(config=config, existing_run_dir=resume_dir)
    run_path = runner.run()
    print(f"\nCompleted/Paused. Run directory: {run_path}")


if __name__ == "__main__":
    main()
