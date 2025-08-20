"""
简单图标生成器 - 生成树形结构所需的展开/折叠图标
"""

import os
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen
from PyQt5.QtCore import Qt

# 确保图标目录存在
icons_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
os.makedirs(icons_dir, exist_ok=True)


# 创建展开/折叠图标
def create_tree_icons():
    # 创建关闭状态图标 (右箭头)
    closed_pixmap = QPixmap(12, 12)
    closed_pixmap.fill(Qt.transparent)
    painter = QPainter(closed_pixmap)
    painter.setPen(QPen(QColor("#aaaaaa"), 1.2))
    painter.drawLine(3, 6, 9, 6)
    painter.drawLine(6, 3, 9, 6)
    painter.drawLine(6, 9, 9, 6)
    painter.end()
    closed_pixmap.save(os.path.join(icons_dir, "branch-closed.png"))

    # 创建打开状态图标 (下箭头)
    open_pixmap = QPixmap(12, 12)
    open_pixmap.fill(Qt.transparent)
    painter = QPainter(open_pixmap)
    painter.setPen(QPen(QColor("#aaaaaa"), 1.2))
    painter.drawLine(6, 3, 6, 9)
    painter.drawLine(3, 6, 6, 9)
    painter.drawLine(9, 6, 6, 9)
    painter.end()
    open_pixmap.save(os.path.join(icons_dir, "branch-open.png"))


if __name__ == "__main__":
    create_tree_icons()
    print("图标创建完成!")
