from PySide6.QtWidgets import QGraphicsEllipseItem
from PySide6.QtGui import QBrush, QColor
from PySide6.QtCore import Qt

class Player:
    def __init__(self, name, color, start_money=5000):
        self.player_id = 0
        self.name = name
        self.money = start_money
        self.position = 0
        self.properties = []
        self.jail_turns = 0
        self.color = color

        self.in_jail = False
        self.is_bankrupt = False

        self.token = QGraphicsEllipseItem(0, 0, 30, 30)
        self.token.setBrush(QBrush(QColor(color)))
        self.token.setPen(QColor(0, 0, 0))
        self.token.setZValue(4)

    def get_total_assets_value(self):
        total = self.money
        for prop in self.properties:
            if not getattr(prop, 'is_mortgaged', False):
                total += prop.property_price // 2
            if getattr(prop, 'buildings_level', 0) > 0:
                total += (prop.buildings_level * getattr(prop, 'building_price', 50)) // 2
        return total

    def declare_bankruptcy(self, creditor=None):
        self.is_bankrupt = True
        print(f"[{self.name}] ОБЪЯВЛЯЕТ БАНКРОТСТВО И ВЫБЫВАЕТ ИЗ ИГРЫ!")
        
        if creditor:
            payout = self.get_total_assets_value() // 2
            if payout > 0:
                print(f"Крассавчик жи есть [{creditor.name}] получает 50% активов банкрота: ${payout}")
                creditor.receive(payout)

        for prop in self.properties:
            prop.owner = None
            prop.is_mortgaged = False
            if hasattr(prop, 'buildings_level'):
                prop.buildings_level = 0
            prop.setOpacity(1.0)
            prop.setBrush(QBrush())
            
        self.properties.clear()
        self.token.hide()
        
        if hasattr(self, 'profile_ui'):
            self.profile_ui.update_balance()

    def pay_or_bankrupt(self, amount, creditor=None):
        """Универсальный метод попытки оплаты"""
        total_assets = self.get_total_assets_value()
        
        if total_assets < amount:
            print(f"[{self.name}] не может заплатить ${amount}! Его активы всего ${total_assets}")
            self.declare_bankruptcy(creditor)
            return False 
            
        if self.money < amount:
            if hasattr(self, 'find_money'): 
                self.find_money(amount)

        self.pay(amount)
        if creditor:
            creditor.receive(amount)
            
        return True

    def move_to_cell(self, cell, index):
        self.position = index
        rect = cell.sceneBoundingRect()
        cx = rect.center().x()
        cy = rect.center().y()
        offsets = [
            (-30, -30),
            (0, -30),
            (-30, 0),
            (0, 0)
        ]
        ox, oy = offsets[self.player_id % 4]
        self.token.setPos(cx + ox, cy + oy)
        
    def receive(self, amount):
        self.money += amount
        if hasattr(self, 'profile_ui'):
            self.profile_ui.update_balance()

    def pay(self, amount):
        self.money -= amount
        if hasattr(self, 'profile_ui'):
            self.profile_ui.update_balance()


class BotPlayer(Player):
    def __init__(self, name, color, start_money=5000):
        super().__init__(name, color, start_money)

    def buy_decision(self, cell):
        if self.money - cell.property_price >= 200:
            return True
        return False

    def find_money(self, required_amount):
        print(f"БОТ [{self.name}] срочно ищет ${required_amount}...")
        
        unmortgaged_props = [p for p in self.properties if not p.is_mortgaged]
        unmortgaged_props.sort(key=lambda x: x.property_price)
        
        for prop in unmortgaged_props:
            if self.money >= required_amount:
                break
                
            prop.is_mortgaged = True
            prop.setOpacity(0.5)
            received = prop.property_price // 2
            self.receive(received)
            print(f"БОТ заложил {prop.property_name} и получил ${received}")