"""University Student Learning Portal desktop GUI. Connect to the team API or use an offline preview."""

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from .portal_client import DEFAULT_PROFILE, SAVED_PROFILE, Portal, PortalError
from PyQt6.QtCore import (
    QEasingCurve, QEvent, QPoint, QPointF, QRectF, QObject, QParallelAnimationGroup,
    QPropertyAnimation, QRunnable, QSize, Qt, QThreadPool, QTimer, QVariantAnimation,
    QSettings, pyqtSignal, pyqtSlot,
)
from PyQt6.QtGui import (
    QColor, QCursor, QFont, QIcon, QKeySequence, QPainter, QPen, QPixmap, QPolygonF, QRadialGradient,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


DESIGN_STYLES = """
    QWidget { color: #243247; font-family: 'Segoe UI'; font-size: 10pt; }
    QMainWindow, QDialog { background: #F4F1EE; }
    QLineEdit, QComboBox, QSpinBox {
        background: #FFFFFF; border: 1px solid #D9E0E8; border-radius: 6px;
        padding: 8px 10px; min-height: 20px; selection-background-color: #2874A6;
    }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 1px solid #E4572E; }
    QComboBox::drop-down { border: 0; width: 26px; }
    QPushButton {
        background: #17365D; color: #FFFFFF; border: 1px solid #17365D;
        border-radius: 6px; padding: 8px 13px; min-height: 20px; font-weight: 600;
    }
    QPushButton:hover { background: #D94D2B; border-color: #D94D2B; }
    QPushButton:pressed { background: #102845; }
    QPushButton:disabled { background: #E5EAF0; color: #98A2B3; border-color: #E5EAF0; }
    QPushButton[variant="secondary"] { background: rgba(255,255,255,210); color: #17365D; border-color: rgba(255,255,255,220); }
    QPushButton[variant="secondary"]:hover { background: #FFF7F2; border-color: #E7B9A9; }
    QPushButton[variant="quiet"] { background: transparent; color: #FFFFFF; border-color: transparent; }
    QPushButton[variant="danger"] { background: #A93232; border-color: #A93232; }
    QPushButton[variant="danger"]:hover { background: #862626; border-color: #862626; }
    QTableWidget {
        background: rgba(255,255,255,225); alternate-background-color: rgba(250,247,244,220); color: #243247;
        border: 1px solid rgba(255,255,255,230); border-radius: 12px; gridline-color: #F0E8E3;
        selection-background-color: #FCE3D9; selection-color: #49251C;
    }
    QTableWidget::item { padding: 8px; border-bottom: 1px solid #EDF1F5; }
    QHeaderView::section {
        background: #F7EDE7; color: #49352D; padding: 11px; border: 0;
        border-bottom: 1px solid #E8DCD5; font-weight: 700;
    }
    QDialogButtonBox QPushButton { min-width: 82px; }
    QFormLayout QLabel { color: #344054; font-weight: 600; }
    QScrollBar:vertical, QScrollBar:horizontal { background: #EDF1F6; border: 0; }
    QScrollBar:vertical { width: 10px; margin: 0; }
    QScrollBar:horizontal { height: 10px; margin: 0; }
    QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
        background: #C3CFDD; border-radius: 5px; min-height: 28px; min-width: 28px;
    }
    QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background: #2874A6; }
    QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
    QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
    #loginPanel { background: #FFFFFF; }
    #brandingPanel { background: #0C0D0F; }
    #sidebar { background: #17191D; }
    #loginHeading { color: #17365D; font-size: 25pt; font-weight: 700; }
    #brandName { color: #FFFFFF; font-size: 18pt; font-weight: 700; }
    #welcomeText { color: #FFFFFF; font-size: 19pt; font-weight: 700; }
    #inputField { background: #F8FAFC; }
    #signInButton { padding: 12px; }
    #errorLabel { color: #A93232; font-size: 9pt; }
    #sidebarLogo { color: #FFFFFF; font-size: 16pt; font-weight: 700; letter-spacing: 1px; }
    #menuButton {
        background: transparent; color: #DCE6F0; border: 0; text-align: left;
        padding: 11px 12px; border-radius: 7px; font-weight: 500;
    }
    #menuButton:hover { background: #244A70; color: #FFFFFF; }
    QPushButton#menuButton[active="true"] {
        background: #2874A6; color: #FFFFFF; border-left: 3px solid #FFFFFF; font-weight: 700;
    }
    #logoutButton { background: #A93232; border-color: #A93232; }
    #contentArea, #dashboardPage, QScrollArea { background: transparent; border: 0; }
    #pageHeading { color: #17365D; font-size: 19pt; font-weight: 700; }
    QLabel#userName { color: #17365D; font-size: 10pt; font-weight: 700; }
    QLabel#userRole { color: #667085; font-size: 9pt; }
    #headerSeparator { background: #D9E0E8; border: 0; }
    #welcomeHeading { color: #17365D; font-size: 18pt; font-weight: 700; }
    #sectionHeading { color: #17365D; font-size: 16pt; font-weight: 700; }
    #statCard, #panelCard {
        background: rgba(255,255,255,218); border: 1px solid rgba(255,255,255,235); border-radius: 18px; padding: 12px;
    }
    #cardTitle { color: #667085; font-size: 9pt; }
    #cardValue { color: #252323; font-size: 24pt; font-weight: 750; }
    #panelHeading { color: #17365D; font-size: 12pt; font-weight: 700; }
    #panelDescription { color: #667085; font-size: 9pt; }
    #noticeSummary { color: #17365D; font-size: 13pt; font-weight: 700; }
    #quickButton { background: rgba(255,255,255,215); color: #49352D; border-color: rgba(255,255,255,235); border-radius: 18px; }
    #quickButton:hover { background: #FFF6F0; color: #49251C; border-color: #E7B9A9; }
    #activityList { background: rgba(255,255,255,180); border: 1px solid rgba(255,255,255,230); border-radius: 12px; padding: 6px; }
    #activityList::item { color: #344054; padding: 9px; border-bottom: 1px solid #EEE4DE; }
    #activityList::item:hover { background: rgba(255,255,255,230); }
    #activityList::item:selected { background: #FCE3D9; color: #49251C; }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 2px solid #E4572E; }
    QTableWidget::item:hover:!selected { background: #FFF2EB; }
    QPushButton#menuButton[active="true"] { background: #FFFFFF; color: #17365D; border-left: 3px solid #E4572E; }
    QPushButton#menuButton[collapsed="true"] { text-align: center; padding-left: 0; padding-right: 0; }
    QPushButton#menuButton[active="true"]:hover { background: #FFF8F4; color: #17365D; }
    #statCard, #panelCard, #heroCard, #agendaCard { border-radius: 20px; }
    #heroCard { background: #E4572E; border: 1px solid rgba(255,255,255,135); border-radius: 24px; }
    #heroTitle { color: white; font-size: 20pt; font-weight: 750; }
    #heroCopy { color: rgba(255,255,255,235); font-size: 10pt; }
    #heroMeta { color: rgba(255,255,255,235); font-size: 9pt; }
    #heroButton { background: #171615; color: white; border: 1px solid #171615; border-radius: 20px; }
    #heroButton:hover { background: #302B29; border-color: #302B29; }
    #heroButton[variant="secondary"] { background: rgba(255,255,255,36); color: white; border: 1px solid rgba(255,255,255,135); }
    #heroButton[variant="secondary"]:hover { background: rgba(255,255,255,70); }
    #primaryStat { background: #E4572E; border: 1px solid rgba(255,255,255,135); }
    #primaryStat #cardTitle, #primaryStat #cardValue, #primaryStat QLabel { color: white; }
    #primaryStat #panelDescription { color: rgba(255,255,255,225); }
    #sidebar { border: 1px solid rgba(255,255,255,25); border-radius: 20px; }
    #workspaceLabel { color: rgba(255,255,255,225); font-size: 9pt; }
    #viewChip { background: rgba(255,255,255,190); border: 1px solid white; border-radius: 12px; padding: 3px 8px; }
    #sidebarNavButton { background: transparent; color: #DCE6F0; border: 0; text-align: left; padding: 10px 12px; border-radius: 12px; }
    #sidebarNavButton:hover { background: #292C31; color: white; }
    #sidebarNavButton[active="true"] { background: #E4572E; color: #17191D; border-left: 3px solid #FFD7C9; font-weight: 700; }
    #sidebarNavButton[collapsed="true"] { text-align: center; padding: 8px 0; }
    #sidebarSection { color: rgba(255,255,255,155); font-size: 8pt; font-weight: 700; letter-spacing: 1px; }
    #collapseHandle { background: white; color: #17365D; border: 1px solid #EFE5E0; border-radius: 15px; min-width: 28px; max-width: 28px; min-height: 28px; max-height: 28px; padding: 0; }
    #analyticsRange { background: rgba(255,255,255,185); border: 1px solid white; border-radius: 16px; padding: 2px; }
    #analyticsRange QPushButton { background: transparent; color: #49352D; border: 0; border-radius: 14px; padding: 6px 12px; }
    #analyticsRange QPushButton[active="true"] { background: #171615; color: white; }
    #statCard[statTone="teal"] { border-top: 4px solid #20A387; }
    #statCard[statTone="gold"] { border-top: 4px solid #E9A12B; }
    #statCard[statTone="violet"] { border-top: 4px solid #8B5BB5; }
    #emptyState { color: #667085; background: rgba(255,255,255,130); border: 1px dashed #D8C8BF; border-radius: 12px; padding: 16px; }
    #analyticsLoading { color: #7C4A3A; background: rgba(255,255,255,180); border-radius: 10px; padding: 6px 10px; }
    QDialog { background: #F7F1ED; }
    QDialog QLineEdit, QDialog QComboBox, QDialog QSpinBox { background: rgba(255,255,255,235); }
"""


APP_STYLE_EXTRAS = """
    QCheckBox:enabled:hover, QComboBox:enabled:hover, QSpinBox:enabled:hover { border-color: #A9B9CC; }
    QTableWidget::item:hover:!selected, QListWidget::item:hover:!selected,
    QHeaderView::section:hover, QMenu::item:selected { background: #EAF0F6; color: #17365D; }
    #identityCard { background: #FFFFFF; border: 1px solid #E3E8EF; border-radius: 8px; padding: 5px 10px; }
    #syncStatus { color: #52677F; background: #EAF0F6; border: 1px solid #D9E0E8;
                  border-radius: 10px; padding: 5px 9px; font-size: 9pt; }
    #appearanceToggle { border-radius: 16px; }
    #analyticsLoading { color: #7C4A3A; background: rgba(255,255,255,180); border-radius: 10px; padding: 6px 10px; }
    #analyticsProgress { border: 0; background: rgba(255,255,255,100); border-radius: 3px; max-height: 6px; }
    #analyticsProgress::chunk { background: #E4572E; border-radius: 3px; }
    #notificationButton {
        background: #FFFFFF;
        color: #17365D;
        border: 1px solid #D9E0E8;
        border-radius: 18px;
        padding: 7px 12px;
        font-weight: 700;
    }
    #notificationButton:hover {
        background: #FFF2EB;
        border-color: #E4572E;
    }
"""

DARK_THEME_STYLES = """
    QWidget { color: #EEE9E5; }
    QMainWindow, QDialog { background: #1D1F23; }
    QLineEdit, QComboBox, QSpinBox {
        color: #F1ECE8; background: #292C31; border: 1px solid #4B4E53;
        selection-background-color: #E4572E; selection-color: white;
    }
    QDialog QLineEdit, QDialog QComboBox, QDialog QSpinBox {
        color: #F1ECE8; background: #292C31; border: 1px solid #4B4E53;
        selection-background-color: #E4572E; selection-color: white;
    }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 2px solid #F07858; }
    QComboBox QAbstractItemView, QMenu { color: #F1ECE8; background: #292C31; border: 1px solid #4B4E53; }
    QPushButton[variant="primary"] { color: white; background: #D94D2B; border-color: #D94D2B; }
    QPushButton[variant="primary"]:hover { background: #EB6544; border-color: #EB6544; }
    QPushButton[variant="secondary"] { color: #F1ECE8; background: #303338; border-color: #505258; }
    QPushButton[variant="secondary"]:hover { color: white; background: #41444A; border-color: #666970; }
    QPushButton:disabled { color: #898B90; background: #303237; border-color: #3D4045; }
    QTableWidget { color: #EEE9E5; background: #25282D; alternate-background-color: #2B2E33;
                   border-color: #484B51; gridline-color: #393C42; selection-background-color: #5A382F;
                   selection-color: #FFF8F3; }
    QTableWidget::item { border-bottom-color: #393C42; }
    QTableWidget::item:hover:!selected, QListWidget::item:hover:!selected,
    QHeaderView::section:hover, QMenu::item:selected { color: #FFF8F3; background: #383B40; }
    QHeaderView::section { color: #F0E8E3; background: #303338; border-bottom-color: #4A4D52; }
    QScrollBar:vertical, QScrollBar:horizontal { background: #23252A; }
    QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background: #55585E; }
    #loginPanel { background: #25282D; }
    #loginHeading, #pageHeading, #welcomeHeading, #sectionHeading, #panelHeading, #noticeSummary { color: #F4EDE8; }
    #brandName, #welcomeText, #userName { color: #FFF8F3; }
    #userRole, #panelDescription, #cardTitle { color: #B9B4B0; }
    #inputField { color: #F1ECE8; background: #292C31; }
    #contentArea, #dashboardPage, QScrollArea { background: transparent; }
    #statCard, #panelCard { color: #EEE9E5; background: rgba(42,45,50,238); border-color: rgba(255,255,255,34); }
    #cardValue { color: #F8F2EE; }
    #primaryStat { background: #D94D2B; border-color: rgba(255,255,255,125); }
    #primaryStat #cardTitle, #primaryStat #cardValue, #primaryStat QLabel { color: white; }
    #heroCard { background: #D94D2B; border-color: rgba(255,255,255,130); }
    #quickButton { color: #F0EAE6; background: #303338; border-color: #505258; }
    #quickButton:hover { color: white; background: #41444A; }
    #activityList { color: #EEE9E5; background: rgba(31,33,37,225); border-color: #494C52; }
    #activityList::item { color: #EEE9E5; border-bottom-color: #393C42; }
    #activityList::item:selected { color: white; background: #5A382F; }
    #emptyState { color: #C6C0BC; background: rgba(31,33,37,200); border-color: #55585E; }
    #identityCard { background: rgba(42,45,50,230); border-color: #4B4E53; }
    #syncStatus { color: #D8D1CC; background: #303338; border-color: #505258; }
    #analyticsLoading { color: #F2C2AF; background: #303338; }
    #analyticsProgress { background: #44474D; }
    #analyticsRange { background: #292C31; border-color: #505258; }
    #analyticsRange QPushButton { color: #EEE9E5; }
    #analyticsRange QPushButton[active="true"] { color: white; background: #111214; }
    #brandingPanel { background: #0C0D0F; }
"""


def application_stylesheet(theme="light"):
    return DESIGN_STYLES + APP_STYLE_EXTRAS + (DARK_THEME_STYLES if theme == "dark" else "")


class PortalButton(QPushButton):
    """Shared button with a consistent visual variant."""

    def __init__(self, text, variant="primary", parent=None):
        super().__init__(text, parent)
        self.setProperty("variant", variant)


class PortalCard(QFrame):
    """Reusable white surface used by dashboard cards and action panels."""

    def __init__(self, object_name="panelCard", parent=None):
        super().__init__(parent)
        self.setObjectName(object_name)
        self.content_layout = QVBoxLayout(self)
        self.content_layout.setContentsMargins(16, 14, 16, 14)
        self.content_layout.setSpacing(10)
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setColor(QColor(67, 42, 31, 36))
        self._shadow.setOffset(0, 3)
        self._shadow.setBlurRadius(0)
        self.setGraphicsEffect(self._shadow)
        self._hover_animation = QPropertyAnimation(self._shadow, b"blurRadius", self)
        self._hover_animation.setDuration(150)
        self._hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def enterEvent(self, event):
        self._animate_shadow(13)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_shadow(0)
        super().leaveEvent(event)

    def _animate_shadow(self, radius):
        self._hover_animation.stop()
        self._hover_animation.setStartValue(self._shadow.blurRadius())
        self._hover_animation.setEndValue(radius)
        self._hover_animation.start()


class WarmCanvas(QFrame):
    """Paint a restrained warm backdrop beneath translucent portal surfaces."""

    def __init__(self, dark=False, parent=None):
        super().__init__(parent)
        self.dark = bool(dark)

    def set_dark(self, dark):
        self.dark = bool(dark)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#202126" if self.dark else "#F2E8E2"))
        for center, radius, color in (
            (QPointF(self.width() * .13, self.height() * .12), self.width() * .66,
             QColor(229, 119, 82, 31 if self.dark else 45)),
            (QPointF(self.width() * .92, self.height() * .12), self.width() * .62,
             QColor(191, 117, 99, 25 if self.dark else 36)),
            (QPointF(self.width() * .63, self.height() * .94), self.width() * .76,
             QColor(255, 228, 207, 24 if self.dark else 95)),
        ):
            gradient = QRadialGradient(center, max(1, radius))
            gradient.setColorAt(0, color)
            gradient.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))
            painter.fillRect(self.rect(), gradient)
        painter.end()
        super().paintEvent(event)


class ProgressRing(QWidget):
    """Small animated ring whose value comes from the current portal snapshot."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0.0
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(650)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.valueChanged.connect(self._set_animated_value)
        self.setMinimumSize(98, 98)
        self.setMaximumSize(118, 118)
        self.setAccessibleName("Average lesson completion")

    def set_value(self, value):
        value = max(0, min(100, float(value)))
        if abs(value - self.progress) < .1:
            return
        self.animation.stop()
        self.animation.setStartValue(self.progress)
        self.animation.setEndValue(value)
        self.animation.start()

    def _set_animated_value(self, value):
        self.progress = float(value)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = self.rect().adjusted(8, 8, -8, -8)
        pen = QPen(QColor(255, 255, 255, 85), 7)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(bounds, 90 * 16, -360 * 16)
        pen.setColor(QColor("#FFFFFF"))
        painter.setPen(pen)
        painter.drawArc(bounds, 90 * 16, -int(360 * self.progress * 16 / 100))
        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        painter.drawText(self.rect().adjusted(0, -2, 0, -2), Qt.AlignmentFlag.AlignCenter,
                         f"{round(self.progress)}%")
        painter.end()


class AnimatedDialog(QDialog):
    """Short fade for existing modal forms without changing their result flow."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(1)
        self.setGraphicsEffect(self._opacity)
        self._fade = QPropertyAnimation(self._opacity, b"opacity", self)
        self._fade.setDuration(135)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._pending_result = None

    def showEvent(self, event):
        self._opacity.setOpacity(0)
        self._fade.stop()
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.start()
        super().showEvent(event)

    def accept(self):
        self._finish_with_fade(QDialog.DialogCode.Accepted)

    def reject(self):
        self._finish_with_fade(QDialog.DialogCode.Rejected)

    def _finish_with_fade(self, result):
        if not self.isVisible():
            QDialog.done(self, result)
            return
        self._fade.stop()
        self._pending_result = result
        self._fade.setStartValue(self._opacity.opacity())
        self._fade.setEndValue(0.0)
        try:
            self._fade.finished.disconnect(self._finish_close)
        except TypeError:
            pass
        self._fade.finished.connect(self._finish_close)
        self._fade.start()

    def _finish_close(self):
        if self._pending_result is not None:
            result, self._pending_result = self._pending_result, None
            QDialog.done(self, result)


def cap_badge(size):
    """Draw the portal cap on its own backing at double resolution."""
    image = QPixmap(size * 2, size * 2)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(size * 2 / 64, size * 2 / 64)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("white"))
    painter.drawRoundedRect(0, 0, 64, 64, 14, 14)
    painter.setBrush(QColor("#2874A6"))
    painter.drawPolygon(QPolygonF([QPointF(x, y) for x, y in
                                  [(18, 32), (32, 39), (47, 32), (47, 40), (32, 47), (18, 40)]]))
    painter.setBrush(QColor("#17365D"))
    painter.drawPolygon(QPolygonF([QPointF(x, y) for x, y in
                                  [(7, 28), (32, 16), (57, 28), (32, 40)]]))
    painter.drawRoundedRect(53, 28, 3, 15, 1, 1)
    painter.end()
    image.setDevicePixelRatio(2)
    label = QLabel()
    label.setPixmap(image)
    label.setFixedSize(size, size)
    label.setAccessibleName("University Student Learning Portal logo")
    return label


def sidebar_icon(kind, color="#E5EDF5"):
    """Draw a small, consistent navigation glyph without an added icon package."""
    image = QPixmap(48, 48)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), 3.2, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    if kind == "dashboard":
        for x, y in ((9, 9), (26, 9), (9, 26), (26, 26)):
            painter.drawRoundedRect(x, y, 12, 12, 3, 3)
    elif kind == "students":
        painter.drawEllipse(17, 7, 14, 14)
        painter.drawArc(9, 23, 30, 23, 0, 180 * 16)
        painter.drawLine(12, 37, 36, 37)
    elif kind == "courses":
        painter.drawRoundedRect(8, 9, 32, 30, 4, 4)
        painter.drawLine(24, 10, 24, 38)
        painter.drawLine(13, 16, 19, 16)
        painter.drawLine(29, 16, 35, 16)
    elif kind == "enrollments":
        for y in (12, 23, 34):
            painter.drawRoundedRect(8, y - 4, 7, 7, 2, 2)
            painter.drawLine(21, y, 39, y)
    elif kind == "analytics":
        painter.drawLine(9, 39, 39, 39)
        painter.drawLine(11, 37, 11, 26)
        painter.drawLine(21, 37, 21, 18)
        painter.drawLine(31, 37, 31, 10)
        painter.drawLine(39, 37, 39, 23)
    elif kind == "logout":
        painter.drawRoundedRect(8, 8, 20, 32, 3, 3)
        painter.drawLine(21, 24, 40, 24)
        painter.drawLine(33, 17, 40, 24)
        painter.drawLine(33, 31, 40, 24)
    painter.end()
    return QIcon(image)


def moon_icon(color):
    """Draw a crescent-moon icon in the requested color."""
    image = QPixmap(48, 48)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    painter.drawEllipse(7, 5, 34, 38)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
    painter.drawEllipse(20, 1, 34, 38)
    painter.end()
    return QIcon(image)


class LoginPage(QWidget):
    signed_in = pyqtSignal()

    def __init__(self, portal):
        super().__init__()
        self.portal = portal
        self.setup_ui()

    def show_connection(self):
        endpoint = self.portal.endpoint
        if endpoint:
            self.connection_label.setText(f"Team server · {endpoint.host}:{endpoint.port}")
        else:
            self.connection_label.setText("Choose portal-team.json from your backend developer.")

    def transition_panels(self):
        return [
            (self.branding_panel.grab(), self.branding_panel.geometry()),
            (self.login_panel.grab(), self.login_panel.geometry()),
        ]

    def choose_connection(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose the team connection", "", "Team profile (*.json)")
        if path:
            try:
                self.portal.configure(path, remember=True)
            except PortalError as error:
                self.error_label.setText(str(error))
                return
            self.error_label.clear()
            self.show_connection()

    def login(self):
        username, password = self.username_input.text().strip(), self.password_input.text()
        if not username or not password:
            self.error_label.setText("Enter your username and password.")
            return
        try:
            self.portal.login(username, password)
        except PortalError as error:
            self.error_label.setText(str(error))
            self.password_input.selectAll()
            self.password_input.setFocus()
            return
        self.password_input.clear()
        self.show_password_checkbox.setChecked(False)
        self.signed_in.emit()

    def toggle_password(self, checked):
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )

    def setup_ui(self):

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # LOGIN PANEL

        login_panel = QFrame()
        self.login_panel = login_panel
        login_panel.setObjectName("loginPanel")

        login_layout = QVBoxLayout(login_panel)
        login_layout.setContentsMargins(65, 55, 65, 55)

        login_layout.addStretch()

        heading = QLabel("Welcome Back")
        heading.setObjectName("loginHeading")

        description = QLabel("Sign in to access your learning portal.")

        username_label = QLabel("Username")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setObjectName("inputField")

        password_label = QLabel("Password")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setObjectName("inputField")

        self.show_password_checkbox = QCheckBox("Show password")
        self.show_password_checkbox.toggled.connect(self.toggle_password)

        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)

        self.username_input.textChanged.connect(lambda: self.error_label.clear())
        self.password_input.textChanged.connect(lambda: self.error_label.clear())

        sign_in_button = PortalButton("Sign In")
        sign_in_button.setObjectName("signInButton")
        sign_in_button.clicked.connect(self.login)

        self.password_input.returnPressed.connect(self.login)

        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.connection_label = QLabel()
        self.connection_label.setWordWrap(True)
        self.show_connection()
        choose = PortalButton("Choose team connection file", "secondary")
        choose.clicked.connect(self.choose_connection)

        login_layout.addWidget(heading)
        login_layout.addWidget(description)
        login_layout.addWidget(self.connection_label)
        login_layout.addWidget(choose)
        login_layout.addSpacing(25)

        login_layout.addWidget(username_label)
        login_layout.addWidget(self.username_input)

        login_layout.addSpacing(12)

        login_layout.addWidget(password_label)
        login_layout.addWidget(self.password_input)
        login_layout.addWidget(self.show_password_checkbox)

        login_layout.addSpacing(15)
        login_layout.addWidget(sign_in_button)
        login_layout.addSpacing(15)
        login_layout.addWidget(self.error_label)

        login_layout.addStretch()

        # BRANDING PANEL

        branding_panel = QFrame()
        self.branding_panel = branding_panel
        branding_panel.setObjectName("brandingPanel")

        branding_layout = QVBoxLayout(branding_panel)
        branding_layout.setContentsMargins(45, 50, 45, 45)

        logo = cap_badge(64)
        logo.setObjectName("logo")

        university_name = QLabel("UNIVERSITY\nSTUDENT\nLEARNING PORTAL")
        university_name.setObjectName("brandName")

        welcome = QLabel("Your Academic Journey\nStarts Here.")
        welcome.setObjectName("welcomeText")

        branding_layout.addWidget(logo)
        branding_layout.addSpacing(20)
        branding_layout.addWidget(university_name)
        branding_layout.addStretch()
        branding_layout.addWidget(welcome)

        # The original two-panel layout

        main_layout.addWidget(branding_panel, 42)
        main_layout.addWidget(login_panel, 42)

class RecordForm(AnimatedDialog):
    """Build a labelled form. Each dropdown retains the database ID of its selection."""

    def __init__(self, parent, title):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(460)
        self.layout = QFormLayout(self)
        self.layout.setContentsMargins(24, 22, 24, 18)
        self.layout.setHorizontalSpacing(18)
        self.layout.setVerticalSpacing(13)
        self.inputs = {}

    def line(self, key, caption, value="", placeholder="", limit=240):
        field = QLineEdit(str(value))
        field.setMaxLength(limit)
        field.setPlaceholderText(placeholder)
        self.layout.addRow(caption, field)
        self.inputs[key] = field

    def number(self, key, caption, value, maximum, optional=False):
        field = QSpinBox()
        field.setRange(0 if optional else 1, maximum)
        if optional:
            field.setSpecialValueText("Not set")
        field.setValue(value or 0)
        self.layout.addRow(caption, field)
        self.inputs[key] = field

    def choose(self, key, caption, choices, initial=None):
        field = QComboBox()
        for item in choices:
            field.addItem(item["name"], item["id"])
        if field.count() == 0:
            raise PortalError(f"No available choices for {caption.lower()}. Add the academic record first.")
        if initial is not None:
            field.setCurrentIndex(field.findData(initial))
        self.layout.addRow(caption, field)
        self.inputs[key] = field

    def values(self):
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addRow(buttons)
        if self.exec() != QDialog.DialogCode.Accepted:
            return None
        result = {}
        for name, field in self.inputs.items():
            if isinstance(field, QComboBox):
                result[name] = field.currentData()
            elif isinstance(field, QSpinBox):
                result[name] = field.value() or None
            else:
                result[name] = field.text().strip()
        return result


class StudentProfileDialog(AnimatedDialog):
    """Read-only profile assembled only from the authenticated snapshot."""

    def __init__(self, parent, student, enrollments):
        super().__init__(parent)
        self.setWindowTitle("Student profile")
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 18)
        layout.setSpacing(14)
        heading = QLabel(student.name)
        heading.setObjectName("welcomeHeading")
        layout.addWidget(heading)
        details = QFormLayout()
        details.setHorizontalSpacing(18)
        details.setVerticalSpacing(10)
        for label, value in (
            ("Official student ID", student.number),
            ("Programme", student.programme),
            ("Gender", student.cell(student.gender)),
            ("Email", student.cell(student.email)),
            ("Phone", student.cell(student.phone_number)),
            ("Status", student.status.title()),
        ):
            details.addRow(label, QLabel(value))
        layout.addLayout(details)
        section = QLabel("Enrolments in the current snapshot")
        section.setObjectName("panelHeading")
        layout.addWidget(section)
        enrolment_list = QListWidget()
        matching = [e for e in enrollments if e.student_number == student.number]
        enrolment_list.addItems(
            [f"{e.course_code} · {e.course}  —  {e.term}  ({e.status.title()})" for e in matching]
            or ["No enrolments in the current snapshot."]
        )
        layout.addWidget(enrolment_list)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


class AuditLogSignals(QObject):
    finished = pyqtSignal(object)


class AuditLogTask(QRunnable):
    """Load one persistent audit page away from the GUI thread."""

    def __init__(self, portal, limit, offset):
        super().__init__()
        self.portal = portal
        self.limit = limit
        self.offset = offset
        self.signals = AuditLogSignals()

    def run(self):
        try:
            result = self.portal.audit_log(limit=self.limit, offset=self.offset)
        except PortalError as error:
            result = error
        self.signals.finished.emit(result)


class AuditLogDialog(AnimatedDialog):
    """Paginated database audit history, with session-only preview data."""

    PAGE_SIZE = 50

    def __init__(self, parent, portal, session_entries):
        super().__init__(parent)
        self.portal = portal
        self.session_entries = session_entries
        self.offset = 0
        self.total = 0
        self.task = None
        self.setWindowTitle("Audit log" if not portal.preview else "Preview audit log")
        self.resize(1120, 580)
        layout = QVBoxLayout(self)
        note = QLabel(
            "Persistent server history, newest first. This log includes the account, time, operation, "
            "record key and before/after values."
            if not portal.preview else
            "Preview actions exist only in memory and disappear when the preview closes."
        )
        note.setObjectName("panelDescription")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter the records on this page…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.filter_rows)
        layout.addWidget(self.search)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Time", "Account", "Table", "Action", "Record key", "Before", "After"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        layout.addWidget(self.table)
        self.status = QLabel()
        self.status.setObjectName("panelDescription")
        layout.addWidget(self.status)
        footer = QHBoxLayout()
        self.previous_button = PortalButton("Previous", "secondary")
        self.previous_button.clicked.connect(self.previous_page)
        footer.addWidget(self.previous_button)
        self.next_button = PortalButton("Next", "secondary")
        self.next_button.clicked.connect(self.next_page)
        footer.addWidget(self.next_button)
        footer.addStretch()
        self.refresh_button = PortalButton("Refresh", "secondary")
        self.refresh_button.clicked.connect(self.load_page)
        footer.addWidget(self.refresh_button)
        close = PortalButton("Close", "secondary")
        close.clicked.connect(self.accept)
        footer.addWidget(close)
        layout.addLayout(footer)
        self.load_page()

    @staticmethod
    def format_value(value):
        if value is None:
            return "—"
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        return str(value)

    def load_page(self):
        if self.portal.preview:
            self.total = len(self.session_entries)
            start = self.offset
            self.show_entries([
                {
                    "occurred_at": entry["time"],
                    "actor_name": entry["account"],
                    "actor_username": "",
                    "table_name": entry["record"].split(" · ", 1)[0].casefold() + "s",
                    "operation": entry["action"],
                    "record_key": entry["record"],
                    "old_data": entry["details"],
                    "new_data": None,
                }
                for entry in self.session_entries[start:start + self.PAGE_SIZE]
            ])
            return
        self.status.setText("Loading audit history…")
        self.refresh_button.setEnabled(False)
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.task = AuditLogTask(self.portal, self.PAGE_SIZE, self.offset)
        self.task.signals.finished.connect(self.page_loaded)
        QThreadPool.globalInstance().start(self.task)

    @pyqtSlot(object)
    def page_loaded(self, result):
        self.refresh_button.setEnabled(True)
        if isinstance(result, PortalError):
            self.status.setText(str(result))
            self.previous_button.setEnabled(self.offset > 0)
            self.next_button.setEnabled(False)
            return
        self.total = result["total"]
        self.show_entries(result["entries"])

    def show_entries(self, entries):
        self.table.setRowCount(len(entries) or 1)
        if not entries:
            self.table.setItem(0, 0, QTableWidgetItem("No audit records on this page."))
            self.table.setSpan(0, 0, 1, 7)
        for row, entry in enumerate(entries):
            actor = entry.get("actor_name") or entry.get("database_user") or "Unknown account"
            username = entry.get("actor_username")
            account = f"{actor} ({username})" if username else actor
            values = (
                self.format_value(entry.get("occurred_at")),
                account,
                self.format_value(entry.get("table_name")),
                self.format_value(entry.get("operation")),
                self.format_value(entry.get("record_key")),
                self.format_value(entry.get("old_data")),
                self.format_value(entry.get("new_data")),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                self.table.setItem(row, column, item)
        self.filter_rows(self.search.text())
        if entries:
            first = self.offset + 1
            last = min(self.offset + len(entries), self.total)
            self.status.setText(f"Showing {first}–{last} of {self.total} audit records")
        else:
            self.status.setText(f"No audit records on this page · {self.total} total")
        self.previous_button.setEnabled(self.offset > 0)
        self.next_button.setEnabled(self.offset + self.PAGE_SIZE < self.total)
        self.table.resizeColumnsToContents()

    def filter_rows(self, query):
        query = query.casefold().strip()
        for row in range(self.table.rowCount()):
            values = [self.table.item(row, col).text() for col in range(self.table.columnCount())
                      if self.table.item(row, col)]
            self.table.setRowHidden(row, query not in " ".join(values).casefold())

    def previous_page(self):
        self.offset = max(0, self.offset - self.PAGE_SIZE)
        self.load_page()

    def next_page(self):
        if self.offset + self.PAGE_SIZE < self.total:
            self.offset += self.PAGE_SIZE
            self.load_page()


HEADERS = {
    "students": ["Student ID", "Full name", "Gender", "Programme", "Status"],
    "courses": ["Code", "Course", "Department", "Credits", "Lessons"],
    "enrollments": ["Enrolment", "Student", "Course", "Semester", "Lessons", "Progress", "Status"],
}

BUTTONS = {
    "students": [
        ("add_student", "Add student"),
        ("edit_student", "Edit student"),
        ("deactivate_student", "Deactivate"),
        ("reactivate_student", "Reactivate"),
        ("delete_student", "Delete"),
    ],
    "courses": [
        ("add_course", "Add course"),
        ("edit_course", "Edit course"),
        ("offer_course", "Offer in semester"),
        ("delete_course", "Delete"),
    ],
    "enrollments": [
        ("add_enrollment", "Create enrolment"),
        ("complete_lesson", "Complete lesson"),
        ("withdraw_enrollment", "Withdraw"),
        ("delete_enrollment", "Remove"),
    ],
}
ACADEMIC = [
    ("add_department", "Add department"),
    ("add_year", "Add academic year"),
    ("add_semester", "Add semester"),
    ("assign_lecturer", "Assign lecturer"),
]
TITLES = dict(pair for pairs in BUTTONS.values() for pair in pairs)
TITLES.update(ACADEMIC)


class SnapshotSignals(QObject):
    finished = pyqtSignal(int, object)


class SnapshotTask(QRunnable):
    """Fetch on a worker, then deliver the response to the GUI thread."""
    def __init__(self, portal, revision):
        super().__init__()
        self.portal = portal
        self.revision = revision
        self.signals = SnapshotSignals()

    def run(self):
        try:
            outcome = self.portal.request("snapshot")
        except PortalError as error:
            outcome = error
        self.signals.finished.emit(self.revision, outcome)


class EnrollmentChart(QWidget):
    """Small dependency-free chart of the current enrolment status totals."""

    COLORS = (QColor("#2874A6"), QColor("#34866A"), QColor("#D28A36"))
    LABELS = ("In progress", "Completed", "Withdrawn")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.counts = [0, 0, 0]
        self.dark = False
        self.setMinimumHeight(155)
        self.setAccessibleName("Enrolment status chart")

    def set_dark(self, dark):
        self.dark = bool(dark)
        self.update()

    def set_records(self, records):
        totals = {"enrolled": 0, "active": 0, "completed": 0, "withdrawn": 0}
        for record in records:
            status = record.status.casefold()
            if status in totals:
                totals[status] += 1
        self.counts = [totals["enrolled"] + totals["active"], totals["completed"], totals["withdrawn"]]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        label_width = 104
        value_width = 30
        bar_x = label_width
        bar_width = max(20, self.width() - label_width - value_width - 12)
        maximum = max(self.counts, default=0)
        row_height = 43
        for index, label in enumerate(self.LABELS):
            y = 8 + index * row_height
            painter.setPen(QColor("#C6C0BC" if self.dark else "#52677F"))
            painter.drawText(0, y + 19, label)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#45484E" if self.dark else "#EDF1F6"))
            painter.drawRoundedRect(bar_x, y + 4, bar_width, 14, 7, 7)
            amount = self.counts[index]
            if amount and maximum:
                painter.setBrush(self.COLORS[index])
                painter.drawRoundedRect(bar_x, y + 4, max(7, int(bar_width * amount / maximum)), 14, 7, 7)
            painter.setPen(QColor("#F1ECE8" if self.dark else "#243247"))
            painter.drawText(bar_x + bar_width + 8, y + 17, str(amount))
        if maximum == 0:
            painter.setPen(QColor("#C6C0BC" if self.dark else "#667085"))
            painter.drawText(bar_x, 8 + len(self.LABELS) * row_height + 2, "No enrolment data yet")
        painter.end()


class BreakdownChart(QWidget):
    """Reusable horizontal breakdown chart for values in the loaded snapshot."""

    COLORS = (QColor("#2874A6"), QColor("#34866A"), QColor("#D28A36"),
              QColor("#8050A8"), QColor("#C85A4A"), QColor("#5D7895"))

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.dark = False
        self.setMinimumHeight(120)

    def set_dark(self, dark):
        self.dark = bool(dark)
        self.update()

    def set_data(self, values):
        ranked = sorted(((str(label), int(count)) for label, count in values.items() if count > 0),
                        key=lambda pair: (-pair[1], pair[0].casefold()))
        if len(ranked) > 6:
            ranked = ranked[:5] + [("Other", sum(count for _label, count in ranked[5:]))]
        self.items = ranked
        self.setMinimumHeight(max(120, len(self.items) * 34 + 18))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self.items:
            painter.setPen(QColor("#C6C0BC" if self.dark else "#667085"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No records in this snapshot")
            painter.end()
            return
        label_width = min(140, max(86, self.width() // 3))
        value_width = 34
        bar_x = label_width
        bar_width = max(18, self.width() - label_width - value_width - 10)
        maximum = max(value for _label, value in self.items)
        for index, (label, value) in enumerate(self.items):
            y = 6 + index * 34
            painter.setPen(QColor("#C6C0BC" if self.dark else "#52677F"))
            painter.drawText(0, y, label_width - 8, 22, Qt.AlignmentFlag.AlignVCenter,
                             self.fontMetrics().elidedText(label, Qt.TextElideMode.ElideRight, label_width - 8))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#45484E" if self.dark else "#EDF1F6"))
            painter.drawRoundedRect(bar_x, y + 4, bar_width, 14, 7, 7)
            painter.setBrush(self.COLORS[index % len(self.COLORS)])
            painter.drawRoundedRect(bar_x, y + 4, max(7, int(bar_width * value / maximum)), 14, 7, 7)
            painter.setPen(QColor("#F1ECE8" if self.dark else "#243247"))
            painter.drawText(bar_x + bar_width + 6, y, value_width - 6, 22,
                             Qt.AlignmentFlag.AlignVCenter, str(value))
        painter.end()


class DonutChart(QWidget):
    """Accessible, dependency-free doughnut chart for snapshot distributions."""

    COLORS = BreakdownChart.COLORS

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.total = 0
        self.dark = False
        self.setMinimumHeight(170)

    def set_dark(self, dark):
        self.dark = bool(dark)
        self.update()

    def set_data(self, values):
        ranked = sorted(((str(label), int(value)) for label, value in values.items() if value > 0),
                        key=lambda item: (-item[1], item[0].casefold()))
        self.items = ranked[:5] + [("Other", sum(value for _label, value in ranked[5:]))] if len(ranked) > 6 else ranked
        self.total = sum(value for _label, value in self.items)
        summary = ", ".join(f"{name}: {value}" for name, value in self.items)
        self.setAccessibleName("Doughnut chart" + (", " + summary if summary else ", no records"))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self.items:
            painter.setPen(QColor("#C6C0BC" if self.dark else "#667085"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No records in this snapshot")
            painter.end()
            return
        size = min(146, max(100, self.height() - 16), max(100, self.width() // 2 - 12))
        x, y = 8, (self.height() - size) // 2
        circle = QRectF(x, y, size, size)
        start = 90 * 16
        for index, (_label, value) in enumerate(self.items):
            span = round(360 * 16 * value / self.total)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self.COLORS[index % len(self.COLORS)])
            painter.drawPie(circle, start, -span)
            start -= span
        hole = circle.adjusted(size * .27, size * .27, -size * .27, -size * .27)
        painter.setBrush(QColor("#2A2D32" if self.dark else "#FFFFFF"))
        painter.drawEllipse(hole)
        painter.setPen(QColor("#F1ECE8" if self.dark else "#243247"))
        painter.drawText(hole, Qt.AlignmentFlag.AlignCenter, f"{self.total}\nrecords")
        legend_x = int(x + size + 16)
        available = max(72, self.width() - legend_x - 6)
        row_height = min(26, max(19, (self.height() - 10) // min(6, len(self.items))))
        for index, (label, value) in enumerate(self.items[:6]):
            row_y = 6 + index * row_height
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self.COLORS[index % len(self.COLORS)])
            painter.drawEllipse(legend_x, row_y + 6, 9, 9)
            painter.setPen(QColor("#F1ECE8" if self.dark else "#52677F"))
            text = self.fontMetrics().elidedText(label, Qt.TextElideMode.ElideRight, max(28, available - 42))
            painter.drawText(legend_x + 14, row_y, max(24, available - 42), row_height,
                             Qt.AlignmentFlag.AlignVCenter, text)
            painter.setPen(QColor("#F1ECE8" if self.dark else "#243247"))
            painter.drawText(self.width() - 30, row_y, 26, row_height,
                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, str(value))
        painter.end()


class DashboardReportDialog(AnimatedDialog):
    """Small report of counts that are present in the current authorized snapshot."""

    def __init__(self, parent, portal):
        super().__init__(parent)
        self.setWindowTitle("Snapshot report")
        self.setMinimumSize(520, 430)
        layout = QVBoxLayout(self)
        note = QLabel(
            "Counts reflect the records available to your account in the current snapshot. "
            + ("Preview records are fictional and held in memory." if portal.preview else
               "This report does not include records outside your access scope.")
        )
        note.setObjectName("panelDescription")
        note.setWordWrap(True)
        layout.addWidget(note)
        students = list(portal.students.values())
        enrollments = list(portal.enrollments.values())
        lecturers = portal.lookups.get("lecturers")
        rows = [
            ("Students in snapshot", str(len(students))),
            ("Active students", str(sum(s.status.casefold() == "active" for s in students))),
            ("Courses in snapshot", str(len(portal.courses))),
            ("Enrolments in snapshot", str(len(enrollments))),
            ("Completed enrolments", str(sum(e.status.casefold() == "completed" for e in enrollments))),
            ("Active lecturers", str(len(lecturers)) if lecturers is not None else "Not available"),
        ]
        table = QTableWidget(len(rows), 2)
        table.setHorizontalHeaderLabels(["Measure", "Value"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().hide()
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                table.setItem(row, column, QTableWidgetItem(value))
        layout.addWidget(table)
        close = PortalButton("Close", "secondary")
        close.clicked.connect(self.accept)
        layout.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)


class DashboardPage(QWidget):
    logout_requested = pyqtSignal()
    access_changed = pyqtSignal()

    def __init__(self, portal):
        super().__init__()
        self.portal = portal
        self.user = portal.user.copy()
        self.initial_actions = portal.actions.copy()
        self.theme_mode = str(QApplication.instance().property("uslpTheme") or "light")
        self.activities = []
        self.tables, self.searches, self.status_filters, self.quick_buttons = {}, {}, {}, {}
        self.empty_states = {}
        self.audit_events = []
        self.recent_audit_entries = []
        self.activity_task = None
        self.activity_needs_refresh = False
        self.activity_error = None
        self.menu_buttons = []
        staff = self.user["staff"]
        self.lecturer = "Lecturer" in self.user["roles"]
        self.names = [
            "Dashboard",
            "Students" if staff else "My students" if self.lecturer else "My profile",
            "Courses" if staff else "My courses",
            "Enrolments" if staff else "My enrolments",
            "Analytics",
        ]
        self.sidebar_expanded = False
        self.sidebar_target_expanded = False
        self.revision = 0
        self.pending = None
        self.pending_revision = None
        self.empty_snapshot_streak = 0
        self.pending_action = None
        self.poll_timer = QTimer(self)
        # Poll gently in the background. Explicit page changes still trigger a
        # background refresh immediately while keeping the cached page usable.
        self.poll_timer.setInterval(15000)
        self.poll_timer.timeout.connect(self.poll)
        self.setup_ui()
        self.display()
        self.load_recent_activity()
        if not portal.preview:
            self.mark_updated()
            self.poll_timer.start()

    def setup_ui(self):
        main = QHBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)
        sidebar = QFrame()
        self.sidebar = sidebar
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(72)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(12, 18, 12, 16)
        nav.setSpacing(7)
        brand = QHBoxLayout()
        brand.addWidget(cap_badge(36))
        self.brand_title = QLabel("USLP")
        self.brand_title.setObjectName("sidebarLogo")
        self.brand_title.hide()
        brand.addWidget(self.brand_title)
        brand.addStretch()
        nav.addLayout(brand)
        nav.addSpacing(18)
        main_section = QLabel("MAIN")
        main_section.setObjectName("sidebarSection")
        main_section.hide()
        nav.addWidget(main_section)
        self.main_section_label = main_section
        self.nav_kinds = ("dashboard", "students", "courses", "enrollments", "analytics")
        self.menu_page_indices = []
        nav_order = (0, 4, 1, 2, 3)
        for page_index in nav_order:
            title = self.names[page_index]
            button = PortalButton(title, "quiet")
            button.setObjectName("sidebarNavButton")
            button.setAccessibleName(title)
            button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            kind = self.nav_kinds[page_index]
            button.setIcon(sidebar_icon(kind))
            button.setIconSize(QSize(20, 20))
            button.setToolTip(title)
            button.setProperty("collapsed", True)
            button.setProperty("active", False)
            button.setText("")
            button.clicked.connect(lambda checked=False, idx=page_index: self.open_page(idx))
            nav.addWidget(button)
            self.menu_buttons.append(button)
            self.menu_page_indices.append(page_index)
            if page_index == 4:
                records_section = QLabel("RECORDS")
                records_section.setObjectName("sidebarSection")
                records_section.hide()
                nav.addWidget(records_section)
                self.records_section_label = records_section
        nav.addStretch()
        logout = PortalButton("Exit preview" if self.portal.preview else "Logout", "danger")
        self.logout_button = logout
        logout.setObjectName("sidebarNavButton")
        logout.setIcon(sidebar_icon("logout"))
        logout.setIconSize(QSize(20, 20))
        logout.setAccessibleName("Exit preview" if self.portal.preview else "Log out")
        logout.setToolTip(logout.accessibleName())
        logout.setText("")
        logout.setProperty("collapsed", True)
        logout.clicked.connect(self.logout_requested.emit)
        nav.addWidget(logout)
        self.collapse_timer = QTimer(self)
        self.collapse_timer.setSingleShot(True)
        self.collapse_timer.setInterval(170)
        self.collapse_timer.timeout.connect(self._collapse_sidebar_if_outside)
        self.sidebar_animation = QVariantAnimation(self)
        self.sidebar_animation.setDuration(230)
        self.sidebar_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.sidebar_animation.valueChanged.connect(lambda width: self.sidebar.setFixedWidth(int(width)))
        self.sidebar_animation.finished.connect(self._finish_sidebar_animation)
        for widget in [sidebar, *sidebar.findChildren(QWidget)]:
            widget.installEventFilter(self)
        panel = WarmCanvas(dark=self.theme_mode == "dark")
        panel.setObjectName("contentArea")
        content = QVBoxLayout(panel)
        content.setContentsMargins(30, 22, 30, 24)
        content.setSpacing(16)
        bar = QHBoxLayout()
        self.heading = QLabel("Dashboard")
        self.heading.setObjectName("pageHeading")
        bar.addWidget(self.heading)
        # Notification bell in the top bar
        self.notification_button = PortalButton("🔔 0", "secondary")
        self.notification_button.setObjectName("notificationButton")
        self.notification_button.setAccessibleName("View notifications")
        self.notification_button.setToolTip("Click to view notifications")
        self.notification_button.clicked.connect(self.open_notifications)
        bar.addWidget(self.notification_button)
        bar.addStretch()
        self.global_search = QLineEdit()
        self.global_search.setMaximumWidth(230)
        self.global_search.setPlaceholderText("Search loaded records · Ctrl+K")
        self.global_search.setAccessibleName("Search loaded student, course and enrolment records")
        self.global_search.returnPressed.connect(self.search_records)
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.search_shortcut.activated.connect(self.global_search.setFocus)
        bar.addWidget(self.global_search)
        self.appearance_toggle = PortalButton(
            "", "secondary"
        )
        self.appearance_toggle.setObjectName("appearanceToggle")
        self.appearance_toggle.setIconSize(QSize(20, 20))
        self.appearance_toggle.setFixedSize(40, 38)
        self.update_theme_icon()
        self.appearance_toggle.clicked.connect(self.toggle_theme)
        bar.addWidget(self.appearance_toggle)
        self.sync_label = QLabel("Offline preview · changes stay in this window" if self.portal.preview else "")
        self.sync_label.setObjectName("syncStatus")
        self.sync_label.setTextFormat(Qt.TextFormat.PlainText)
        self.sync_label.setMaximumWidth(175)
        bar.addWidget(self.sync_label)
        identity = QVBoxLayout()
        for value, style in [(self.user["name"], "userName"), (" · ".join(self.user["roles"]), "userRole")]:
            lab = QLabel(value)
            lab.setTextFormat(Qt.TextFormat.PlainText)
            lab.setObjectName(style)
            identity.addWidget(lab)
        identity_widget = QWidget()
        identity_widget.setMaximumWidth(155)
        identity_widget.setObjectName("identityCard")
        identity_widget.setLayout(identity)
        bar.addWidget(identity_widget)
        content.addLayout(bar)
        divider = QFrame()
        divider.setObjectName("headerSeparator")
        divider.setFixedHeight(1)
        content.addWidget(divider)
        self.pages = QStackedWidget()
        self.dashboard_widget = self.dashboard()
        self.pages.addWidget(self.dashboard_widget)
        self.record_page_widgets = {}
        for idx, key in enumerate(HEADERS, 1):
            record_page = self.record_page(key, self.names[idx])
            self.record_page_widgets[key] = record_page
            self.pages.addWidget(record_page)
        self.analytics_widget = self.analytics_page()
        self.analytics_index = self.pages.addWidget(self.analytics_widget)
        self.page_effects = {}
        self.page_fade = None
        content.addWidget(self.pages)
        main.addWidget(sidebar)
        main.addWidget(panel)
        self.show_page(0)

    def update_theme_icon(self):
        moon_color = "#FFFFFF" if self.theme_mode == "dark" else "#17365D"
        self.appearance_toggle.setText("")
        self.appearance_toggle.setIcon(moon_icon(moon_color))
        self.appearance_toggle.setToolTip("Toggle theme")
        self.appearance_toggle.setAccessibleName(
            "Switch to light mode" if self.theme_mode == "dark" else "Switch to dark mode"
        )

    def toggle_theme(self):
        self.theme_mode = "dark" if self.theme_mode == "light" else "light"
        app = QApplication.instance()
        app.setProperty("uslpTheme", self.theme_mode)
        app.setStyleSheet(application_stylesheet(self.theme_mode))
        QSettings("USLP", "StudentLearningPortal").setValue("appearance", self.theme_mode)
        for canvas in self.findChildren(WarmCanvas):
            canvas.set_dark(self.theme_mode == "dark")
        for chart in (self.enrollment_chart, self.analytics_enrollment_chart,
                      self.programme_chart, self.student_status_chart,
                      self.semester_chart, self.course_enrolment_chart, self.analytics_distribution_chart):
            chart.set_dark(self.theme_mode == "dark")
        self.update_theme_icon()

    def eventFilter(self, watched, event):
        if watched is self.sidebar or self.sidebar.isAncestorOf(watched):
            if event.type() in (QEvent.Type.Enter, QEvent.Type.FocusIn):
                self.collapse_timer.stop()
                self.set_sidebar_expanded(True)
            elif event.type() in (QEvent.Type.Leave, QEvent.Type.FocusOut):
                self.collapse_timer.start()
        return super().eventFilter(watched, event)

    def set_sidebar_expanded(self, expanded):
        expanded = bool(expanded)
        if expanded == self.sidebar_target_expanded and self.sidebar_animation.state() == QVariantAnimation.State.Running:
            return
        if expanded == self.sidebar_expanded and self.sidebar_animation.state() != QVariantAnimation.State.Running:
            return
        self.sidebar_target_expanded = expanded
        if expanded:
            self.brand_title.show()
            self.main_section_label.show()
            self.records_section_label.show()
            for button, page_index in zip(self.menu_buttons, self.menu_page_indices):
                title = self.names[page_index]
                button.setText(title)
                button.setToolTip("")
                button.setProperty("collapsed", False)
                button.style().unpolish(button)
                button.style().polish(button)
            self.logout_button.setText(self.logout_button.accessibleName())
            self.logout_button.setToolTip("")
            self.logout_button.setProperty("collapsed", False)
            self.logout_button.style().unpolish(self.logout_button)
            self.logout_button.style().polish(self.logout_button)
        self.sidebar_animation.stop()
        self.sidebar_animation.setStartValue(self.sidebar.width())
        self.sidebar_animation.setEndValue(232 if expanded else 72)
        self.sidebar_animation.start()

    def _finish_sidebar_animation(self):
        self.sidebar_expanded = self.sidebar_target_expanded
        if self.sidebar_expanded:
            return
        self.brand_title.hide()
        self.main_section_label.hide()
        self.records_section_label.hide()
        for button in self.menu_buttons:
            button.setText("")
            button.setToolTip(button.accessibleName())
            button.setProperty("collapsed", True)
            button.style().unpolish(button)
            button.style().polish(button)
        self.logout_button.setText("")
        self.logout_button.setToolTip(self.logout_button.accessibleName())
        self.logout_button.setProperty("collapsed", True)
        self.logout_button.style().unpolish(self.logout_button)
        self.logout_button.style().polish(self.logout_button)

    def _collapse_sidebar_if_outside(self):
        pointer_inside = self.sidebar.rect().contains(self.sidebar.mapFromGlobal(QCursor.pos()))
        focus = QApplication.focusWidget()
        focus_inside = bool(focus and (focus is self.sidebar or self.sidebar.isAncestorOf(focus)))
        if not pointer_inside and not focus_inside:
            self.set_sidebar_expanded(False)

    def dashboard(self):
        page = QFrame()
        page.setObjectName("dashboardPage")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(2, 16, 2, 18)
        lay.setSpacing(15)
        welcome = QLabel("Welcome, " + self.user["name"])
        welcome.setTextFormat(Qt.TextFormat.PlainText)
        welcome.setObjectName("welcomeHeading")
        lay.addWidget(welcome)
        staff = self.user["staff"]
        description = QLabel(
            "University academic records" if staff else
            "Your assigned teaching and class records" if self.lecturer else
            "Your student record, courses and learning progress"
        )
        description.setObjectName("panelDescription")
        lay.addWidget(description)
        if self.portal.preview:
            demo_note = QLabel("Demonstration mode · fictional records held in memory")
            demo_note.setObjectName("noticeSummary")
            lay.addWidget(demo_note)

        hero = PortalCard("heroCard")
        hero_row = QHBoxLayout()
        hero_row.setSpacing(20)
        hero_copy = QVBoxLayout()
        self.hero_title = QLabel("Your academic progress at a glance" if not staff
                                 else "Academic records at a glance")
        self.hero_title.setObjectName("heroTitle")
        self.hero_title.setWordWrap(True)
        hero_copy.addWidget(self.hero_title)
        self.hero_description = QLabel(
            "See your current courses, enrolments and recorded lesson progress."
            if not staff else "Review the records and activity currently available to your account."
        )
        self.hero_description.setObjectName("heroCopy")
        self.hero_description.setWordWrap(True)
        hero_copy.addWidget(self.hero_description)
        self.hero_progress_label = QLabel("Lesson completion is not available in this snapshot.")
        self.hero_progress_label.setObjectName("heroMeta")
        self.hero_progress_label.setWordWrap(True)
        hero_copy.addWidget(self.hero_progress_label)
        hero_actions = QHBoxLayout()
        analytics_action = PortalButton("View analytics")
        analytics_action.setObjectName("heroButton")
        analytics_action.clicked.connect(lambda: self.open_page(self.analytics_index))
        enrolments_action = PortalButton("Open enrolments", "secondary")
        enrolments_action.setObjectName("heroButton")
        enrolments_action.clicked.connect(lambda: self.open_page(3))
        hero_actions.addWidget(analytics_action)
        hero_actions.addWidget(enrolments_action)
        hero_actions.addStretch()
        hero_copy.addLayout(hero_actions)
        hero_row.addLayout(hero_copy, 1)
        self.hero_ring = ProgressRing()
        hero_row.addWidget(self.hero_ring, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        hero.content_layout.addLayout(hero_row)
        lay.addWidget(hero)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        self.stats = []
        self.stat_notes = []
        if staff:
            labels = ["Total students", "Active lecturers", "Total courses", "Total enrolments"]
        elif self.lecturer:
            labels = ["My students", "My courses", "My enrolments", "In progress"]
        else:
            labels = ["Student ID", "My courses", "My enrolments", "Completed enrolments"]
        for i, title in enumerate(labels):
            card = PortalCard("primaryStat" if i == 0 else "statCard")
            box = card.content_layout
            caption = QLabel(title)
            caption.setObjectName("cardTitle")
            value = QLabel()
            value.setObjectName("cardValue")
            note = QLabel()
            note.setObjectName("panelDescription")
            box.addWidget(caption)
            box.addWidget(value)
            box.addWidget(note)
            if i:
                card.setProperty("statTone", ("teal", "gold", "violet")[(i - 1) % 3])
            grid.addWidget(card, 0, i)
            self.stats.append(value)
            self.stat_notes.append(note)
        lay.addLayout(grid)

        actions = PortalCard("panelCard")
        buttons = QGridLayout()
        buttons.setSpacing(8)
        actions.content_layout.addLayout(buttons)
        button_index = 0

        def add_quick_button(button):
            nonlocal button_index
            buttons.addWidget(button, button_index // 3, button_index % 3)
            button_index += 1

        for action, page_index, text in [
            ("add_student", 1, "Register student"),
            ("add_course", 2, "Add course"),
            ("add_enrollment", 3, "Create enrolment"),
        ]:
            if action in self.portal.actions:
                btn = PortalButton(text, "secondary")
                btn.setObjectName("quickButton")
                btn.clicked.connect(lambda checked=False, a=action, p=page_index: self.quick_action(p, a))
                add_quick_button(btn)
                self.quick_buttons[action] = btn
        manage = PortalButton("Manage enrolments", "secondary")
        manage.setObjectName("quickButton")
        manage.clicked.connect(lambda: self.open_page(3))
        add_quick_button(manage)
        self.quick_buttons["manage_enrollments"] = manage
        reports = PortalButton("View reports", "secondary")
        reports.setObjectName("quickButton")
        reports.clicked.connect(self.open_report)
        add_quick_button(reports)
        self.quick_buttons["view_reports"] = reports
        refresh = PortalButton("Refresh overview", "secondary")
        refresh.setObjectName("quickButton")
        refresh.clicked.connect(self.refresh_overview)
        add_quick_button(refresh)
        self.quick_buttons["refresh"] = refresh
        if staff:
            audit = PortalButton("Audit log", "secondary")
            audit.setObjectName("quickButton")
            audit.clicked.connect(self.open_audit_log)
            add_quick_button(audit)
            self.quick_buttons["audit_log"] = audit
        lay.addWidget(actions)

        analytics = QGridLayout()
        analytics.setHorizontalSpacing(14)
        analytics.setVerticalSpacing(14)

        def chart_card(title, subtitle, chart):
            card = PortalCard("panelCard")
            heading = QLabel(title)
            heading.setObjectName("panelHeading")
            card.content_layout.addWidget(heading)
            note = QLabel(subtitle)
            note.setObjectName("panelDescription")
            note.setWordWrap(True)
            card.content_layout.addWidget(note)
            card.content_layout.addWidget(chart)
            return card

        self.programme_chart = BreakdownChart()
        self.student_status_chart = DonutChart()
        self.semester_chart = BreakdownChart()
        self.course_enrolment_chart = DonutChart()
        self.enrollment_chart = EnrollmentChart()
        analytics.addWidget(chart_card(
            "Students by programme", "Distribution in the records visible to your account", self.programme_chart
        ), 0, 0)
        analytics.addWidget(chart_card(
            "Student status", "Current status in the loaded student records", self.student_status_chart
        ), 0, 1)
        analytics.addWidget(chart_card(
            "Enrolments by semester", "Terms represented in the current enrolment records", self.semester_chart
        ), 1, 0)
        analytics.addWidget(chart_card(
            "Enrolments by course", "Current enrolment counts grouped by course", self.course_enrolment_chart
        ), 1, 1)
        analytics.addWidget(chart_card(
            "Enrolment status", "In progress, completed and withdrawn records", self.enrollment_chart
        ), 2, 0)

        performance = PortalCard("panelCard")
        performance_heading = QLabel("Academic performance")
        performance_heading.setObjectName("panelHeading")
        performance.content_layout.addWidget(performance_heading)
        performance_note = QLabel(
            "Grades and assessment marks are not included in the current API. "
            "Lesson completion is shown separately and is not a grade."
        )
        performance_note.setObjectName("panelDescription")
        performance_note.setWordWrap(True)
        performance.content_layout.addWidget(performance_note)
        self.academic_summary = QLabel()
        self.academic_summary.setObjectName("noticeSummary")
        self.academic_summary.setWordWrap(True)
        performance.content_layout.addWidget(self.academic_summary)
        analytics.addWidget(performance, 2, 1)

        notices = PortalCard("panelCard")
        notices_heading = QLabel("Notifications and record checks")
        notices_heading.setObjectName("panelHeading")
        notices.content_layout.addWidget(notices_heading)
        self.notice_summary = QLabel()
        self.notice_summary.setObjectName("panelDescription")
        self.notice_summary.setWordWrap(True)
        notices.content_layout.addWidget(self.notice_summary)
        self.notification_list = QListWidget()
        self.notification_list.setObjectName("activityList")
        notices.content_layout.addWidget(self.notification_list)
        analytics.addWidget(notices, 3, 0, 1, 2)
        lay.addLayout(analytics)

        activity = PortalCard("panelCard")
        activity_lay = activity.content_layout
        self.activity_heading = QLabel("Recent activity")
        self.activity_heading.setObjectName("panelHeading")
        activity_lay.addWidget(self.activity_heading)
        activity_note = QLabel("Newest first · sourced from the audit log for staff, or this session in preview mode")
        activity_note.setObjectName("panelDescription")
        activity_note.setWordWrap(True)
        activity_lay.addWidget(activity_note)
        self.activity_list = QListWidget()
        self.activity_list.setObjectName("activityList")
        activity_lay.addWidget(self.activity_list)
        lay.addWidget(activity)
        lay.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        # Keep references for the notification button
        self.dashboard_scroll = scroll
        self.notifications_card = notices
        return scroll

    def analytics_page(self):
        page = QFrame()
        page.setObjectName("dashboardPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(2, 16, 2, 18)
        layout.setSpacing(14)
        header = QHBoxLayout()
        title = QLabel("Analytics")
        title.setObjectName("welcomeHeading")
        header.addWidget(title)
        header.addStretch()
        download = PortalButton("Download report", "secondary")
        download.clicked.connect(self.export_report)
        header.addWidget(download)
        layout.addLayout(header)
        note = QLabel("Explore counts calculated from records currently available to your account.")
        note.setObjectName("panelDescription")
        layout.addWidget(note)
        loading_row = QHBoxLayout()
        self.analytics_loading = QLabel("Refreshing analytics from the current portal snapshot…")
        self.analytics_loading.setObjectName("analyticsLoading")
        self.analytics_loading.hide()
        self.analytics_progress = QProgressBar()
        self.analytics_progress.setRange(0, 0)
        self.analytics_progress.setTextVisible(False)
        self.analytics_progress.setFixedWidth(120)
        self.analytics_progress.setObjectName("analyticsProgress")
        self.analytics_progress.hide()
        loading_row.addWidget(self.analytics_loading)
        loading_row.addWidget(self.analytics_progress)
        loading_row.addStretch()
        layout.addLayout(loading_row)

        self.analytics_stats = []
        stat_row = QGridLayout()
        stat_row.setHorizontalSpacing(10)
        for column, label_text in enumerate(("Students", "Active lecturers", "Courses", "Enrolments")):
            card = PortalCard("primaryStat" if column == 0 else "statCard")
            label = QLabel(label_text)
            label.setObjectName("cardTitle")
            value = QLabel("—")
            value.setObjectName("cardValue")
            hint = QLabel("Current snapshot")
            hint.setObjectName("panelDescription")
            card.content_layout.addWidget(label)
            card.content_layout.addWidget(value)
            card.content_layout.addWidget(hint)
            stat_row.addWidget(card, 0, column)
            self.analytics_stats.append((value, hint))
        layout.addLayout(stat_row)

        distribution_card = PortalCard("panelCard")
        distribution_header = QHBoxLayout()
        distribution_title = QLabel("Record distribution")
        distribution_title.setObjectName("panelHeading")
        distribution_header.addWidget(distribution_title)
        distribution_header.addStretch()
        self.analytics_mode_buttons = {}
        segment = QWidget()
        segment.setObjectName("analyticsRange")
        segment_layout = QHBoxLayout(segment)
        segment_layout.setContentsMargins(3, 3, 3, 3)
        segment_layout.setSpacing(2)
        for mode, text in (("programmes", "Programmes"), ("statuses", "Student status"),
                           ("semesters", "Semesters")):
            button = PortalButton(text, "secondary")
            button.setObjectName("analyticsModeButton")
            button.setProperty("active", mode == "programmes")
            button.clicked.connect(lambda checked=False, current=mode: self.set_analytics_mode(current))
            segment_layout.addWidget(button)
            self.analytics_mode_buttons[mode] = button
        distribution_header.addWidget(segment)
        distribution_card.content_layout.addLayout(distribution_header)
        self.analytics_distribution_chart = DonutChart()
        distribution_card.content_layout.addWidget(self.analytics_distribution_chart)
        distribution_note = QLabel("Charts use the loaded student and enrolment records; they do not imply a date range.")
        distribution_note.setObjectName("panelDescription")
        distribution_note.setWordWrap(True)
        distribution_card.content_layout.addWidget(distribution_note)
        layout.addWidget(distribution_card)

        lower = QGridLayout()
        lower.setHorizontalSpacing(14)
        enrolment_card = PortalCard("panelCard")
        enrolment_title = QLabel("Enrolment status")
        enrolment_title.setObjectName("panelHeading")
        enrolment_card.content_layout.addWidget(enrolment_title)
        self.analytics_enrollment_chart = EnrollmentChart()
        enrolment_card.content_layout.addWidget(self.analytics_enrollment_chart)
        lower.addWidget(enrolment_card, 0, 0)
        progress_card = PortalCard("panelCard")
        progress_title = QLabel("Academic progress")
        progress_title.setObjectName("panelHeading")
        progress_card.content_layout.addWidget(progress_title)
        self.analytics_academic_summary = QLabel()
        self.analytics_academic_summary.setObjectName("noticeSummary")
        self.analytics_academic_summary.setWordWrap(True)
        progress_card.content_layout.addWidget(self.analytics_academic_summary)
        progress_note = QLabel("Assessment grades are not included in the current API snapshot.")
        progress_note.setObjectName("panelDescription")
        progress_note.setWordWrap(True)
        progress_card.content_layout.addWidget(progress_note)
        lower.addWidget(progress_card, 0, 1)
        layout.addLayout(lower)
        layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        return scroll

    def set_analytics_mode(self, mode):
        if mode not in {"programmes", "statuses", "semesters"}:
            return
        self.analytics_mode = mode
        for key, button in self.analytics_mode_buttons.items():
            button.setProperty("active", key == mode)
            button.style().unpolish(button)
            button.style().polish(button)
        self._update_analytics_chart()

    def _update_analytics_chart(self):
        if not hasattr(self, "analytics_distribution_chart"):
            return
        students = list(self.portal.students.values())
        enrollments = list(self.portal.enrollments.values())
        values = {
            "programmes": Counter(s.programme or "Unspecified" for s in students),
            "statuses": Counter(s.status.title() or "Unspecified" for s in students),
            "semesters": Counter(e.term or "Unspecified" for e in enrollments),
        }
        self.analytics_distribution_chart.set_data(values.get(getattr(self, "analytics_mode", "programmes"), {}))

    def export_report(self):
        path, _ = QFileDialog.getSaveFileName(self, "Download snapshot report", "uslp-summary.csv", "CSV files (*.csv)")
        if not path:
            return
        lecturers = self.portal.lookups.get("lecturers")
        students = list(self.portal.students.values())
        courses = list(self.portal.courses.values())
        enrollments = list(self.portal.enrollments.values())
        rows = [
            ("Measure", "Value"),
            ("Students in snapshot", len(students)),
            ("Active students", sum(s.status.casefold() == "active" for s in students)),
            ("Active lecturers", len(lecturers) if lecturers is not None else "Not available"),
            ("Courses in snapshot", len(courses)),
            ("Enrolments in snapshot", len(enrollments)),
            ("Completed enrolments", sum(e.status.casefold() == "completed" for e in enrollments)),
        ]
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as output:
                csv.writer(output).writerows(rows)
        except OSError as error:
            QMessageBox.warning(self, "Report", f"The report could not be saved: {error}")
            return
        QMessageBox.information(self, "Report", "The snapshot summary was saved.")

    def record_page(self, key, title):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 18, 0, 0)
        layout.setSpacing(14)
        search_bar = QHBoxLayout()
        search = QLineEdit()
        search.setPlaceholderText("Search " + title.lower() + "…")
        search.setClearButtonEnabled(True)
        search.setAccessibleName("Search " + title.lower())
        search_bar.addWidget(search, 1)
        status_filter = None
        if key == "students":
            status_filter = QComboBox()
            status_filter.setAccessibleName("Filter students by status")
            status_filter.addItem("All statuses", "all")
            status_filter.addItem("Active", "active")
            status_filter.addItem("Inactive", "inactive")
            search_bar.addWidget(status_filter)
        layout.addLayout(search_bar)
        empty_state = QLabel()
        empty_state.setObjectName("emptyState")
        empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_state.setWordWrap(True)
        empty_state.hide()
        layout.addWidget(empty_state)
        self.empty_states[key] = empty_state
        table = QTableWidget(0, len(HEADERS[key]))
        table.setMouseTracking(True)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setHorizontalHeaderLabels(HEADERS[key])
        table.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setStretchLastSection(False)
        if key == "enrollments":
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        elif key == "students":
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        elif key == "courses":
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().hide()
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.verticalHeader().setDefaultSectionSize(42)
        table.setCornerButtonEnabled(False)
        layout.addWidget(table)
        self.tables[key], self.searches[key] = table, search
        if status_filter is not None:
            self.status_filters[key] = status_filter
            status_filter.currentIndexChanged.connect(lambda _index: self.filter_table(key, search.text()))
            table.cellDoubleClicked.connect(lambda _row, _column: self.view_selected_student())
        search.textChanged.connect(lambda value: self.filter_table(key, value))
        out = QHBoxLayout()
        for action, text in BUTTONS[key]:
            if action in self.portal.actions:
                destructive = action in {"delete_student", "delete_course", "delete_enrollment"}
                btn = PortalButton(text, "danger" if destructive else "secondary")
                btn.clicked.connect(lambda checked=False, a=action: self.perform(a))
                out.addWidget(btn)
        if key == "students":
            view = PortalButton("View profile", "secondary")
            view.clicked.connect(self.view_selected_student)
            out.addWidget(view)
            if self.user["staff"]:
                audit = PortalButton("Audit log", "secondary")
                audit.clicked.connect(self.open_audit_log)
                out.addWidget(audit)
        if key == "courses":
            options = [(a, t) for a, t in ACADEMIC if a in self.portal.actions]
            if options:
                academic = PortalButton("Academic setup", "secondary")
                menu = QMenu(academic)
                for action, text in options:
                    menu.addAction(text).triggered.connect(lambda checked=False, a=action: self.perform(a))
                academic.setMenu(menu)
                out.addWidget(academic)
        out.addStretch()
        refresh = PortalButton("Refresh", "secondary")
        refresh.clicked.connect(self.refresh_async)
        out.addWidget(refresh)
        layout.addLayout(out)
        return page

    def display(self):
        for key, table in self.tables.items():
            current = table.item(table.currentRow(), 0) if table.currentRow() >= 0 else None
            selected = current.data(Qt.ItemDataRole.UserRole) if current else None
            records = getattr(self.portal, key)
            table.setRowCount(len(records))
            table.clearSelection()
            for i, record in enumerate(records.values()):
                for j, value in enumerate(record.cells()):
                    item = QTableWidgetItem(value)

                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignLeft |
                        Qt.AlignmentFlag.AlignVCenter
                    )

                    item.setToolTip(value)

                    if j == 0:
                        item.setData(Qt.ItemDataRole.UserRole, record.id)
                    table.setItem(i, j, item)
                if record.id == selected:
                    table.selectRow(i)
            self.filter_table(key, self.searches[key].text())
            table.resizeColumnsToContents()

        students = list(self.portal.students.values())
        courses = list(self.portal.courses.values())
        enrollments = list(self.portal.enrollments.values())
        completed = sum(e.status.casefold() == "completed" for e in enrollments)
        active_lecturers = self.portal.lookups.get("lecturers")
        if self.user["staff"]:
            totals = [len(students), len(active_lecturers) if active_lecturers is not None else "—",
                      len(courses), len(enrollments)]
            notes = ["Records in your snapshot", "Active lecturer records" if active_lecturers is not None
                     else "Not provided for this account", "Available in your snapshot", "Current records"]
        elif self.lecturer:
            totals = [len(students), len(courses), len(enrollments),
                      sum(e.status.casefold() in {"enrolled", "active"} for e in enrollments)]
            notes = ["Assigned student records", "Courses available to you", "Your enrolment records",
                     "Enrolled or active"]
        else:
            student = next(iter(self.portal.students.values()), None)
            totals = [student.number if student else "—", len(courses), len(enrollments), completed]
            notes = ["Your student ID" if student else "Not available", "Courses in your snapshot",
                     "Your enrolment records", "Completed records"]
        for widget, value, note, note_text in zip(self.stats, totals, self.stat_notes, notes):
            widget.setText(str(value))
            note.setText(note_text)

        self.programme_chart.set_data(Counter(s.programme or "Unspecified" for s in students))
        self.student_status_chart.set_data(Counter(s.status.title() or "Unspecified" for s in students))
        self.semester_chart.set_data(Counter(e.term or "Unspecified" for e in enrollments))
        self.course_enrolment_chart.set_data(Counter(
            f"{e.course_code} Â· {e.course}" for e in enrollments
        ))
        self.enrollment_chart.set_records(enrollments)
        measurable = [e.progress for e in enrollments if e.progress is not None]
        average_progress = round(sum(measurable) / len(measurable)) if measurable else None
        self.academic_summary.setText(
            f"Completed enrolments: {completed} of {len(enrollments)}. "
            + (f"Average lesson completion: {average_progress}% across {len(measurable)} records."
               if measurable else "Lesson completion totals are unavailable for these enrolments.")
        )
        if measurable:
            self.hero_ring.show()
            self.hero_ring.set_value(average_progress)
            self.hero_progress_label.setText(
                f"Average lesson completion: {average_progress}% across {len(measurable)} enrolments."
            )
        else:
            self.hero_ring.hide()
            self.hero_progress_label.setText("Lesson totals are not available in the current records.")
        analytics_values = [len(students), len(active_lecturers) if active_lecturers is not None else "—",
                            len(courses), len(enrollments)]
        analytics_hints = ["Records in your account scope",
                           "Active lecturer records" if active_lecturers is not None else "Not available to this account",
                           "Records in your account scope", "Records in your account scope"]
        for (value_label, hint_label), value, hint in zip(self.analytics_stats, analytics_values, analytics_hints):
            value_label.setText(str(value))
            hint_label.setText(hint)
        self.analytics_enrollment_chart.set_records(enrollments)
        self.analytics_academic_summary.setText(
            f"{completed} of {len(enrollments)} enrolments completed. "
            + (f"Average recorded lesson completion is {average_progress}%."
               if measurable else "No measurable lesson totals are available.")
        )
        self._update_analytics_chart()

        checks = []
        inactive = sum(s.status.casefold() != "active" for s in students)
        withdrawn = sum(e.status.casefold() == "withdrawn" for e in enrollments)
        missing_lessons = sum(c.total_lessons is None for c in courses)
        if inactive:
            checks.append(f"{inactive} student record(s) are not active")
        if withdrawn:
            checks.append(f"{withdrawn} enrolment record(s) are withdrawn")
        if missing_lessons:
            checks.append(f"{missing_lessons} course(s) have no lesson total")
        self.notice_summary.setText(
            "Record checks from this snapshot; the current API does not provide server notifications."
        )
        self.notification_list.clear()
        self.notification_list.addItems(checks or ["No items need attention in the loaded records."])
        # Update the notification number in the top bar
        self.update_notification_badge()
        self.render_recent_activity()

    def open_notifications(self):
        """Open the dashboard and scroll to the notification section."""
        self.show_page(0)
        # Wait briefly for the dashboard page to become visible
        QTimer.singleShot(
            150,
            lambda: self.dashboard_scroll.ensureWidgetVisible(
                self.notifications_card, 0, 20
            )
        )

    def update_notification_badge(self):
        """Show the number of notifications in the top bar."""
        no_notifications_message = (
            "No items need attention in the loaded records."
        )
        count = self.notification_list.count()
        # Do not count the empty-state message as a notification
        if (
            count == 1
            and self.notification_list.item(0).text()
            == no_notifications_message
        ):
            count = 0
        self.notification_button.setText(f"🔔 {count}")
        self.notification_button.setToolTip(
            f"{count} notification(s). Click to view."
        )

    def search_records(self):
        query = self.global_search.text().strip().casefold()
        if not query:
            return
        for index, key in enumerate(("students", "courses", "enrollments"), 1):
            table = self.tables[key]
            for row in range(table.rowCount()):
                cells = [table.item(row, column).text() for column in range(table.columnCount())
                         if table.item(row, column)]
                if query in " ".join(cells).casefold():
                    self.show_page(index)
                    if key == "students" and key in self.status_filters:
                        self.status_filters[key].setCurrentIndex(0)
                    self.searches[key].setText(self.global_search.text())
                    table.selectRow(row)
                    table.setFocus()
                    self.sync_label.setText("Showing a match in loaded records")
                    return
        self.sync_label.setText("No matches in the records currently loaded")

    def open_report(self):
        DashboardReportDialog(self, self.portal).exec()

    def refresh_overview(self):
        self.refresh_async()
        self.load_recent_activity()

    def load_recent_activity(self):
        if self.portal.preview or not self.user["staff"]:
            self.render_recent_activity()
            return
        if self.activity_task is not None:
            self.activity_needs_refresh = True
            return
        self.activity_error = None
        self.activity_task = AuditLogTask(self.portal, 8, 0)
        self.activity_task.signals.finished.connect(self.recent_activity_loaded)
        QThreadPool.globalInstance().start(self.activity_task)

    @pyqtSlot(object)
    def recent_activity_loaded(self, result):
        self.activity_task = None
        if isinstance(result, PortalError):
            self.activity_error = str(result)
            self.recent_audit_entries = []
        else:
            self.activity_error = None
            self.recent_audit_entries = list(result.get("entries", []))
        self.render_recent_activity()
        if self.activity_needs_refresh:
            self.activity_needs_refresh = False
            self.load_recent_activity()

    def render_recent_activity(self):
        if not hasattr(self, "activity_list"):
            return
        self.activity_list.clear()
        if self.portal.preview or not self.user["staff"] or self.activity_error:
            rows = sorted(self.audit_events, key=lambda entry: entry.get("time", ""), reverse=True)
            self.activity_heading.setText("Recent activity this session")
            if self.activity_error and self.user["staff"] and not rows:
                self.activity_list.addItem("Persistent activity is temporarily unavailable.")
            else:
                for entry in rows[:8]:
                    line = f"{entry.get('time', '')}  ·  {entry.get('account', '')}  ·  " \
                           f"{entry.get('action', '')}  ·  {entry.get('record', '')}"
                    item = QListWidgetItem(line)
                    item.setToolTip(entry.get("details", ""))
                    self.activity_list.addItem(item)
                if not rows:
                    self.activity_list.addItem("No activity recorded in this session yet.")
            return
        self.activity_heading.setText("Recent system activity")
        for entry in self.recent_audit_entries[:8]:
            when = AuditLogDialog.format_value(entry.get("occurred_at"))
            actor = entry.get("actor_name") or entry.get("database_user") or "Unknown account"
            username = entry.get("actor_username")
            if username:
                actor += f" ({username})"
            operation = str(entry.get("operation") or "Activity").replace("_", " ").title()
            table = str(entry.get("table_name") or "record").replace("_", " ").title()
            record = AuditLogDialog.format_value(entry.get("record_key"))
            item = QListWidgetItem(f"{when}  ·  {actor}  ·  {operation} {table}  ·  {record}")
            item.setToolTip(
                f"Account: {actor}\nOperation: {operation}\nRecord: {record}\n"
                f"Before: {AuditLogDialog.format_value(entry.get('old_data'))}\n"
                f"After: {AuditLogDialog.format_value(entry.get('new_data'))}"
            )
            self.activity_list.addItem(item)
        if not self.recent_audit_entries:
            self.activity_list.addItem("No persistent activity records are available yet.")

    def filter_table(self, key, value):
        table = self.tables[key]
        query = value.casefold().strip()
        visible_rows = 0
        for i in range(table.rowCount()):
            cells = [table.item(i, j).text() for j in range(table.columnCount()) if table.item(i, j)]
            matches_query = query in " ".join(cells).casefold()
            status_filter = self.status_filters.get(key)
            matches_status = (
                status_filter is None
                or status_filter.currentData() == "all"
                or (table.item(i, 4) and table.item(i, 4).text().casefold() == status_filter.currentData())
            )
            visible = matches_query and matches_status
            table.setRowHidden(i, not visible)
            visible_rows += int(visible)
        empty = self.empty_states.get(key)
        if empty is not None:
            singular = {"students": "student", "courses": "course", "enrollments": "enrolment"}[key]
            empty.setText(
                f"No {singular} records are available in this account's snapshot."
                if table.rowCount() == 0 else
                f"No {singular} records match the current search or filters."
            )
            empty.setVisible(visible_rows == 0)

    def view_selected_student(self):
        try:
            student = self.selected("students")
        except PortalError as error:
            self.handle_error(error)
            return
        StudentProfileDialog(self, student, list(self.portal.enrollments.values())).exec()

    def open_audit_log(self):
        if self.user["staff"]:
            AuditLogDialog(self, self.portal, self.audit_events).exec()

    def make_audit_entry(self, action, fields, result, happened_at):
        if action == "complete_lesson":
            entity_key = "enrollments"
        else:
            entity_key = next(
                (key for token, key in (("student", "students"), ("course", "courses"),
                                        ("enrollment", "enrollments")) if token in action),
                None,
            )
        record_id = result.get("id")
        record = getattr(self.portal, entity_key, {}).get(fields.get("id")) if entity_key else None
        entity_names = {"students": "Student", "courses": "Course", "enrollments": "Enrolment"}
        record_names = {"students": "number", "courses": "code", "enrollments": "id"}
        if record is not None:
            record_name = getattr(record, record_names[entity_key])
            details = " · ".join(record.cells())
            if action.startswith("edit_"):
                changed_values = {key: value for key, value in fields.items()
                                  if key not in {"id", "version", "expected"}}
                details += " · Submitted changes: " + ", ".join(
                    f"{key}: {value}" for key, value in changed_values.items()
                )
            elif action == "deactivate_student":
                details += " · Status changed to inactive"
            elif action == "reactivate_student":
                details += " · Status changed to active"
        else:
            record_name = fields.get("number") or fields.get("code") or fields.get("name") or str(record_id)
            safe_fields = {key: value for key, value in fields.items()
                           if key not in {"version", "expected", "password"}}
            details = ", ".join(f"{key}: {value}" for key, value in safe_fields.items())
        roles = ", ".join(self.user.get("roles", [])) or "Unknown role"
        username = self.user.get("username", "unknown account")
        return {
            "time": happened_at.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "account": f"{self.user.get('name', username)} ({username})",
            "role": roles,
            "action": TITLES.get(action, action.replace("_", " ").title()),
            "record": f"{entity_names.get(entity_key, 'Academic record')} · {record_name} · #{record_id}",
            "details": details,
        }

    def show_page(self, index):
        if not 0 <= index < self.pages.count():
            return
        changed_page = self.pages.currentIndex() != index
        if changed_page:
            page = self.pages.widget(index)
            effect = self.page_effects.get(index)
            if effect is None:
                effect = QGraphicsOpacityEffect(page)
                # page.setGraphicsEffect(effect)
                self.page_effects[index] = effect
            if self.page_fade is not None:
                self.page_fade.stop()
                self.page_fade.setTargetObject(effect)
            effect.setOpacity(0.0)
        self.pages.setCurrentIndex(index)
        if changed_page:
            if self.page_fade is None:
                self.page_fade = QPropertyAnimation(effect, b"opacity", self)
                self.page_fade.setDuration(145)
                self.page_fade.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.page_fade.setStartValue(0.0)
            self.page_fade.setEndValue(1.0)
            self.page_fade.start()
        self.heading.setText(self.names[index])
        for button, page_index in zip(self.menu_buttons, self.menu_page_indices):
            button.setProperty("active", page_index == index)
            button.setIcon(sidebar_icon(self.nav_kinds[page_index],
                                        "#17191D" if page_index == index else "#E5EDF5"))
            button.style().unpolish(button)
            button.style().polish(button)

    def open_page(self, index):
        self.show_page(index)
        if index == 0:
            self.load_recent_activity()
        elif index == self.analytics_index and not self.portal.preview:
            self.set_analytics_loading(True)
        if not self.portal.preview:
            self.refresh_async()

    def set_analytics_loading(self, active):
        self.analytics_loading.setVisible(bool(active))
        self.analytics_progress.setVisible(bool(active))

    def quick_action(self, page, action):
        self.show_page(page)
        if self.pending_action is not None:
            return
        if self.portal.preview:
            self.perform(action)
        else:
            self.pending_action = action
            self.refresh_async()

    def stop_sync(self):
        self.poll_timer.stop()
        self.revision += 1

    def mark_updated(self):
        if not self.portal.preview:
            self.sync_label.setText("Updated " + datetime.now().strftime("%H:%M:%S"))

    def poll(self):
        if self.pending is not None or not self.isVisible() or QApplication.activeModalWidget() is not None:
            return
        self.start_snapshot_task()

    def refresh_async(self):
        """Request a current snapshot without blocking page navigation."""
        if self.portal.preview:
            self.refresh()
            return
        if self.pages.currentIndex() == self.analytics_index:
            self.set_analytics_loading(True)
        if self.pending is None:
            self.sync_label.setText("Refreshing · showing last update")
            self.start_snapshot_task()

    def start_snapshot_task(self):
        # A single worker owns the pending slot. In particular, a stale task's
        # completion must never make a newer request look idle.
        if self.pending is not None:
            return
        if self.pages.currentIndex() == self.analytics_index:
            self.set_analytics_loading(True)
        self.revision += 1
        self.pending_revision = self.revision
        self.pending = SnapshotTask(self.portal, self.revision)
        self.pending.signals.finished.connect(self.poll_finished)
        QThreadPool.globalInstance().start(self.pending)

    @pyqtSlot(int, object)
    def poll_finished(self, revision, outcome):
        if revision == self.pending_revision:
            self.pending = None
            self.pending_revision = None
            self.set_analytics_loading(False)
        # A newer foreground read/write, a sign-out or an open form takes precedence.
        if revision != self.revision or not self.poll_timer.isActive() or QApplication.activeModalWidget() is not None:
            return
        if isinstance(outcome, PortalError):
            self.empty_snapshot_streak = 0
            action_requested = self.pending_action is not None
            self.pending_action = None
            if outcome.status in (401, 403) or action_requested:
                self.handle_error(outcome)
            else:
                self.sync_label.setText("Reconnecting · showing last update")
            return
        try:
            # A complete, successful response with every collection suddenly
            # empty can happen while the live service is being updated. Keep
            # showing the last good snapshot until that same state is confirmed.
            # The warning stays visible; no fake records are introduced.
            snapshot_dropped_records = isinstance(outcome, dict) and any(
                isinstance(outcome.get(key), list) and not outcome[key] and getattr(self.portal, key)
                for key in ("students", "courses", "enrollments")
            )
            actions = outcome.get("actions") if isinstance(outcome, dict) else None
            same_access = (
                isinstance(actions, (list, tuple, set))
                and outcome.get("user") == self.portal.user
                and set(actions) == self.portal.actions
            )
            if snapshot_dropped_records and same_access:
                self.empty_snapshot_streak += 1
                if self.empty_snapshot_streak < 3:
                    self.sync_label.setText(
                        f"Server snapshot is empty ({self.empty_snapshot_streak}/3) Â· showing last update"
                    )
                    self.pending_action = None
                    return
            else:
                self.empty_snapshot_streak = 0
            changed = self.portal.apply_snapshot(outcome)
            self.empty_snapshot_streak = 0
        except PortalError as error:
            self.pending_action = None
            self.sync_label.setText(str(error))
            return
        if self.show_snapshot(changed) and self.pending_action is not None:
            action, self.pending_action = self.pending_action, None
            self.perform(action)

    def show_snapshot(self, changed):
        if self.user != self.portal.user or self.initial_actions != self.portal.actions:
            self.stop_sync()
            self.access_changed.emit()
            return False
        if changed:
            self.display()
            if self.pages.currentIndex() == 0:
                self.load_recent_activity()
        self.mark_updated()
        return True

    def handle_error(self, error):
        if error.status in (401, 403):
            self.stop_sync()
        if error.status == 503 and not self.portal.preview:
            self.sync_label.setText("Connection interrupted · showing last update")
        QMessageBox.warning(self, "Portal", str(error))
        if error.status in (401, 403):
            self.logout_requested.emit()

    def should_hold_empty_snapshot(self, data):
        """Retain visible records until an all-empty live snapshot is confirmed."""
        dropped_records = isinstance(data, dict) and any(
            isinstance(data.get(key), list) and not data[key] and getattr(self.portal, key)
            for key in ("students", "courses", "enrollments")
        )
        actions = data.get("actions") if isinstance(data, dict) else None
        same_access = (
            isinstance(actions, (list, tuple, set))
            and data.get("user") == self.portal.user
            and set(actions) == self.portal.actions
        )
        if dropped_records and same_access:
            self.empty_snapshot_streak += 1
            if self.empty_snapshot_streak < 3:
                self.sync_label.setText(
                    f"Server snapshot is empty ({self.empty_snapshot_streak}/3) - showing last update"
                )
                return True
        else:
            self.empty_snapshot_streak = 0
        return False

    def refresh(self):
        self.revision += 1
        try:
            if self.portal.preview:
                changed = self.portal.refresh()
            else:
                data = self.portal.request("snapshot")
                if self.should_hold_empty_snapshot(data):
                    return False
                changed = self.portal.apply_snapshot(data)
                self.empty_snapshot_streak = 0
        except PortalError as error:
            self.handle_error(error)
            return False
        return self.show_snapshot(changed)

    def selected(self, key):
        table = self.tables[key]
        items = table.selectedItems()
        if not items or table.isRowHidden(items[0].row()):
            raise PortalError("Select a visible row first.")
        id = table.item(items[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        return getattr(self.portal, key)[id]

    def perform(self, action):
        if action not in self.portal.actions:
            return
        try:
            fields = self.action_fields(action)
            if fields is None:
                return
            happened_at = datetime.now().astimezone()
            self.revision += 1
            result = self.portal.request(action, **fields)
        except PortalError as error:
            self.handle_error(error)
            return
        self.audit_events.insert(0, self.make_audit_entry(action, fields, result, happened_at))
        message = TITLES[action] + " · record " + str(result["id"])
        if action == "complete_lesson":
            message += f" · {result['lessons_completed']}/{result['total_lessons']} lessons"
        self.activities.insert(0, datetime.now().strftime("%H:%M") + "   " + message)
        self.render_recent_activity()
        self.refresh()
        self.load_recent_activity()

    def action_fields(self, action):
        title = TITLES[action]
        form = RecordForm(self, title)
        lookups = self.portal.lookups
        if action in (
            "delete_student",
            "delete_course",
            "deactivate_student",
            "withdraw_enrollment",
            "delete_enrollment",
        ):
            key = {"student": "students", "course": "courses", "enrollment": "enrollments"}[
                action.split("_")[1]
            ]
            record = self.selected(key)
            message = f"{title} · {' / '.join(record.cells()[:2])}?"
            if action == "delete_student":
                message += ("\nThis also removes the student's imported class-list entries. "
                            "Use Deactivate to keep the student on the roster.")
            reply = QMessageBox.question(
                self,
                title,
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            return {"id": record.id} if reply == QMessageBox.StandardButton.Yes else None
        if action == "complete_lesson":
            enrollment = self.selected("enrollments")
            return {"id": enrollment.id, "expected": enrollment.lessons_completed}
        if action == "reactivate_student":
            return {"id": self.selected("students").id}
        extra = {}
        if action in ("add_student", "edit_student"):
            student = self.selected("students") if action == "edit_student" else None

            if student is None:
                form.line("number", "Official student ID", limit=40)
                form.line("first_name", "Given name(s)", limit=80)
                form.line("last_name", "Surname", limit=80)
                if not self.portal.preview:
                    form.line("email", "Email address (required by current API)", limit=254)
                    form.line(
                        "phone_number", "Sierra Leone phone (required by current API)",
                        placeholder="+232 followed by 8 digits", limit=32
                    )
                    form.number("study_level", "Study level", 1, 32767)
                    form.line(
                        "admitted_on", "Admission date",
                        placeholder="YYYY-MM-DD", limit=10
                    )
            else:
                extra.update(id=student.id, version=student.version)
                name_parts = student.name.rsplit(" ", 1)
                form.line(
                    "first_name", "Given name(s)",
                    name_parts[0] if len(name_parts) == 2 else student.name,
                    placeholder="Enter both names when changing the name",
                    limit=80
                )
                form.line(
                    "last_name", "Surname",
                    name_parts[1] if len(name_parts) == 2 else "",
                    placeholder="Enter both names when changing the name",
                    limit=80
                )

            form.choose(
                "programme", "Programme", lookups.get("programmes", []),
                student.programme_id if student is not None else None
            )
        elif action in ("add_course", "edit_course"):
            c = self.selected("courses") if action == "edit_course" else None
            if c:
                extra.update(id=c.id, version=c.version)
            form.line("code", "Course code", c.code if c else "", limit=20)
            form.line("title", "Course title", c.title if c else "", limit=180)
            form.choose(
                "department", "Department", lookups.get("departments", []), c.department_id if c else None
            )
            form.number("credits", "Credits", c.credits if c else 1, 32767)
            form.number("lessons", "Total lessons", c.total_lessons if c else None, 10000, True)
        elif action == "add_enrollment":
            choices = [
                {"id": s.id, "name": s.number + " · " + s.name}
                for s in self.portal.students.values()
                if s.status == "active"
            ]
            form.choose("student", "Student", choices)
            form.choose(
                "offering", "Open course offering", [o for o in lookups.get("offerings", []) if o["open"]]
            )
        elif action == "add_department":
            form.line("code", "Department code", limit=20)
            form.line("name", "Department name", limit=150)
        elif action in ("add_year", "add_semester"):
            if action == "add_semester":
                form.choose("year", "Academic year", lookups.get("years", []))
            form.line("name", "Name", limit=60)
            form.line("start", "Start date", placeholder="YYYY-MM-DD", limit=10)
            form.line("end", "End date", placeholder="YYYY-MM-DD", limit=10)
        elif action == "offer_course":
            form.choose(
                "course",
                "Course",
                [{"id": c.id, "name": c.code + " · " + c.title} for c in self.portal.courses.values()],
            )
            form.choose("semester", "Semester", lookups.get("semesters", []))
        elif action == "assign_lecturer":
            form.choose("offering", "Course offering", lookups.get("offerings", []))
            form.choose("lecturer", "Lecturer", lookups.get("lecturers", []))
        values = form.values()
        if values is None:
            return None

        if action == "edit_student":
            if self.portal.preview:
                entered_name = " ".join(
                    part for part in (values.pop("first_name", "").strip(),
                                      values.pop("last_name", "").strip()) if part
                )
                values["name"] = entered_name or student.name
            elif not values["first_name"] and not values["last_name"]:
                values.pop("first_name")
                values.pop("last_name")
        if action == "add_student" and self.portal.preview:
            values["name"] = " ".join(
                part for part in (values.pop("first_name", "").strip(),
                                  values.pop("last_name", "").strip()) if part
            )
        if action in ("add_student", "edit_student"):
            email = values.get("email", "").strip()
            if action == "add_student" and not self.portal.preview and not email:
                QMessageBox.warning(self, "Student details", "The current portal API requires an email address.")
                return None
            if email and (email.count("@") != 1 or any(ch.isspace() for ch in email)
                          or email.startswith("@") or email.endswith("@")):
                QMessageBox.warning(self, "Student details", "Enter a valid email address or leave it blank.")
                return None
            phone = values.get("phone_number", "").strip()
            if action == "add_student" and not self.portal.preview and not phone:
                QMessageBox.warning(self, "Student details", "The current portal API requires a phone number.")
                return None
            if phone and (len([ch for ch in phone if ch.isdigit()]) < 7
                          or any(not (ch.isdigit() or ch in "+()- ") for ch in phone)):
                QMessageBox.warning(self, "Student details", "Enter a valid phone number or leave it blank.")
                return None
            if action == "add_student" and not self.portal.preview:
                try:
                    datetime.strptime(values.get("admitted_on", ""), "%Y-%m-%d")
                except ValueError:
                    QMessageBox.warning(self, "Student details", "Enter the admission date as YYYY-MM-DD.")
                    return None

        return dict(values, **extra)

class StudentPortalApp(QMainWindow):
    def __init__(self, portal):
        super().__init__()
        self.portal = portal
        self.setWindowTitle("University Student Learning Portal" + (" · Offline preview" if portal.preview else ""))
        self.setMinimumSize(960, 620)
        self.resize(1200, 750)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.login_page = LoginPage(portal)
        self.stack.addWidget(self.login_page)
        self.login_page.signed_in.connect(self.open_dashboard)
        self.dashboard_page = None
        self._transition_animation = None
        self._transition_labels = []
        self._transition_running = False
        if portal.preview:
            self.portal.login("", "")
            self.open_dashboard()

    def remove_dashboard(self):
        if self.dashboard_page is not None:
            self.dashboard_page.stop_sync()
            self.stack.removeWidget(self.dashboard_page)
            self.dashboard_page.deleteLater()
            self.dashboard_page = None

    def open_dashboard(self):
        if self._transition_running:
            return
        animate_transition = (
            self.stack.currentWidget() is self.login_page
            and self.isVisible()
            and not self.portal.preview
        )
        panel_images = self.login_page.transition_panels() if animate_transition else None
        self.remove_dashboard()
        self.dashboard_page = DashboardPage(self.portal)
        self.dashboard_page.logout_requested.connect(self.logout)
        self.dashboard_page.access_changed.connect(self.open_dashboard)
        if animate_transition:
            self.dashboard_page.setEnabled(False)
        self.stack.addWidget(self.dashboard_page)
        self.stack.setCurrentWidget(self.dashboard_page)
        if panel_images:
            self.start_login_transition(panel_images)

    def start_login_transition(self, panel_images):
        self._transition_running = True
        animation = QParallelAnimationGroup(self)
        for index, (pixmap, panel_geometry) in enumerate(panel_images):
            panel = QLabel(self.stack)
            panel.setPixmap(pixmap)
            panel.setGeometry(panel_geometry)
            panel.setMargin(0)
            panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            panel.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            panel.show()
            panel.raise_()
            self._transition_labels.append(panel)

            movement = QPropertyAnimation(panel, b"pos", animation)
            movement.setDuration(850)
            movement.setStartValue(panel_geometry.topLeft())
            end_x = -panel_geometry.width() if index == 0 else self.stack.width()
            movement.setEndValue(QPoint(end_x, panel_geometry.y()))
            movement.setEasingCurve(QEasingCurve.Type.InOutCubic)
            animation.addAnimation(movement)

        self._transition_animation = animation
        animation.finished.connect(self.finish_login_transition)
        animation.start()

    def finish_login_transition(self):
        for panel in self._transition_labels:
            panel.hide()
            panel.deleteLater()
        self._transition_labels.clear()
        self._transition_animation = None
        if self.dashboard_page is None or self.stack.currentWidget() is not self.dashboard_page:
            self._transition_running = False
            return
        self.dashboard_page.setEnabled(True)
        self._transition_running = False

    def cancel_transition(self):
        if self._transition_animation is not None:
            self._transition_animation.stop()
            self._transition_animation = None
        for panel in self._transition_labels:
            panel.hide()
            panel.deleteLater()
        self._transition_labels.clear()
        self._transition_running = False

    def logout(self):
        self.cancel_transition()
        if self.portal.preview:
            self.close()
            return
        if self.dashboard_page:
            self.dashboard_page.stop_sync()
        self.portal.logout()
        self.stack.setCurrentWidget(self.login_page)
        self.remove_dashboard()
        self.login_page.password_input.clear()
        self.login_page.username_input.clear()
        self.login_page.error_label.clear()
        self.login_page.show_password_checkbox.setChecked(False)
        self.login_page.username_input.setFocus()

    def closeEvent(self, event):
        self.cancel_transition()
        if self.dashboard_page:
            self.dashboard_page.stop_sync()
        self.portal.logout()
        super().closeEvent(event)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", action="store_true", help=argparse.SUPPRESS)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--profile", type=Path, help="team connection file supplied by the backend developer")
    mode.add_argument("--demo", action="store_true", help="open with disposable in-memory data")
    args = parser.parse_args()
    app = QApplication(sys.argv[:1])
    theme = str(QSettings("USLP", "StudentLearningPortal").value("appearance", "light"))
    if theme not in {"light", "dark"}:
        theme = "light"
    app.setProperty("uslpTheme", theme)
    app.setStyleSheet(application_stylesheet(theme))
    app.setFont(QFont("Segoe UI", 10))
    error = None
    if args.demo:
        from .preview import PreviewPortal
        portal = PreviewPortal()
    else:
        portal = Portal()
        path = args.profile or (SAVED_PROFILE if SAVED_PROFILE.is_file() else DEFAULT_PROFILE)
        if args.profile or path.is_file():
            try:
                portal.configure(path)
            except PortalError as exc:
                error = str(exc)
    window = StudentPortalApp(portal)
    if error:
        window.login_page.error_label.setText(error)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
