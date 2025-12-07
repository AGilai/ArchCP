import logging
import sys
from .config import settings

class ColoredFormatter(logging.Formatter):
    """
    Custom formatter to add colors to log levels.
    Format: [Timestamp] [Level] [LoggerName] Message
    """
    # ANSI Escape Codes
    grey = "\x1b[38;20m"
    green = "\x1b[32;20m"
    blue = "\x1b[34;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    # The Log Format
    fmt = "%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    FORMATS = {
        logging.DEBUG: grey + fmt + reset,
        logging.INFO: green + fmt + reset,
        logging.WARNING: yellow + fmt + reset,
        logging.ERROR: red + fmt + reset,
        logging.CRITICAL: bold_red + fmt + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt=self.date_fmt)
        return formatter.format(record)

def get_logger(name: str):
    """
    Factory function to get a configured logger.
    """
    logger = logging.getLogger(name)
    
    # Only configure if handler hasn't been added (prevents duplicates)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(ColoredFormatter())
        logger.addHandler(handler)
        
        # Set level from config
        level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(level)
        
    return logger