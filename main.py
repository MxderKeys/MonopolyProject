import sys
import random
from PySide6.QtWidgets import (QApplication, QGraphicsView, QGraphicsScene, 
                               QGraphicsRectItem, QDialog, QVBoxLayout, QHBoxLayout, 
                               QLabel, QSpinBox, QPushButton, QMessageBox)
from PySide6.QtGui import QBrush, QColor
from PySide6.QtCore import Qt, QTimer


from player import Player, BotPlayer
from cells_classes import PropertyCell, StartCell, ChanceCell, RestCell, MoneyCell, KasinoCell, TrapCell
from map_config import cells_list
from game_map import GameMap

class GameSetupDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Настройка Монополии")
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout(self)

        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Живые игроки (люди):"))
        self.human_spin = QSpinBox()
        self.human_spin.setRange(1, 4)
        self.human_spin.setValue(1)
        h_layout.addWidget(self.human_spin)
        layout.addLayout(h_layout)

        b_layout = QHBoxLayout()
        b_layout.addWidget(QLabel("Компьютерные боты:"))
        self.bot_spin = QSpinBox()
        self.bot_spin.setRange(0, 4)
        self.bot_spin.setValue(3)
        b_layout.addWidget(self.bot_spin)
        layout.addLayout(b_layout)

        self.start_btn = QPushButton("НАЧАТЬ ИГРУ")
        self.start_btn.clicked.connect(self.check_and_start)
        layout.addWidget(self.start_btn)

    def check_and_start(self):
        total_players = self.human_spin.value() + self.bot_spin.value()
        if total_players < 2 or total_players > 4:
            QMessageBox.warning(self, "Ошибка", "Всего игроков должно быть от 2 до 4!")
        else:
            self.accept()

    def get_settings(self):
        return self.human_spin.value(), self.bot_spin.value()


class GameBoardView(QGraphicsView):
    def __init__(self, humans_count, bots_count):
        super().__init__()
        
        self.game_scene = QGraphicsScene(0, 0, 2400, 2000)
        self.setScene(self.game_scene)
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))

        self.setWindowTitle("Монополия")
        self.resize(850, 850)

        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.game_map = GameMap(0, 0)
        self.game_scene.addItem(self.game_map)
        self.game_map.setPos(630, 430)
        self.centerOn(self.game_map)

        self.players = []
        colors = [QColor("red"), QColor("blue"), QColor("green"), QColor("yellow")]
        color_idx = 0

        for i in range(humans_count):
            player = Player(f"Игрок {i+1}", colors[color_idx], 1000)
            player.player_id = color_idx
            self.players.append(player)
            color_idx += 1

        for i in range(bots_count):
            bot = BotPlayer(f"Бот {i+1}", colors[color_idx], 5000)
            bot.player_id = color_idx
            self.players.append(bot)
            color_idx += 1

        if self.game_map.cells:
            for p in self.players:
                self.game_scene.addItem(p.token)
                p.move_to_cell(self.game_map.cells[0], 0)

        self.current_player_index = 0
        self.has_rolled = False
        print(f"\n--- ИГРА НАЧАЛАСЬ. ХОД ИГРОКА: {self.players[0].name} ---")
        self.game_map.active_player = self.players[0]

        if isinstance(self.players[0], BotPlayer):
             QTimer.singleShot(1000, self.play_bot_turn)

    def next_turn(self):
        active_players = [p for p in self.players if not p.is_bankrupt]
        if len(active_players) == 1:
            winner = active_players[0]
            print(f"\n🏆 ИГРА ОКОНЧЕНА! ПОБЕДИТЕЛЬ: {winner.name} 🏆")
            QMessageBox.information(self, "Конец игры", f"Победил {winner.name}!\nОстальные игроки обанкротились.")
            return

        self.has_rolled = False
        
        while True:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            current = self.players[self.current_player_index]
            if not current.is_bankrupt:
                break
                
        self.game_map.active_player = current
        print(f"\n--- ХОД ИГРОКА: {current.name} ---")

        if isinstance(current, BotPlayer):
            QTimer.singleShot(1000, self.play_bot_turn)

    def play_bot_turn(self):
        current = self.players[self.current_player_index]
        self.game_map.roll_dice_and_move(current)
        
        if current.money < 0:
            current.declare_bankruptcy()
            
        QTimer.singleShot(1500, self.next_turn)

    def keyPressEvent(self, event):
        """Обработка клавиш живыми игроками"""
        if event.key() == Qt.Key_Escape:
            QApplication.quit()
            return

        current_player = self.players[self.current_player_index]

        if event.key() == Qt.Key_Space:
            if not isinstance(current_player, BotPlayer) and not self.has_rolled:
                self.game_map.roll_dice_and_move(current_player)
                self.has_rolled = True
                print("Нажмите ENTER, чтобы завершить ход.")
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if not isinstance(current_player, BotPlayer):
                if current_player.money < 0:
                    QMessageBox.critical(self, "Долги!", f"Ваш баланс отрицательный: ${current_player.money}!\nКликайте по своим участкам и закладывайте имущество, пока не выйдете в плюс.")
                    return
                
                if self.has_rolled and not self.game_map.is_dice_blocked:
                    self.next_turn()
                elif not self.has_rolled:
                    print("Сначала бросьте кубики (ПРОБЕЛ)!")
                elif self.game_map.is_dice_blocked:
                    print("Примите решение по участку!")
        else:
            super().keyPressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    setup_dialog = GameSetupDialog()
    
    if setup_dialog.exec():
        h_count, b_count = setup_dialog.get_settings()
        
        game_window = GameBoardView(h_count, b_count)
        game_window.showMaximized()
        
        sys.exit(app.exec())
    else:
        sys.exit()