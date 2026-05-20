from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QMessageBox
from PySide6.QtGui import QBrush, QColor, QFont, QPen, QTextOption
from PySide6.QtCore import Qt

from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel

import random

from cell import Cell
from player import BotPlayer

GROUP_COLORS = {
    "КОФЕЙНИ": QColor(150, 75, 0),             #Коричневая
    "РЕСТОРАНЫ": QColor(0, 0, 255),            #Синяя
    "МЕБЕЛЬ": QColor(255, 0, 0),               #Красная
    "АВТОБРЕНДЫ": QColor(255, 255, 0),         #Желтая
    "ВИДЕОХОСТИНГИ": QColor(128, 0, 128),      #Фиолетовая
    "МАГАЗИНЫ ОДЕЖДЫ": QColor(255, 165, 0),    #Оранжевая
    "СЫРЬЕВЫЕ РЕСУРСЫ": QColor(128, 128, 128), #Серая
    "ЭНЕРГЕТИКИ": QColor(0, 255, 255),         #Голубая
}


class PropertyCell(Cell):
    def __init__(self, property_name, property_price, x, y, width=80, height=180, cell_group=None, rent_list=None, building_price=50, rotation_angle=0):
        super().__init__(x, y, width, height, rotation_angle)
        self.property_name = property_name
        self.property_price = int(property_price)
        self.cell_group = cell_group

        self.owner = None
        self.is_mortgaged = False
        self.buildings_level = 0

        self.rent_list = rent_list if rent_list else [10, 50, 150, 450, 625, 750]
        self.building_price = building_price

        self.setPos(x, y)

        value_font = QFont("Arial", 12)
        value_font.setBold(True)

        name_font = QFont("Arial", 14)
        name_font.setBold(True)

        self.color_rect = QGraphicsRectItem(5, 5, width - 10, 30, self)
        self.color_rect.setBrush(QBrush(GROUP_COLORS.get(cell_group, QColor(0, 0, 0)))) 
        self.color_rect.setPen(QColor(0, 0, 0))

        option = QTextOption()
        option = QTextOption(Qt.AlignmentFlag.AlignCenter)

        self.name_text = QGraphicsTextItem(property_name, self)
        self.name_text.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.name_text.setFont(name_font)
        self.name_text.setDefaultTextColor(Qt.black)
        if rotation_angle == 270:
            self.name_text.setRotation(90)
            self.name_text.setPos(54, 40)
        else:
            self.name_text.setRotation(-90)
            self.name_text.setPos(28, 170)
        self.name_text.setTextWidth(height - 50)
        self.name_text.document().setDefaultTextOption(option)

        self.value_text = QGraphicsTextItem(property_price, self)
        self.value_text.setFont(value_font)
        self.value_text.setDefaultTextColor(Qt.white)
        self.value_text.setPos(5, 8)
        self.value_text.setTextWidth(width - 10)
        self.value_text.document().setDefaultTextOption(option)
        self.value_text.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

    def on_player_step(self, player, game_map):
        print(f"Игрок {player.name} наступил на {self.property_name}")
        if self.owner is None:
            # === ПРОВЕРКА НА БОТА ===
            if isinstance(player, BotPlayer):
                if player.wants_to_buy(self):
                    player.pay(self.property_price)
                    self.owner = player
                    player.properties.append(self)
                    
                    from PySide6.QtGui import QPen, QColor
                    pen = QPen(QColor(player.color))
                    pen.setWidth(4)
                    self.color_rect.setPen(pen)
                    print(f"[{player.name}] купил {self.property_name}!")
                else:
                    print(f"[{player.name}] отказался от покупки. Аукцион!")
                    
            else:
                game_map.is_dice_blocked = True 
                self.buy_window = BuyDialog(self, player, game_map.unlock_dice)
                self.buy_window.show()

        elif self.owner != player:
            if not self.is_mortgaged and not self.owner.in_jail:
                rent_amount = self.rent_list[self.buildings_level]
                print(f"-> {player.name} платит ренту ${rent_amount} игроку {self.owner.name}")

                if player.money < rent_amount:
                    if isinstance(player, BotPlayer):
                        # Бот пытается найти деньги сам
                        player.find_money(rent_amount)
                    else:
                        game_map.is_dice_blocked = True 
                        self.buy_window = BuyDialog(self, player, game_map.unlock_dice)
                        self.buy_window.show()

                player.pay(rent_amount)
                self.owner.receive(rent_amount)
            else:
                print(f"{self.owner} сосёт бибу. Территория в залоге и никто ему ничего не должен!")


    def show_info(self):
        self.info_window = PropertyInfoDialog(self, self.owner)
        self.info_window.show()


class StartCell(Cell):
    def __init__(self, x, y, prize=300, width=180, height=180):
        super().__init__(x, y, width, height)
        self.name = "Старт"

        self.setPos(x, y)
        font = QFont("Arial", 12)
        font.setBold(True)

        option = QTextOption()
        option = QTextOption(Qt.AlignmentFlag.AlignCenter)

        self.name_text = QGraphicsTextItem(self.name, self)
        self.name_text.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.name_text.setFont(font)
        self.name_text.setDefaultTextColor(Qt.black)
        self.name_text.setPos(10, 10)
        self.name_text.setTextWidth(width - 20)
        self.name_text.document().setDefaultTextOption(option)

        self.value_text = QGraphicsTextItem(f"Ваша награда: {str(prize)}", self)
        self.value_text.setFont(font)
        self.value_text.setDefaultTextColor(Qt.black)
        self.value_text.setPos(10, 120)
        self.value_text.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.value_text.setTextWidth(width - 20)
        self.value_text.document().setDefaultTextOption(option)

    def on_player_step(self, player, game_map):
        print(f"{player.name} наступил на старт и получает ${self.prize * 2}!")
        player.receive(int(self.value_text.toPlainText().split()[-1]))

    def show_info(self):
        print(f"Открываем красивое окно с информацией об улице")


class ChanceCell(Cell):
    def __init__(self, x, y, width=80, height=180, coefficient=0, rotation_angle=0):
        super().__init__(x, y, width, height, rotation_angle)
        self.name = "?"
        self.coefficient = coefficient

        self.setPos(x, y)
        font = QFont("Arial", 50)
        font.setBold(True)

        self.color_rect = QGraphicsRectItem(5, 5, width - 10, 30, self)
        self.color_rect.setBrush(QBrush(QColor(155, 155, 155))) 
        self.color_rect.setPen(QColor(0, 0, 0))

        option = QTextOption()
        option = QTextOption(Qt.AlignmentFlag.AlignCenter)

        self.name_text = QGraphicsTextItem(self.name, self)
        self.name_text.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.name_text.setFont(font)
        self.name_text.setDefaultTextColor(Qt.black)
        self.name_text.setPos(10, 60)
        self.name_text.setTextWidth(width - 20)
        self.name_text.document().setDefaultTextOption(option)

    def on_player_step(self, player, game_map):
        outcome = random.choice([-10, 10, 50, -50, 20, -20, 100, 60])
        outcome = int(outcome * self.coefficient)

        if outcome > 0:
            print(f"{player.name} нашёл на полу ${outcome}")
            player.receive(outcome)
        else:
            print(f"{player.name}-лошара! У него из кармана выпало ${abs(outcome)}")
            player.pay(abs(outcome))

    def show_info(self):
        print(f"Открываем красивое окно с информацией об улице")


class MoneyCell(Cell):
    def __init__(self, x, y, width=80, height=180, coefficient=0, rotation_angle=0):
        super().__init__(x, y, width, height, rotation_angle)
        self.name = f"$"
        self.coefficient = coefficient

        self.setPos(x, y)
        font = QFont("Arial", 50)
        font.setBold(True)

        self.color_rect = QGraphicsRectItem(5, 5, width - 10, 30, self)
        self.color_rect.setBrush(QBrush(QColor(50, 200, 50))) 
        self.color_rect.setPen(QColor(0, 0, 0))

        option = QTextOption()
        option = QTextOption(Qt.AlignmentFlag.AlignCenter)

        self.name_text = QGraphicsTextItem(self.name, self)
        self.name_text.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.name_text.setFont(font)
        self.name_text.setDefaultTextColor(Qt.black)
        self.name_text.setPos(10, 60)
        self.name_text.setTextWidth(width - 20)
        self.name_text.document().setDefaultTextOption(option)

    def on_player_step(self, player, game_map):
        outcome = random.choice([200, 10, 50, 100, 20, 500])
        outcome *= self.coefficient

        print(f"Таинственный дядя скинул {player.name} целых ${outcome}!!!!")
        player.receive(int(outcome))

    def show_info(self):
        print(f"Открываем красивое окно с информацией об улице")


class RestCell(Cell):
    def __init__(self, x, y, width=180, height=180):
        super().__init__(x, y, width, height)
        self.name = "ОТДЫХ\nНУ ИЛИ ТЮРЬМА"

        self.setPos(x, y)
        font = QFont("Arial", 12)
        font.setBold(True)

        option = QTextOption()
        option = QTextOption(Qt.AlignmentFlag.AlignCenter)

        self.name_text = QGraphicsTextItem(self.name, self)
        self.name_text.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.name_text.setFont(font)
        self.name_text.setDefaultTextColor(Qt.black)
        self.name_text.setPos(10, 80)
        self.name_text.setTextWidth(width - 20)
        self.name_text.document().setDefaultTextOption(option)

    def on_player_step(self, player, game_map):
        print(f"{player.name} высматривает в камерах своих конкурентов. Чтож.")

    def show_info(self):
        print(f"Открываем красивое окно с информацией об улицe")


class KasinoCell(Cell):
    def __init__(self, x, y, width=180, height=180):
        super().__init__(x, y, width, height)
        self.name = "КАЗИНО"

        self.setPos(x, y)
        font = QFont("Arial", 20)
        font.setBold(True)

        option = QTextOption()
        option = QTextOption(Qt.AlignmentFlag.AlignCenter)

        self.name_text = QGraphicsTextItem(self.name, self)
        self.name_text.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.name_text.setFont(font)
        self.name_text.setDefaultTextColor(Qt.black)
        self.name_text.setPos(10, 80)
        self.name_text.setTextWidth(width - 20)
        self.name_text.document().setDefaultTextOption(option)

    def on_player_step(self, player, game_map):
        outcome = random.choice([-300, -200, -100, 600])
        if outcome > 0:
            print(f"Джекпот! {player.name} выиграл в казино ${outcome}")
            player.receive(outcome)
        else:
            print(f"Неудача. {player.name} проиграл в казино ${abs(outcome)}")
            player.pay(abs(outcome))

    def show_info(self):
        print(f"Открываем красивое окно казино")


class TrapCell(Cell):
    def __init__(self, x, y, jail_index, width=180, height=180):
        super().__init__(x, y, width, height)
        self.name = "ЛОВУШКА"

        self.jail_index = jail_index

        self.setPos(x, y)
        font = QFont("Arial", 20)
        font.setBold(True)

        option = QTextOption()
        option = QTextOption(Qt.AlignmentFlag.AlignCenter)

        self.name_text = QGraphicsTextItem(self.name, self)
        self.name_text.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.name_text.setFont(font)
        self.name_text.setDefaultTextColor(Qt.black)
        self.name_text.setPos(10, 80)
        self.name_text.setTextWidth(width - 20)
        self.name_text.document().setDefaultTextOption(option)

    def on_player_step(self, player, game_map):
        print(f"{player.name} попал в ловушку! Отправляется в тюрьму.")
        player.in_jail = True
        player.jail_turns = 3 # Сидеть 3 хода
        return {"teleport_to": self.jail_index}

    def show_info(self):
        print(f"Открываем красивое окно с информацией о ловушке")


class PropertyInfoDialog(QDialog):
    def __init__(self, property_cell, player=None):
        super().__init__()
        self.setWindowTitle(f"Информация: {property_cell.property_name}")

        self.setModal(False) 
        self.cell = property_cell
        self.player = player
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Цена: ${self.cell.property_price}"))
        
        status = "Свободен" if not self.cell.owner else f"Владелец: {self.cell.owner.name}"
        if self.cell.is_mortgaged:
            status += " (В ЗАЛОГЕ)"
        layout.addWidget(QLabel(f"Статус: {status}"))
        
        if self.cell.owner == self.player:
            if not self.cell.is_mortgaged:
                self.mortgage_btn = QPushButton("Заложить (получить 50%)")
                self.mortgage_btn.clicked.connect(self.mortgage)
                layout.addWidget(self.mortgage_btn)
            else:
                self.unmortgage_btn = QPushButton("Выкупить из залога")
                self.unmortgage_btn.clicked.connect(self.unmortgage)
                layout.addWidget(self.unmortgage_btn)

    def mortgage(self):
        self.cell.is_mortgaged = True
        self.cell.setOpacity(0.5)
        self.player.receive(self.cell.property_price // 2)
        self.close()

    def unmortgage(self):
        cost = (self.cell.property_price // 2)
        if self.player.money >= cost:
            self.player.pay(cost)
            self.cell.is_mortgaged = False
            self.cell.setOpacity(1.0)
            self.close()
        else:
            print("Не хватает денег для выкупа!")


class BuyDialog(QDialog):
    def __init__(self, property_cell, player, unlock_callback):
        super().__init__()
        self.setWindowTitle("Покупка участка")
        self.setModal(False)
        
        self.cell = property_cell
        self.player = player
        self.unlock_callback = unlock_callback
        
        layout = QVBoxLayout(self)
        
        self.balance_label = QLabel(f"Ваш баланс: ${self.player.money}")
        layout.addWidget(QLabel(f"Участок: {self.cell.property_name}\nЦена: ${self.cell.property_price}"))
        layout.addWidget(self.balance_label)
        
        self.buy_btn = QPushButton("Купить")
        self.buy_btn.clicked.connect(self.try_buy)
        layout.addWidget(self.buy_btn)
        
        self.auction_btn = QPushButton("Аукцион")
        self.auction_btn.clicked.connect(self.go_auction)
        layout.addWidget(self.auction_btn)

    def update_balance(self):
        self.balance_label.setText(f"Ваш баланс: ${self.player.money}")

    def try_buy(self):
        if self.player.money >= self.cell.property_price:
            self.player.pay(self.cell.property_price)
            self.cell.owner = self.player
            self.player.properties.append(self.cell)
            
            pen = QPen(QColor(self.player.color))
            pen.setWidth(4)
            self.cell.color_rect.setPen(pen)
            
            print(f"[{self.player.name}] Купил участок!")
            self.unlock_callback() 
            self.close()
        else:
            print("Всё ещё не хватает денег! Продайте что-нибудь на поле.")
            self.update_balance()

    def go_auction(self):
        print("Отправляем на аукцион!")
        self.unlock_callback()
        self.close()