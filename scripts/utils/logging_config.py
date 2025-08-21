import logging
import os
from logging.handlers import RotatingFileHandler

# Configure logging for local development
if not os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    handler = RotatingFileHandler(
        f'{log_dir}/app.log',
        maxBytes=1024*1024*1024,  # 1GB
        backupCount=5
    )
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler]
    )