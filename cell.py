from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PySide6.QtGui import QBrush, QColor, QFont, QTextOption
from PySide6.QtCore import Qt

class Cell(QGraphicsRectItem):
    def __init__(self, x, y, width=180, height=180, rotation_angle=0):
        super().__init__(0, 0, width, height)
        self.press_pos = None
        
        self.setPos(x, y)
        if rotation_angle % 180 == 90:
            self.setRotation(rotation_angle)
            
        self.base_color = QColor(255, 255, 255)
        self.setBrush(QBrush(self.base_color))
        self.setPen(QColor(0, 0, 0))

        self.setZValue(2)
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event):
        highlight_color = QColor(180, 180, 180)
        self.setBrush(QBrush(highlight_color))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(self.base_color))
        super().hoverLeaveEvent(event)

    def on_player_step(self, player):
        raise NotImplementedError("Метод on_player_step должен быть переопределен!")

    def show_info(self):
        raise NotImplementedError("Метод show_info должен быть переопределен!")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.press_pos = event.scenePos()
            event.accept() 
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.press_pos is not None:
            dist = (event.scenePos() - self.press_pos).manhattanLength()
            
            if dist < 5: 
                self.show_info()
            
            self.press_pos = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)