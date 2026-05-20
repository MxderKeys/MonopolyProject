from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PySide6.QtGui import QBrush, QColor, QFont, QPen
from PySide6.QtCore import Qt

class PlayerProfile(QGraphicsRectItem):
    def __init__(self, player, width=220, height=85):
        super().__init__(0, 0, width, height)
        self.player = player
        self.setZValue(6)
        
        self.setBrush(QBrush(QColor(240, 240, 240)))
        self.setPen(QPen(Qt.black, 2))
        
        self.header = QGraphicsRectItem(0, 0, width, 35, self)
        tint = QColor(player.color)
        tint.setAlpha(150)
        self.header.setBrush(QBrush(tint))
        self.header.setPen(Qt.NoPen)
        
        self.name_text = QGraphicsTextItem(player.name, self)
        self.name_text.setFont(QFont("Arial", 12, QFont.Bold))
        self.name_text.setDefaultTextColor(Qt.black)
        self.name_text.setPos(10, 5)
        
        self.balance_text = QGraphicsTextItem("", self)
        self.balance_text.setFont(QFont("Arial", 16, QFont.Bold))
        self.balance_text.setDefaultTextColor(QColor(0, 100, 0))
        self.balance_text.setPos(10, 45)
        
        self.update_balance()

    def update_balance(self):
        """Метод вызывается при любом изменении денег или банкротстве"""
        if self.player.is_bankrupt:
            self.balance_text.setPlainText("БАНКРОТ")
            self.balance_text.setDefaultTextColor(Qt.red)
            self.setOpacity(0.4)
        else:
            self.balance_text.setPlainText(f"Баланс: ${self.player.money}")


class DiceUI(QGraphicsTextItem):
    def __init__(self):
        super().__init__("Ожидание броска...")
        self.setFont(QFont("Arial", 24, QFont.Bold))
        self.setDefaultTextColor(Qt.white)
        
        # Добавляем темный полупрозрачный фон для текста, чтобы читалось на любом фоне
        bg = QGraphicsRectItem(-20, -10, 250, 60, self)
        bg.setBrush(QBrush(QColor(0, 0, 0, 150)))
        bg.setPen(Qt.NoPen)
        bg.setZValue(-1)

    def show_roll(self, d1, d2):
        self.setPlainText(f"🎲 {d1}    🎲 {d2}   (Ход: {d1+d2})")