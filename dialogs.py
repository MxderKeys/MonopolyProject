
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QMessageBox
from PySide6.QtGui import QBrush, QColor, QFont, QPen, QTextOption
from PySide6.QtCore import Qt, QTimer

from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QSpinBox

import random

from cell import Cell
from player import BotPlayer

class AuctionDialog(QDialog):
    def __init__(self, property_cell, players, on_finish_callback, current_id):
        super().__init__()
        self.setWindowTitle(f"Аукцион: {property_cell.property_name}")
        self.cell = property_cell
        self.on_finish_callback = on_finish_callback
        
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        
        # Список тех, кто ВСЁ ЕЩЁ участвует в торгах (изначально все живые)
        self.auction_players = [p for p in players if not p.is_bankrupt]
        
        self.current_bid = 0
        self.current_winner = None
        self.active_index = current_id
        
        layout = QVBoxLayout(self)
        
        self.info_label = QLabel()
        layout.addWidget(self.info_label)
        
        self.bid_input = QSpinBox()
        self.bid_input.setRange(1, 10000)
        layout.addWidget(self.bid_input)
        
        self.bid_btn = QPushButton("Сделать ставку")
        self.bid_btn.clicked.connect(self.place_bid)
        layout.addWidget(self.bid_btn)
        
        self.canc_btn = QPushButton("Пас / Сдаться")
        self.canc_btn.clicked.connect(self.canc_bid)
        layout.addWidget(self.canc_btn)
        
        # Инициализируем стартовое состояние UI
        self.check_auction_state()
        
        # Таймер для автоматических ходов ботов
        self.bot_timer = QTimer()
        self.bot_timer.timeout.connect(self.bot_turn)
        self.bot_timer.start(1000)

    def check_auction_state(self):
        # Сценарий 1: Все пасанули, ставок не было
        if len(self.auction_players) == 0:
            print("Все игроки пасанули. Участок остаётся у банка.")
            self.current_winner = None
            self.finish()
            return
            
        # Сценарий 2: Остался всего один игрок
        if len(self.auction_players) == 1:
            if not self.current_winner:
                self.current_winner = self.auction_players[0]
                self.current_bid = self.cell.property_price // 2
            self.finish()
            return
            
        if self.active_index >= len(self.auction_players):
            self.active_index = 0
            
        current_p = self.auction_players[self.active_index]
        
        leader_info = f"Лидер: {self.current_winner.name} (${self.current_bid})" if self.current_winner else "Ставок пока нет"
        self.info_label.setText(f"=== {leader_info} ===\n\nСейчас принимает решение: {current_p.name}\nБаланс игрока: ${current_p.money}")
        
        self.bid_input.setValue(self.current_bid + 10)
        
        is_human = not isinstance(current_p, BotPlayer)
        self.bid_btn.setEnabled(is_human)
        self.bid_input.setEnabled(is_human)
        
        self.canc_btn.setEnabled(is_human and current_p != self.current_winner)

    def place_bid(self):
        bid = self.bid_input.value()
        player = self.auction_players[self.active_index]
        
        if bid > self.current_bid and player.money >= bid:
            self.current_bid = bid
            self.current_winner = player
            print(f"👤 {player.name} поднял ставку до ${bid}")
            self.advance_turn()
        else:
            QMessageBox.warning(self, "Ошибка", "Ставка должна быть выше текущей, и у вас должно хватать денег!")

    def canc_bid(self):
        player = self.auction_players[self.active_index]
        print(f"🏳️ {player.name} пасует и выбывает из аукциона.")
        
        self.auction_players.remove(player)
        
        self.check_auction_state()

    def bot_turn(self):
        if not self.auction_players:
            return
            
        player = self.auction_players[self.active_index]
        
        if isinstance(player, BotPlayer):
            if player == self.current_winner:
                self.advance_turn()
                return
                
            # Расчет желаемой ставки бота (+10% от текущей + шаг)
            bot_bid = int(self.current_bid * 1.1) + 10
            if bot_bid < self.cell.property_price // 2:
                bot_bid = self.cell.property_price // 2 # Начинаем со стартовой цены
                
            if bot_bid <= 3 * self.cell.property_price and bot_bid <= (player.money * 0.40):
                self.current_bid = bot_bid
                self.current_winner = player
                print(f"Бот {player.name} ставит ${bot_bid}")
                self.advance_turn()
            else:
                print(f"Бот {player.name} решил пасовать.")
                self.auction_players.remove(player)
                self.check_auction_state()

    def advance_turn(self):
        if self.auction_players:
            self.active_index = (self.active_index + 1) % len(self.auction_players)
        self.check_auction_state()

    def finish(self):
        self.bot_timer.stop()
        
        if self.current_winner:
            print(f"АУКЦИОН ЗАВЕРШЕН! Участок {self.cell.property_name} уходит к {self.current_winner.name} за ${self.current_bid}")
            self.current_winner.pay(self.current_bid)
            self.cell.owner = self.current_winner
            self.cell.value_text.setPlainText(str(self.cell.rent_list[0]))
            self.current_winner.properties.append(self.cell)
            
            tint = QColor(self.current_winner.color)
            tint.setAlpha(80)
            self.cell.owner_tint.setBrush(QBrush(tint))
            
        self.on_finish_callback()
        self.close()
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            print("Клавиша Escape заблокирована в этом окне!")
            event.ignore()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if not self.is_resolved:
            print("АЛЁ!!! Куда закрываешь?")
            event.ignore()
        else:
            super().closeEvent(event)
        
        
class BuyDialog(QDialog):
    def __init__(self, property_cell, player, unlock_callback, player_list):
        super().__init__()
        self.setWindowTitle("Покупка участка")
        self.setModal(False)
        self.setFixedSize(300, 150)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        self.cell = property_cell
        self.player = player
        self.unlock_callback = unlock_callback
        self.player_list = player_list

        self.is_resolved = False
        
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
            self.cell.value_text.setPlainText(str(self.cell.rent_list[0]))
            self.player.properties.append(self.cell)

            tint_color = QColor(self.player.color)
            tint_color.setAlpha(80)
            self.cell.owner_tint.setBrush(QBrush(tint_color))

            print(f"[{self.player.name}] Купил участок!")
            self.is_resolved = True
            self.unlock_callback() 
            self.close()
        else:
            print("Всё ещё не хватает денег! Продайте что-нибудь на поле.")
            self.update_balance()

    def go_auction(self):
        print("Аукцион начинается!")
        self.auction_window = AuctionDialog(self.cell, self.player_list, self.unlock_callback, self.player.player_id)
        self.auction_window.show()
        self.is_resolved = True 
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            print("Клавиша Escape заблокирована в этом окне!")
            event.ignore()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if not self.is_resolved:
            print("АЛЁ!!! Куда закрываешь?")
            event.ignore()
        else:
            super().closeEvent(event)
            
            

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
        
        if self.cell.owner is not None and self.cell.owner == self.player and not isinstance(self.player, BotPlayer):
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