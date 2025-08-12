"""
Tratamento de erros customizado para o backend
Implementa handlers de erro, retry logic e recuperação graceful
"""
from functools import wraps
from typing import Any, Callable, Optional, Type, Union, Tuple
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from logger_config import app_logger


@dataclass
class ErrorContext:
    """Contexto de erro para logging e recuperação"""
    error_type: str
    error_message: str
    timestamp: datetime
    module: str
    function: str
    traceback: str
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> dict:
        """Converte para dicionário para serialização"""
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
            "module": self.module,
            "function": self.function,
            "traceback": self.traceback,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }


class ChatAppError(Exception):
    """Classe base para erros da aplicação"""
    def __init__(self, message: str, code: str = "UNKNOWN", details: Optional[dict] = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.now()


class ValidationError(ChatAppError):
    """Erro de validação de dados"""
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            details={"field": field, "value": str(value) if value else None}
        )


class ClaudeAPIError(ChatAppError):
    """Erro na comunicação com Claude API"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(
            message,
            code="CLAUDE_API_ERROR",
            details={"status_code": status_code}
        )


class SessionError(ChatAppError):
    """Erro relacionado a sessões"""
    def __init__(self, message: str, session_id: Optional[str] = None):
        super().__init__(
            message,
            code="SESSION_ERROR",
            details={"session_id": session_id}
        )


class FileProcessingError(ChatAppError):
    """Erro no processamento de arquivos"""
    def __init__(self, message: str, filename: Optional[str] = None):
        super().__init__(
            message,
            code="FILE_PROCESSING_ERROR",
            details={"filename": filename}
        )


def handle_errors(
    default_return: Any = None,
    log_errors: bool = True,
    reraise: bool = False,
    error_types: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator para tratamento de erros
    
    Args:
        default_return: Valor a retornar em caso de erro
        log_errors: Se deve logar erros
        reraise: Se deve re-lançar a exceção após tratar
        error_types: Tipos de erro a capturar
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_types as e:
                if log_errors:
                    context = ErrorContext(
                        error_type=type(e).__name__,
                        error_message=str(e),
                        timestamp=datetime.now(),
                        module=func.__module__,
                        function=func.__name__,
                        traceback=traceback.format_exc()
                    )
                    app_logger.error(
                        f"Error in {func.__name__}: {str(e)}",
                        extra={'error_context': context.to_dict()}
                    )
                
                if reraise:
                    raise
                
                return default_return
        
        return wrapper
    return decorator


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator para retry automático em caso de falha
    
    Args:
        max_retries: Número máximo de tentativas
        delay: Delay inicial entre tentativas (segundos)
        backoff: Fator de multiplicação do delay a cada tentativa
        exceptions: Tipos de exceção que devem triggar retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        app_logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay} seconds..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        app_logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}"
                        )
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


class ErrorHandler:
    """Handler centralizado de erros"""
    
    @staticmethod
    def handle_validation_error(error: ValidationError) -> dict:
        """Trata erro de validação"""
        return {
            "error": True,
            "code": error.code,
            "message": str(error),
            "details": error.details,
            "timestamp": error.timestamp.isoformat()
        }
    
    @staticmethod
    def handle_claude_api_error(error: ClaudeAPIError) -> dict:
        """Trata erro da API do Claude"""
        return {
            "error": True,
            "code": error.code,
            "message": "Erro ao comunicar com Claude. Por favor, tente novamente.",
            "details": {
                "original_message": str(error),
                "status_code": error.details.get("status_code")
            },
            "timestamp": error.timestamp.isoformat()
        }
    
    @staticmethod
    def handle_session_error(error: SessionError) -> dict:
        """Trata erro de sessão"""
        return {
            "error": True,
            "code": error.code,
            "message": str(error),
            "details": error.details,
            "timestamp": error.timestamp.isoformat()
        }
    
    @staticmethod
    def handle_generic_error(error: Exception) -> dict:
        """Trata erro genérico"""
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": "Ocorreu um erro interno. Por favor, tente novamente.",
            "details": {
                "error_type": type(error).__name__,
                "debug_message": str(error) if app_logger.level <= 10 else None  # DEBUG level
            },
            "timestamp": datetime.now().isoformat()
        }


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: Type[Exception] = Exception
):
    """
    Implementa pattern Circuit Breaker para prevenir cascata de falhas
    
    Args:
        failure_threshold: Número de falhas antes de abrir o circuito
        recovery_timeout: Tempo em segundos antes de tentar recuperar
        expected_exception: Tipo de exceção esperada
    """
    def decorator(func: Callable) -> Callable:
        func._failures = 0
        func._last_failure_time = None
        func._circuit_open = False
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Verificar se circuito está aberto
            if func._circuit_open:
                if func._last_failure_time and \
                   (time.time() - func._last_failure_time) > recovery_timeout:
                    func._circuit_open = False
                    func._failures = 0
                    app_logger.info(f"Circuit breaker reset for {func.__name__}")
                else:
                    raise ChatAppError(
                        f"Circuit breaker is open for {func.__name__}",
                        code="CIRCUIT_BREAKER_OPEN"
                    )
            
            try:
                result = func(*args, **kwargs)
                func._failures = 0  # Reset on success
                return result
            except expected_exception as e:
                func._failures += 1
                func._last_failure_time = time.time()
                
                if func._failures >= failure_threshold:
                    func._circuit_open = True
                    app_logger.error(
                        f"Circuit breaker opened for {func.__name__} after {func._failures} failures"
                    )
                
                raise
        
        return wrapper
    return decorator