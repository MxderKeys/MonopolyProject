from cells_classes import PropertyCell, StartCell, ChanceCell, RestCell, MoneyCell, KasinoCell, TrapCell
from map_config import cells_list

from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtCore import Qt
import random

class GameMap(QGraphicsRectItem):
    def __init__(self, x, y, width=1140, height=1140):
        super().__init__(x, y, width, height)
        
        self.setBrush(QBrush(QColor(200, 200, 200)))  # Light gray background
        self.setPen(QColor(0, 0, 0))  # Black border
        self.setZValue(1)

        self.players = []
        self.is_dice_blocked = False
        self.cells = []
        self.properties = []
        self.create_game_map()

    def create_game_map(self):
        first_width = 180
        width = 80
        space = 5
        margin = 5

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
                    tmp_cell = ChanceCell(new_x, new_y, coefficient=cell_info[1], rotation_angle=angle)
                    tmp_cell.setParentItem(self)
                elif cell_info[0] == "rest":
                    tmp_cell = RestCell(new_x, new_y)
                    tmp_cell.setParentItem(self)
                    jail_index = len(self.cells)
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

    def unlock_dice(self):
        self.is_dice_blocked = False
        print("Кубики разблокированы.")

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
        action_result = target_cell.on_player_step(player, self)

        if action_result and "teleport_to" in action_result:
            jail_idx = action_result["teleport_to"]
            jail_cell = self.cells[jail_idx]
            player.move_to_cell(jail_cell, jail_idx)