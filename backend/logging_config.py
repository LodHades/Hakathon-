import sys

from loguru import logger

from backend.settings import settings


_LOG_DIR = settings.ROOT / ".logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

_console_configured = False
_module_sinks: set[str] = set()


def setup_base_logging() -> None:
    """Configura el sink de consola (stderr) una sola vez."""
    global _console_configured
    if _console_configured:
        return

    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[module]}</cyan> - <level>{message}</level>"
        ),
        filter=lambda record: "module" in record["extra"],
    )
    _console_configured = True


def get_logger(module_name: str, DIR: str):
    """
    Retorna un logger contextualizado con `module_name`.
    Cada módulo escribe en `.logs/<DIR>/<module_name>.log` con rotación.
    """
    if not _console_configured:
        setup_base_logging()

    key = f"{DIR}/{module_name}"
    if key not in _module_sinks:
        sub_dir = _LOG_DIR / DIR
        sub_dir.mkdir(parents=True, exist_ok=True)
        logger.add(
            sub_dir / f"{module_name}.log",
            level="DEBUG",
            rotation="5 MB",
            retention=3,
            encoding="utf-8",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            filter=lambda record, mn=module_name: record["extra"].get("module") == mn,
            enqueue=True,
        )
        _module_sinks.add(key)

    return logger.bind(module=module_name)
