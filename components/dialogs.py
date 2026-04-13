"""
Dialogs réutilisables pour l'application
Version améliorée avec ErrorDialog professionnel
"""
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout,
    QLabel, QMessageBox, QWidget, QPushButton, QComboBox, QCompleter
)
from PyQt6.QtCore import Qt


def setup_combo(combo: QComboBox, placeholder: str = "Rechercher..."):
    """
    Configure un QComboBox de manière unifiée : éditable, avec complétion et filtrage.
    [TREE SYSTEM] — Changement centralisé → affecte tous les modules automatiquement.

    Args:
        combo: Le QComboBox à configurer
        placeholder: Texte d'invite
    """
    combo.setEditable(True)
    combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
    combo.lineEdit().setPlaceholderText(placeholder)

    # Compléter avec filtrage
    completer = QCompleter(combo.model())
    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    completer.setFilterMode(Qt.MatchFlag.MatchContains)
    completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
    combo.setCompleter(completer)


def create_quick_add_layout(combo, callback):
    """
    Crée un layout horizontal avec un ComboBox et un bouton (+) pour l'ajout rapide.
    [TREE SYSTEM] — Utilise setup_combo() pour unifier le comportement des combos.

    Args:
        combo: Le QComboBox à inclure
        callback: La fonction à appeler lors du clic sur (+)

    Returns:
        QWidget: Un widget contenant le layout combo + bouton
    """
    # [TREE] 2026-04-04 - Unification des combos via setup_combo()
    setup_combo(combo)

    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(5)

    btn = QPushButton()
    from utils.icon_manager import IconManager
    btn.setIcon(IconManager.get_icon("plus", color="#ffffff", size=18))
    btn.setFixedWidth(30)
    btn.setToolTip("Ajouter un nouvel élément")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet("""
        QPushButton {
            font-weight: bold;
            font-size: 16px;
            background-color: #2ea043;
            border: 1px solid #238636;
            border-radius: 4px;
            color: #ffffff;
        }
        QPushButton:hover {
            background-color: #2c974b;
        }
        QPushButton:pressed {
            background-color: #238636;
        }
    """)
    btn.clicked.connect(callback)

    layout.addWidget(combo)
    layout.addWidget(btn)

    return container


class ConfirmDialog(QDialog):
    """Dialog de confirmation personnalisé"""

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self._setup_ui(message)

    def _setup_ui(self, message: str):
        """Configure l'interface"""
        from core.themes import get_active_colors
        c = get_active_colors()
        self.setStyleSheet(f"""
            QDialog {{ background-color: {c['bg_main']}; }}
            QLabel {{ color: {c['text_main']}; }}
            QPushButton {{
                background-color: {c['accent']}; color: #ffffff;
                border: none; padding: 6px 16px; border-radius: 4px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {c['accent_hover']}; }}
        """)
        layout = QVBoxLayout(self)

        # Message
        label = QLabel(message)
        label.setWordWrap(True)
        layout.addWidget(label)

        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes |
            QDialogButtonBox.StandardButton.No
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        # Traduire les boutons en français
        buttons.button(QDialogButtonBox.StandardButton.Yes).setText("Oui")
        buttons.button(QDialogButtonBox.StandardButton.No).setText("Non")

        layout.addWidget(buttons)

        self.setMinimumWidth(400)


def show_error(parent: QWidget, title: str, message: str, exception=None):
    """
    Affiche un message d'erreur avec détails optionnels.

    Args:
        parent: Widget parent
        title: Titre du dialog
        message: Message d'erreur
        exception: Exception optionnelle pour afficher les détails
    """
    # Utiliser le nouvel ErrorDialog professionnel si une exception est fournie
    if exception is not None:
        from components.error_dialog import ErrorDialog
        import traceback
        details = traceback.format_exc()
        dialog = ErrorDialog(
            parent=parent,
            title=title,
            message=message,
            details=details,
            error_type="error"
        )
        dialog.exec()
    else:
        # Utiliser le QMessageBox simple pour la compatibilité
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.button(QMessageBox.StandardButton.Ok).setText("OK")
        msg.exec()


def show_success(parent: QWidget, title: str, message: str):
    """
    Affiche un message de succès.

    Args:
        parent: Widget parent
        title: Titre du dialog
        message: Message de succès
    """
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.button(QMessageBox.StandardButton.Ok).setText("OK")
    msg.exec()


def show_warning(parent: QWidget, title: str, message: str):
    """
    Affiche un message d'avertissement.

    Args:
        parent: Widget parent
        title: Titre du dialog
        message: Message d'avertissement
    """
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.button(QMessageBox.StandardButton.Ok).setText("OK")
    msg.exec()


def confirm_action(parent: QWidget, title: str, message: str) -> bool:
    """
    Demande confirmation pour une action.

    Args:
        parent: Widget parent
        title: Titre du dialog
        message: Message de confirmation

    Returns:
        True si confirmé, False sinon
    """
    dialog = ConfirmDialog(title, message, parent)
    return dialog.exec() == QDialog.DialogCode.Accepted


def confirm_delete(parent: QWidget, item_name: str = "cet élément") -> bool:
    """
    Demande confirmation pour une suppression.

    Args:
        parent: Widget parent
        item_name: Nom de l'élément à supprimer

    Returns:
        True si confirmé, False sinon
    """
    return confirm_action(
        parent,
        "Confirmer la suppression",
        f"Êtes-vous sûr de vouloir supprimer {item_name} ?\n\n"
        "Cette action ne peut pas être annulée."
    )
