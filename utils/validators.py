"""
Validation des données
"""
from datetime import datetime
from typing import Optional, Tuple


def validate_amount(amount: float) -> Tuple[bool, Optional[str]]:
    """
    Valide un montant.
    
    Args:
        amount: Montant à valider
        
    Returns:
        Tuple (est_valide, message_erreur)
    """
    if amount is None:
        return False, "Le montant est requis"
    
    if not isinstance(amount, (int, float)):
        return False, "Le montant doit être un nombre"
    
    if amount < 0:
        return False, "Le montant ne peut pas être négatif"
    
    if amount == 0:
        return False, "Le montant doit être supérieur à zéro"
    
    return True, None


def validate_date(date: datetime) -> Tuple[bool, Optional[str]]:
    """
    Valide une date.
    
    Args:
        date: Date à valider
        
    Returns:
        Tuple (est_valide, message_erreur)
    """
    if date is None:
        return False, "La date est requise"
    
    if not isinstance(date, datetime):
        return False, "Format de date invalide"
    
    # Vérifier que la date n'est pas dans le futur
    if date > datetime.now():
        return False, "La date ne peut pas être dans le futur"
    
    return True, None


def validate_currency_code(code: str) -> Tuple[bool, Optional[str]]:
    """
    Valide un code de devise.
    
    Args:
        code: Code de devise (ex: EUR, USD, DZD)
        
    Returns:
        Tuple (est_valide, message_erreur)
    """
    if not code:
        return False, "Le code de devise est requis"
    
    if not isinstance(code, str):
        return False, "Le code de devise doit être une chaîne"
    
    if len(code) != 3:
        return False, "Le code de devise doit contenir 3 caractères"
    
    if not code.isupper():
        return False, "Le code de devise doit être en majuscules"
    
    return True, None


def validate_required_field(value: any, field_name: str) -> Tuple[bool, Optional[str]]:
    """
    Valide qu'un champ requis n'est pas vide.
    
    Args:
        value: Valeur à valider
        field_name: Nom du champ
        
    Returns:
        Tuple (est_valide, message_erreur)
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return False, f"Le champ '{field_name}' est requis"
    
    return True, None


def validate_positive_number(number: float, field_name: str) -> Tuple[bool, Optional[str]]:
    """
    Valide qu'un nombre est positif.
    
    Args:
        number: Nombre à valider
        field_name: Nom du champ
        
    Returns:
        Tuple (est_valide, message_erreur)
    """
    if number is None:
        return False, f"Le champ '{field_name}' est requis"
    
    if not isinstance(number, (int, float)):
        return False, f"Le champ '{field_name}' doit être un nombre"
    
    if number <= 0:
        return False, f"Le champ '{field_name}' doit être positif"
    
    return True, None



