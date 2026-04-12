"""
Service de synchronisation de la bibliothèque mondiale de devises.
Optimisé pour être ULTRA-LEAN : pas de requêtes lourdes répétitives.
"""
from typing import List, Dict
from core.database import get_session
from core.models import Currency, Transaction, CurrencyPurchase, Account
from utils.constants import WORLD_CURRENCIES, DEFAULT_CURRENCY_CODE

class WorldCurrencySyncEngine:
    """
    Moteur de synchronisation purifié : Rapidité et Efficacité.
    """
    def __init__(self, currency_repo):
        self.currency_repo = currency_repo

    def get_catalog_status(self) -> List[Dict]:
        """
        Récupère l'état de la bibliothèque en mode ultra-rapide.
        """
        try:
            with get_session() as session:
                # 1. Charger uniquement les devises existantes en DB
                all_db = self.currency_repo.get_all(session, limit=1000, include_inactive=True)
                db_map = {c.code.upper(): c for c in all_db}
                
                result = []
                # 2. On part du catalogue ELITE (les 5 de base)
                for entry in WORLD_CURRENCIES:
                    code = entry["code"].upper()
                    db_curr = db_map.get(code)
                    
                    # On ne calcule t_count/p_count QUE si la devise existe en DB et est active
                    # pour savoir si on peut la désactiver
                    can_disable = True
                    if db_curr and db_curr.is_active:
                        if db_curr.is_default:
                            can_disable = False
                        else:
                            # Requête minimale : checking existence rather than full count if possible
                            t_exists = session.query(Transaction.id).join(Account).filter(Account.currency_id == db_curr.id).first() is not None
                            p_exists = session.query(CurrencyPurchase.id).filter(CurrencyPurchase.currency_id == db_curr.id).first() is not None
                            if t_exists or p_exists:
                                can_disable = False

                    result.append({
                        "code": code,
                        "name": entry["name"],
                        "symbol": entry["symbol"],
                        "country": db_curr.country if (db_curr and db_curr.country) else entry.get("country", ""),
                        "is_active": db_curr.is_active if db_curr else False,
                        "is_main": db_curr.is_default if db_curr else (code == DEFAULT_CURRENCY_CODE),
                        "can_disable": can_disable,
                        "db_id": db_curr.id if db_curr else None
                    })

                # 3. Ajouter les devises DB hors Elite qui sont actives (découvertes par recherche)
                elite_codes = {e["code"].upper() for e in WORLD_CURRENCIES}
                for code, db_curr in db_map.items():
                    if code not in elite_codes and db_curr.is_active:
                        # Toujours vérifiable pour suppression
                        t_exists = session.query(Transaction.id).join(Account).filter(Account.currency_id == db_curr.id).first() is not None
                        p_exists = session.query(CurrencyPurchase.id).filter(CurrencyPurchase.currency_id == db_curr.id).first() is not None
                        
                        result.append({
                            "code": code,
                            "name": db_curr.name,
                            "symbol": db_curr.symbol,
                            "country": db_curr.country or "Personnalisée",
                            "is_active": True,
                            "is_main": db_curr.is_default,
                            "can_disable": not (t_exists or p_exists),
                            "db_id": db_curr.id
                        })

                # Tri standard
                result.sort(key=lambda x: (not x['is_active'], x['code']))
                return result

        except Exception as e:
            print(f"❌ WorldCurrencySyncEngine Error: {str(e)}")
            return []
