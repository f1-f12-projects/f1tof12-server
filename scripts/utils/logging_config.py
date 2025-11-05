import logging
import os
from logging.handlers import RotatingFileHandler

# Configure logging
if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
    # Lambda environment - use CloudWatch
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(filename)s:%(funcName)s:%(levelname)s] - %(message)s'
    )
else:
    # Local development - use file logging
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    handler = RotatingFileHandler(
        f'{log_dir}/app.log',
        maxBytes=1024*1024*1024,  # 1GB
        backupCount=5
    )
    handler.setFormatter(logging.Formatter('%(asctime)s [%(filename)s:%(funcName)s:%(levelname)s] - %(message)s'))
    
    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler]
    )