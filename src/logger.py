import logging

# Configuración del logger: se escribe en "log.txt" con hora y mensaje
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")
file_handler = logging.FileHandler("log.txt")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)