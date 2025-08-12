"""
Configuração de logging estruturado para o backend
Implementa logging com rotação, formatação JSON e níveis configuráveis
"""
import logging
import logging.handlers
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Formatador customizado para logs em JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata o log record como JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process,
        }
        
        # Adicionar exception info se presente
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Adicionar campos extras
        if hasattr(record, 'extra_data'):
            log_data["extra"] = record.extra_data
        
        return json.dumps(log_data)


def setup_logger(
    name: str = "chat_app",
    level: str = "INFO",
    log_dir: str = "logs",
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    console_output: bool = True,
    json_format: bool = True
) -> logging.Logger:
    """
    Configura um logger com handlers para arquivo e console
    
    Args:
        name: Nome do logger
        level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Diretório para salvar logs
        max_bytes: Tamanho máximo do arquivo de log antes de rotacionar
        backup_count: Número de arquivos de backup a manter
        console_output: Se deve enviar logs para o console
        json_format: Se deve usar formato JSON
    
    Returns:
        Logger configurado
    """
    # Criar diretório de logs se não existir
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Criar logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Limpar handlers existentes
    logger.handlers = []
    
    # Configurar formatador
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Handler para arquivo com rotação
    file_handler = logging.handlers.RotatingFileHandler(
        log_path / f"{name}.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para erros em arquivo separado
    error_handler = logging.handlers.RotatingFileHandler(
        log_path / f"{name}_errors.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    # Handler para console
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


class LoggerMixin:
    """Mixin para adicionar logging a classes"""
    
    @property
    def logger(self) -> logging.Logger:
        """Retorna logger para a classe"""
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(
                f"{self.__class__.__module__}.{self.__class__.__name__}"
            )
        return self._logger
    
    def log_info(self, message: str, **kwargs):
        """Log de informação com dados extras"""
        self.logger.info(message, extra={'extra_data': kwargs})
    
    def log_error(self, message: str, exc_info: bool = True, **kwargs):
        """Log de erro com dados extras"""
        self.logger.error(message, exc_info=exc_info, extra={'extra_data': kwargs})
    
    def log_warning(self, message: str, **kwargs):
        """Log de warning com dados extras"""
        self.logger.warning(message, extra={'extra_data': kwargs})
    
    def log_debug(self, message: str, **kwargs):
        """Log de debug com dados extras"""
        self.logger.debug(message, extra={'extra_data': kwargs})


# Logger principal da aplicação
app_logger = setup_logger(
    name="chat_app",
    level="INFO",
    console_output=True,
    json_format=True
)

# Logger para requisições Claude
claude_logger = setup_logger(
    name="claude_requests",
    level="DEBUG",
    console_output=False,
    json_format=True
)

# Logger para performance
perf_logger = setup_logger(
    name="performance",
    level="INFO",
    console_output=False,
    json_format=True
)