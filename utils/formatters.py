"""
Formatage des données pour l'affichage
"""
from datetime import datetime
from typing import Optional
from .constants import DATE_FORMAT, DATETIME_FORMAT, AMOUNT_DECIMAL_PLACES

# [UNIFIED] 2026-04-08 - Global amount format setting
# Can be set from settings to "space" (French) or "dot" (Windows)
_amount_format_global = "space"

def set_amount_format(format_type: str):
    """Set global amount format (call from settings)"""
    global _amount_format_global
    _amount_format_global = format_type

def get_amount_format() -> str:
    """Get global amount format"""
    return _amount_format_global


def format_amount(amount: float, currency_symbol: str = "DA", amount_format: str = None) -> str:
    """
    Formate un montant avec séparateurs de milliers et symbole de devise.
    
    Exemple: format_amount(15000.50, "DA") -> "15 000.50 DA"
    Exemple: format_amount(15000.50, "DA", "dot") -> "15.000,50 DA"
    
    Args:
        amount: Montant à formater
        currency_symbol: Symbole de la devise
        amount_format: "space" (format français) ou "dot" (format Windows). 
                      Si None, utilise le paramètre global.
        
    Returns:
        Montant formaté
    """
    # Utiliser le format global si non spécifié
    if amount_format is None:
        amount_format = _amount_format_global
    
    # Formater avec 2 décimales
    formatted = f"{amount:,.{AMOUNT_DECIMAL_PLACES}f}"
    
    if amount_format == "dot":
        # Format Windows: 1.000,00
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        # Format français: 1 000,00 (default)
        formatted = formatted.replace(",", " ")
    
    # Ajouter le symbole de devise
    return f"{formatted} {currency_symbol}"


def parse_amount(amount_str: str) -> float:
    """
    Parse une chaîne de montant formatée en float.
    
    Supporte les deux formats:
    - Format français: "15 000.50 DA" -> 15000.50
    - Format Windows: "15.000,50 DA" -> 15000.50
    
    Args:
        amount_str: Chaîne de montant
        
    Returns:
        Montant en float
    """
    # Retirer le symbole de devise
    amount_str = amount_str.split()[0] if " " in amount_str else amount_str
    
    # Détecter le format et normaliser
    if "," in amount_str and "." in amount_str:
        # Vérifier si c'est format Windows (1.000,50) ou français (1 000.50)
        if amount_str.rfind(",") < amount_str.rfind("."):
            # Format Windows: 1.000,50 -> supprimer les points, remplacer virgule par point
            amount_str = amount_str.replace(".", "").replace(",", ".")
        else:
            # Format français: 1 000.50 -> supprimer les espaces
            amount_str = amount_str.replace(" ", "")
    elif "," in amount_str:
        # Pas de points, juste virgule = soit format Windows sans millier soit français
        if amount_str.rfind(",") > 3:  # Plus de 3 chiffres avant la virgule =可能有separators
            amount_str = amount_str.replace(",", ".")
        # sinon leave as is (déjà format français 1000,50)
    else:
        # Pas de virgule, juste des points ou espaces
        amount_str = amount_str.replace(" ", "")
    
    # Convertir en float
    try:
        return float(amount_str)
    except ValueError:
        return 0.0


def format_date(date: datetime, include_time: bool = False) -> str:
    """
    Formate une date pour l'affichage.
    
    Args:
        date: Date à formater
        include_time: Inclure l'heure ou non
        
    Returns:
        Date formatée
    """
    if date is None:
        return ""
    
    format_str = DATETIME_FORMAT if include_time else DATE_FORMAT
    return date.strftime(format_str)


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse une chaîne de date en datetime.
    
    Args:
        date_str: Chaîne de date
        
    Returns:
        Date en datetime ou None si invalide
    """
    if not date_str:
        return None
    
    try:
        return datetime.strptime(date_str, DATE_FORMAT)
    except ValueError:
        try:
            return datetime.strptime(date_str, DATETIME_FORMAT)
        except ValueError:
            return None


def format_number(number: float, decimals: int = 2) -> str:
    """
    Formate un nombre avec séparateurs de milliers.
    
    Args:
        number: Nombre à formater
        decimals: Nombre de décimales
        
    Returns:
        Nombre formaté
    """
    formatted = f"{number:,.{decimals}f}"
    return formatted.replace(",", " ")
