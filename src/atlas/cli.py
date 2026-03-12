import argparse

from .agents.backtest_loop import run_backtest
from .utils.logging import get_logger


def main():
    parser = argparse.ArgumentParser(description="ATLAS mock runner")
    parser.add_argument("--days", type=int, default=1, help="Number of mock trading days")
    args = parser.parse_args()

    logger = get_logger()
    logger.info("Starting ATLAS mock run for %s day(s)", args.days)
    run_backtest(days=args.days, logger=logger)
    logger.info("Finished ATLAS mock run")


if __name__ == "__main__":
    main()
