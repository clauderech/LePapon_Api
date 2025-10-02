import logging, os, sys, json, time

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = {
            "ts": time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(record.created)),
            "level": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info:
            base["exc"] = self.formatException(record.exc_info)
        return json.dumps(base, ensure_ascii=False)

def _build_handler() -> logging.Handler:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(JsonFormatter())
    return h

_root_configured = False

def configure_logging():
    global _root_configured
    if _root_configured:
        return
    logging.basicConfig(level=LOG_LEVEL, handlers=[_build_handler()], force=True)
    _root_configured = True

# Helper para obter logger já configurado

def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
