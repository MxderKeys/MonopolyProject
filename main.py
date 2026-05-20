import sys
import random
from PySide6.QtWidgets import (QApplication, QGraphicsView, QGraphicsScene, 
                               QGraphicsRectItem, QDialog, QVBoxLayout, QHBoxLayout, 
                               QLabel, QSpinBox, QPushButton, QMessageBox)
from PySide6.QtGui import QBrush, QColor
from PySide6.QtCore import Qt, QTimer

# Импортируем классы из ваших соседних файлов
from player import Player, BotPlayer
from cells_classes import PropertyCell, StartCell, ChanceCell, RestCell, MoneyCell, KasinoCell, TrapCell
from map_config import cells_list


# ==========================================
# 1. СТАРТОВОЕ МЕНЮ (ЛОББИ)
# ==========================================
class GameSetupDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Настройка Монополии")
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout(self)

        # Поле для выбора живых игроков
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Живые игроки (люди):"))
        self.human_spin = QSpinBox()
        self.human_spin.setRange(0, 4)
        self.human_spin.setValue(1) # По умолчанию 1 человек
        h_layout.addWidget(self.human_spin)
        layout.addLayout(h_layout)

        # Поле для выбора ботов
        b_layout = QHBoxLayout()
        b_layout.addWidget(QLabel("Компьютерные боты:"))
        self.bot_spin = QSpinBox()
        self.bot_spin.setRange(0, 4)
        self.bot_spin.setValue(3) # По умолчанию 3 бота
        b_layout.addWidget(self.bot_spin)
        layout.addLayout(b_layout)

        # Кнопка старта
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


# ==========================================
# 2. ИГРОВАЯ КАРТА И ЛОГИКА ПЕРЕМЕЩЕНИЯ
# ==========================================
class GameMap(QGraphicsRectItem):
    def __init__(self, x, y, width=1140, height=1140):
        super().__init__(x, y, width, height)
        
        self.setBrush(QBrush(QColor(200, 200, 200)))  # Светло-серый фон
        self.setPen(QColor(0, 0, 0))  # Черная рамка
        self.setZValue(1)

        self.cells = []
        self.properties = []
        
        # Флаг Паттерна Состояний (Блокировка кубиков)
        self.is_dice_blocked = False 

        self.create_game_map()

    def unlock_dice(self):
        """Метод разблокировки, который вызывается из окон покупки"""
        self.is_dice_blocked = False
        print("Действие завершено! Кубики разблокированы.")

    def create_game_map(self):
        first_width = 180
        width = 80
        space = 5
        margin = 5
        jail_index = 10 # По умолчанию индекс тюрьмы

        for k in range(4):
            angle = k * 90
            for i in range(len(cells_list[k])):
                if k == 0:
                    new_x = self.rect().x() + first_width + space + (i - 1) * (width + space) + margin
                    new_y = self.rect().y() + margin
                elif k == 1:
                    new_x = self.rect().x() + first_width + space + (len(cells_list[0]) - 2) * (width + space) + margin + first_width
                    new_y = self.rect().y() + first_width + space + (i - 1) * (width + space) + margin + width + space
                elif k == 2:
                    new_x = self.rect().x() + first_width + space + (len(cells_list[0]) - 2 - i) * (width + space) + margin
                    new_y = self.rect().y() + first_width + space + (len(cells_list[2]) - 3) * (width + space) + margin + width + space
                elif k == 3:
                    new_x = self.rect().x() + margin
                    new_y = self.rect().y() + first_width + space + (len(cells_list[1]) - i - 1) * (width + space) + margin + width

                cell_info = cells_list[k][i]
                if cell_info[0] == "start":
                    tmp_cell = StartCell(self.rect().x() + margin, self.rect().y() + margin)
                    tmp_cell.setParentItem(self)
                elif cell_info[0] == "property":
                    tmp_cell = PropertyCell(cell_info[2], cell_info[3], new_x, new_y, cell_group=cell_info[1], rotation_angle=angle)
                    tmp_cell.setParentItem(self)
                    self.properties.append(tmp_cell)
                elif cell_info[0] == "chance":
                    tmp_cell = ChanceCell(new_x, new_y, rotation_angle=angle)
                    tmp_cell.setParentItem(self)
                elif cell_info[0] == "rest":
                    tmp_cell = RestCell(new_x, new_y)
                    tmp_cell.setParentItem(self)
                    jail_index = len(self.cells) # Запоминаем индекс тюрьмы
                elif cell_info[0] == "money":
                    tmp_cell = MoneyCell(new_x, new_y, coefficient=cell_info[1], rotation_angle=angle)
                    tmp_cell.setParentItem(self)
                elif cell_info[0] == "kasino":
                    tmp_cell = KasinoCell(self.rect().x() + first_width + space + (len(cells_list[0]) - 2) * (width + space) + margin, self.rect().y() + first_width + space + (len(cells_list[1]) - 1) * (width + space) + margin + width + space)
                    tmp_cell.setParentItem(self)
                elif cell_info[0] == "trap":
                    tmp_cell = TrapCell(self.rect().x() + margin, self.rect().y() + first_width + space + (len(cells_list[1]) - 1) * (width + space) + margin + width + space, jail_index=jail_index)
                    tmp_cell.setParentItem(self)
                
                self.cells.append(tmp_cell)

    def roll_dice_and_move(self, player):
        if self.is_dice_blocked:
            print("ВНИМАНИЕ: Сначала примите решение по участку!")
            return

        if player.in_jail:
            print(f"{player.name} пропускает ход в тюрьме.")
            player.jail_turns -= 1
            if player.jail_turns <= 0:
                player.in_jail = False
            return

        dice_1 = random.randint(1, 6)
        dice_2 = random.randint(1, 6)
        steps = dice_1 + dice_2
        print(f"\nВыпало {dice_1} и {dice_2} (Всего: {steps})")

        board_size = len(self.cells)
        new_position = player.position + steps

        if new_position >= board_size:
            new_position = new_position % board_size
            print(f"Игрок {player.name} прошел СТАРТ и получает $200!")
            player.receive(200)

        target_cell = self.cells[new_position]
        player.move_to_cell(target_cell, new_position)

        # Вызываем логику клетки и ОБЯЗАТЕЛЬНО передаем self (карту)
        action_result = target_cell.on_player_step(player, self)

        if action_result and "teleport_to" in action_result:
            jail_idx = action_result["teleport_to"]
            jail_cell = self.cells[jail_idx]
            player.move_to_cell(jail_cell, jail_idx)


# ==========================================
# 3. ГЛАВНОЕ ОКНО (КАМЕРА И УПРАВЛЕНИЕ ХОДАМИ)
# ==========================================
class GameBoardView(QGraphicsView):
    def __init__(self, humans_count, bots_count):
        super().__init__()
        
        # Огромная сцена
        self.game_scene = QGraphicsScene(0, 0, 3000, 3000)
        self.setScene(self.game_scene)
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30))) # Темный фон стола

        self.setWindowTitle("Монополия")
        self.resize(850, 850)

        # Настройки камеры
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Размещение карты
        self.game_map = GameMap(0, 0)
        self.game_scene.addItem(self.game_map)
        self.game_map.setPos(1000, 1000)
        self.centerOn(self.game_map)

        # Инициализация списка игроков
        self.players = []
        colors = [QColor("red"), QColor("blue"), QColor("green"), QColor("yellow")]
        color_idx = 0

        # Добавляем людей
        for i in range(humans_count):
            player = Player(f"Игрок {i+1}", colors[color_idx], 5000)
            self.players.append(player)
            color_idx += 1

        # Добавляем ботов
        for i in range(bots_count):
            bot = BotPlayer(f"Бот {i+1}", colors[color_idx], 5000)
            self.players.append(bot)
            color_idx += 1

        # Расставляем фишки на старте
        if self.game_map.cells: # Проверка, что карта создалась
            for p in self.players:
                self.game_scene.addItem(p.token)
                p.move_to_cell(self.game_map.cells[0], 0)

        # Система ходов
        self.current_player_index = 0
        self.has_rolled = False
        print(f"\n--- ИГРА НАЧАЛАСЬ. ХОД ИГРОКА: {self.players[0].name} ---")

        # Если первым ходит бот - запускаем его таймер
        if isinstance(self.players[0], BotPlayer):
             QTimer.singleShot(1000, self.play_bot_turn)

    def next_turn(self):
        """Завершает ход и передает очередь дальше"""
        self.has_rolled = False
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        
        current = self.players[self.current_player_index]
        print(f"\n--- ХОД ИГРОКА: {current.name} ---")

        # Если очередь бота
        if isinstance(current, BotPlayer):
            QTimer.singleShot(1000, self.play_bot_turn)

    def play_bot_turn(self):
        """Бросок кубиков ботом и передача хода"""
        current = self.players[self.current_player_index]
        self.game_map.roll_dice_and_move(current)
        
        # Через 1.5 секунды после броска ход переходит дальше
        QTimer.singleShot(1500, self.next_turn)

    def keyPressEvent(self, event):
        """Обработка клавиш живыми игроками"""
        if event.key() == Qt.Key_Escape:
            QApplication.quit()
            return

        current_player = self.players[self.current_player_index]

        # ПРОБЕЛ - Бросок кубиков
        if event.key() == Qt.Key_Space:
            if not isinstance(current_player, BotPlayer) and not self.has_rolled:
                self.game_map.roll_dice_and_move(current_player)
                self.has_rolled = True
                print("Нажмите ENTER, чтобы завершить ход.")
                
        # ENTER - Завершение хода
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if not isinstance(current_player, BotPlayer):
                # Проверяем, что кубики брошены, а окно покупки (если есть) закрыто
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
        game_window.show()
        
        sys.exit(app.exec())
    else:
        sys.exit()