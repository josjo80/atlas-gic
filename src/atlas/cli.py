import argparse

from .config import Config
from .agents.backtest_loop import run_backtest
from .utils.logging import get_logger


def main():
    parser = argparse.ArgumentParser(description="ATLAS runner")
    parser.add_argument("--days", type=int, default=1, help="Number of trading days to simulate")
    args = parser.parse_args()

    config = Config.from_env()
    logger = get_logger()
    logger.info("Starting ATLAS run for %s day(s)", args.days)
    run_backtest(days=args.days, logger=logger, config=config)
    logger.info("Finished ATLAS run")


if __name__ == "__main__":
    main()
