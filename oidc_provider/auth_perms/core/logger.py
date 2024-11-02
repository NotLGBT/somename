import os
import logging 
from pathlib import Path

from flask import request
from dotenv import load_dotenv


class RequestURLFilterForLogs(logging.Filter):
    """ 
    Add request url for every log
    """
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_url = request.path if request else 'N/A'
        return super().filter(record)

    
def configure_logs_for_module(loger_name: str) -> None:
    """ 
    Configurate logging for app
    params:
        loger_name: Name to create log file with name like 'loger_name_logs.log'
    """
    load_dotenv(os.path.join(os.getcwd(), '.env'))
    log_directory = os.getenv('ECOSYSTEM54_LOGGING_MODULE_DIRECTORY')
    if not log_directory:
        log_directory = os.getcwd()
    try:
        if not os.path.exists(os.path.join(log_directory, 'logs')):
            os.mkdir(os.path.join(log_directory, 'logs'))
    except FileNotFoundError:
        Path(f'{log_directory}/logs').mkdir(exist_ok=True, parents=True)
    path_to_logs = os.path.join(os.path.join(log_directory, 'logs'), f'{loger_name}_logs.log')
    logger = logging.getLogger(loger_name)
    file_handler = logging.FileHandler(path_to_logs)
    logger.addFilter(RequestURLFilterForLogs())
    file_handler.setFormatter(logging.Formatter('{asctime} - {levelname} - [Endpoint: {request_url}] - {message}',  
                                                        datefmt='%d-%b-%y %H:%M:%S', style='{'))
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
