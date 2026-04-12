"""
Service pour le module Dashboard
"""
from typing import Dict, List
from datetime import datetime
from core.database import get_session
from modules.treasury.repository import AccountRepository, TransactionRepository
from modules.currency.repository import CurrencyRepository, ExchangeRateRepository
from modules.logistics.repository import ContainerRepository, LicenseRepository
from modules.external_debt.repository import ExternalTransactionRepository, ExternalContactRepository
from utils.constants import DEFAULT_CURRENCY_CODE

class DashboardService:
    def __init__(self):
        self.account_repo = AccountRepository()
        self.transaction_repo = TransactionRepository()
        self.currency_repo = CurrencyRepository()
        self.rate_repo = ExchangeRateRepository()
        self.container_repo = ContainerRepository()
        self.license_repo = LicenseRepository()
        self.ext_trans_repo = ExternalTransactionRepository()
        self.ext_contact_repo = ExternalContactRepository()

    def get_summary_data(self) -> Dict:
        """Récupère les données réelles pour le Dashboard"""
        with get_session() as session:
            # 1. DONNÉES TRÉSORERIE (Réel)
            accounts = self.account_repo.get_active(session)
            
            total_dzd = sum(acc.balance for acc in accounts if acc.currency.code == DEFAULT_CURRENCY_CODE)
            
            foreign_balances = []
            total_foreign_in_dzd = 0.0
            
            foreign_currencies = [c for c in self.currency_repo.get_active(session) if not c.is_default]
            for curr in foreign_currencies:
                curr_balance = sum(acc.balance for acc in accounts if acc.currency_id == curr.id)
                rate_obj = self.rate_repo.get_latest_rate(session, curr.id)
                rate = rate_obj.rate if rate_obj else 1.0
                
                in_dzd = curr_balance * rate
                total_foreign_in_dzd += in_dzd
                
                if curr_balance > 0:
                    foreign_balances.append({
                        'code': curr.code,
                        'symbol': curr.symbol,
                        'amount': curr_balance,
                        'in_dzd': in_dzd
                    })

            # Dernières transactions (pour mini chart)
            recent_trans = self.transaction_repo.get_recent(session, limit=7)
            formatted_trans = []
            trans_history = []  # Pour le chart
            for t in recent_trans:
                formatted_trans.append({
                    'date': t.date.strftime("%d/%m/%Y"),
                    'type': t.type,
                    'amount': f"{t.amount:,.2f} {t.account.currency.symbol}",
                    'desc': t.description
                })
                trans_history.append(t.amount)
            
            # Inverser pour afficher du plus ancien au plus récent
            trans_history = list(reversed(trans_history))

            # 2. DONNÉES LOGISTIQUES (Réel)
            all_containers = self.container_repo.get_all(session, limit=1000, include_inactive=False)
            active_containers = [c for c in all_containers if c.is_active]
            # Statut "EN_ATTENTE" = en attente d'arrivée
            pending_arrival = len([c for c in active_containers if getattr(c, 'status', 'EN_ATTENTE') == 'EN_ATTENTE'])
            
            all_licenses = self.license_repo.get_all(session, limit=1000, include_inactive=False)
            active_licenses = [l for l in all_licenses if l.is_active]
            total_licenses = len(active_licenses)
            
            logistics = {
                'active_containers': len(active_containers),
                'pending_arrival': pending_arrival,
                'total_licenses': total_licenses
            }

            # 3. DONNÉES DETTES EXTERNES (Réel)
            all_contacts = self.ext_contact_repo.get_all(session, limit=1000, include_inactive=False)
            total_customer_receivables = 0.0
            total_supplier_payables = 0.0
            
            for contact in all_contacts:
                balances = self.ext_trans_repo.get_all_balances(session, contact.id)
                for curr_id, balance in balances.items():
                    if balance > 0:
                        total_customer_receivables += balance
                    elif balance < 0:
                        total_supplier_payables += abs(balance)
            
            debts = {
                'customer_receivables': total_customer_receivables,
                'supplier_payables': total_supplier_payables
            }

            return {
                'real': {
                    'total_dzd': total_dzd,
                    'total_foreign_dzd': total_foreign_in_dzd,
                    'foreign_details': foreign_balances,
                    'recent_transactions': formatted_trans,
                    'trans_history': trans_history
                },
                'real_logistics': logistics,
                'real_debts': debts
            }
