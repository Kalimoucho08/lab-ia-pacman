"""
Utilitaires de gestion des erreurs et validation.

Fournit des classes d'exceptions personnalisées,
des middlewares de validation et des helpers pour
gérer les erreurs de manière cohérente dans l'API.
"""
import logging
import traceback
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class ExperimentError(Exception):
    """Exception personnalisée pour les erreurs liées aux expériences."""
    
    def __init__(self, message: str, error_code: str = "EXPERIMENT_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class TrainingError(Exception):
    """Exception personnalisée pour les erreurs d'entraînement."""
    
    def __init__(self, message: str, error_code: str = "TRAINING_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class EnvironmentError(Exception):
    """Exception personnalisée pour les erreurs d'environnement."""
    
    def __init__(self, message: str, error_code: str = "ENVIRONMENT_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationErrorWithDetails(ValidationError):
    """Extension de ValidationError avec des détails supplémentaires."""
    
    def __init__(self, errors: list, model_name: str = None):
        super().__init__(errors, model_name)
        self.model_name = model_name

async def validation_exception_handler(request: Request, exc: ValidationError):
    """Gestionnaire d'exceptions pour les erreurs de validation Pydantic."""
    error_details = []
    
    for error in exc.errors():
        error_details.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Validation error: {error_details}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Erreur de validation des données",
            "errors": error_details,
            "error_code": "VALIDATION_ERROR"
        }
    )

async def experiment_error_handler(request: Request, exc: ExperimentError):
    """Gestionnaire d'exceptions pour ExperimentError."""
    logger.error(f"Experiment error: {exc.message}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": exc.message,
            "error_code": exc.error_code,
            "details": exc.details
        }
    )

async def training_error_handler(request: Request, exc: TrainingError):
    """Gestionnaire d'exceptions pour TrainingError."""
    logger.error(f"Training error: {exc.message}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": exc.message,
            "error_code": exc.error_code,
            "details": exc.details
        }
    )

async def environment_error_handler(request: Request, exc: EnvironmentError):
    """Gestionnaire d'exceptions pour EnvironmentError."""
    logger.error(f"Environment error: {exc.message}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": exc.message,
            "error_code": exc.error_code,
            "details": exc.details
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """Gestionnaire d'exceptions générique pour toutes les exceptions non gérées."""
    # Ne pas logger les erreurs HTTP standard
    if not isinstance(exc, HTTPException):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        traceback_str = traceback.format_exc()
        logger.debug(f"Traceback: {traceback_str}")
    
    # Si c'est une HTTPException, laisser FastAPI la gérer
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error_code": "HTTP_ERROR"
            }
        )
    
    # Pour les autres exceptions, retourner une erreur 500
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Une erreur interne est survenue",
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": str(exc) if str(exc) else "No details available"
        }
    )

def validate_parameters(parameters: Dict[str, Any], schema: Any) -> Dict[str, Any]:
    """
    Valide des paramètres contre un schéma Pydantic.
    
    Args:
        parameters: Dictionnaire de paramètres à valider
        schema: Classe de schéma Pydantic
    
    Returns:
        Dict[str, Any]: Paramètres validés
    
    Raises:
        ValidationErrorWithDetails: Si la validation échoue
    """
    try:
        validated = schema(**parameters)
        return validated.dict()
    except ValidationError as e:
        raise ValidationErrorWithDetails(e.errors(), schema.__name__)

def validate_range(value: float, min_val: float, max_val: float, field_name: str) -> float:
    """
    Valide qu'une valeur est dans une plage spécifiée.
    
    Args:
        value: Valeur à valider
        min_val: Valeur minimale (incluse)
        max_val: Valeur maximale (incluse)
        field_name: Nom du champ pour les messages d'erreur
    
    Returns:
        float: Valeur validée
    
    Raises:
        ValueError: Si la valeur est hors plage
    """
    if not (min_val <= value <= max_val):
        raise ValueError(
            f"{field_name} doit être entre {min_val} et {max_val}, reçu {value}"
        )
    return value

def validate_positive(value: float, field_name: str) -> float:
    """
    Valide qu'une valeur est positive.
    
    Args:
        value: Valeur à valider
        field_name: Nom du champ pour les messages d'erreur
    
    Returns:
        float: Valeur validée
    
    Raises:
        ValueError: Si la valeur n'est pas positive
    """
    if value <= 0:
        raise ValueError(f"{field_name} doit être positif, reçu {value}")
    return value

def validate_integer(value: float, field_name: str) -> int:
    """
    Valide qu'une valeur est un entier.
    
    Args:
        value: Valeur à valider
        field_name: Nom du champ pour les messages d'erreur
    
    Returns:
        int: Valeur convertie en entier
    
    Raises:
        ValueError: Si la valeur n'est pas un entier
    """
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} doit être un nombre, reçu {type(value)}")
    
    if not float(value).is_integer():
        raise ValueError(f"{field_name} doit être un entier, reçu {value}")
    
    return int(value)

# Middleware pour logger les requêtes et réponses
async def log_requests_middleware(request: Request, call_next):
    """Middleware pour logger les requêtes entrantes et les réponses."""
    # Logger la requête
    logger.info(f"Requête: {request.method} {request.url.path}")
    
    # Exécuter la requête
    response = await call_next(request)
    
    # Logger la réponse
    logger.info(f"Réponse: {response.status_code} pour {request.method} {request.url.path}")
    
    return response

# Middleware pour valider les en-têtes
async def validate_headers_middleware(request: Request, call_next):
    """Middleware pour valider les en-têtes requis."""
    # Vérifier l'en-tête Content-Type pour les requêtes POST/PUT
    if request.method in ["POST", "PUT", "PATCH"]:
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            logger.warning(f"Content-Type invalide: {content_type}")
            # On ne bloque pas, mais on logge un avertissement
    
    response = await call_next(request)
    return response