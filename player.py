from PySide6.QtWidgets import QGraphicsEllipseItem
from PySide6.QtGui import QBrush, QColor
from PySide6.QtCore import Qt

from cells_classes import *

class Player:
    def __init__(self, name, color, start_money=5000):
        self.name = name
        self.money = start_money
        self.position = 0
        self.properties = []
        self.in_jail = False
        self.jail_turns = 0
        self.color = color

        self.token = QGraphicsEllipseItem(0, 0, 30, 30)
        self.token.setBrush(QBrush(QColor(color)))
        self.token.setPen(QColor(0, 0, 0))
        self.token.setZValue(4)

    def pay(self, amount):
        self.money -= amount
        print(f"[{self.name}] Заплатил ${amount}. Баланс: ${self.money}")
        if self.money < 0:
            print(f"[{self.name}] БАНКРОТ!")

    def receive(self, amount):
        self.money += amount
        print(f"[{self.name}] Получил ${amount}. Баланс: ${self.money}")

    def move_to_cell(self, cell, index):
        self.position = index
        rect = cell.sceneBoundingRect()
        center_x = rect.center().x()
        center_y = rect.center().y()

        self.token.setPos(center_x - 15, center_y - 15)


class BotPlayer(Player):
    def __init__(self, name, color, start_money=5000):
        super().__init__(name, color, start_money)

    def buy_decision(self, cell):
        if self.money - cell.property_price >= 200:
            return True
        return False

    def find_money(self, required_amount):
        print(f"🤖 БОТ [{self.name}] ищет ${required_amount}...")
        return False