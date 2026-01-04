import logging
import sys

class AutoTracebackLogger(logging.Logger):
    def error(self, message, *args, **kwargs):
        # Automatically add exc_info if we're in an exception context
        if sys.exc_info()[0] is not None and 'exc_info' not in kwargs:
            kwargs['exc_info'] = True
        super().error(message, *args, **kwargs)
    
    def critical(self, message, *args, **kwargs):
        # Automatically add exc_info if we're in an exception context
        if sys.exc_info()[0] is not None and 'exc_info' not in kwargs:
            kwargs['exc_info'] = True
        super().critical(message, *args, **kwargs)

def setup_logger():
    # Set as default logger class
    logging.setLoggerClass(AutoTracebackLogger)

    # Your existing configuration
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("app.log"),
        ],
    )

