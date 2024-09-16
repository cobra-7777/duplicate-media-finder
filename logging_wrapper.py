import logging
import os
from datetime import datetime

# Setup function for logging
def setup_logger():
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create log file with the current date and a custom name
    log_filename = datetime.now().strftime("%Y-%m-%d") + "_copycleanerlog.log"
    log_file = os.path.join(log_dir, log_filename)

    # Configure logging
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

# Wrapper functions for logging
def log_info(message):
    logging.info(message)

def log_error(message):
    logging.error(message)

def log_debug(message):
    logging.debug(message)

def log_warning(message):
    logging.warning(message)