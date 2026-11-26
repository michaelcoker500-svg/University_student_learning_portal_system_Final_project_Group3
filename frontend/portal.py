"""University Student Learning Portal desktop GUI. Connect to the team API or use an offline preview."""

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from .portal_client import DEFAULT_PROFILE, SAVED_PROFILE, Portal, PortalError
from PyQt6.QtCore import QPointF, QObject, QRunnable, Qt, QThreadPool, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QFont, QPainter, QPixmap, QPolygonF
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
    QMainWindow, QDialog { background: #F4F6F9; }
    QLineEdit, QComboBox, QSpinBox {
        background: #FFFFFF; border: 1px solid #D9E0E8; border-radius: 6px;
        padding: 8px 10px; min-height: 20px; selection-background-color: #2874A6;
    }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 1px solid #2874A6; }
    QComboBox::drop-down { border: 0; width: 26px; }
    QPushButton {
        background: #17365D; color: #FFFFFF; border: 1px solid #17365D;
        border-radius: 6px; padding: 8px 13px; min-height: 20px; font-weight: 600;
    }
    QPushButton:hover { background: #2874A6; border-color: #2874A6; }
    QPushButton:pressed { background: #102845; }
    QPushButton:disabled { background: #E5EAF0; color: #98A2B3; border-color: #E5EAF0; }
    QPushButton[variant="secondary"] { background: #FFFFFF; color: #17365D; border-color: #D9E0E8; }
    QPushButton[variant="secondary"]:hover { background: #EAF0F6; }
    QPushButton[variant="quiet"] { background: transparent; color: #FFFFFF; border-color: transparent; }
    QPushButton[variant="danger"] { background: #A93232; border-color: #A93232; }
    QPushButton[variant="danger"]:hover { background: #862626; border-color: #862626; }
    QTableWidget {
        background: #FFFFFF; alternate-background-color: #F8FAFC; color: #243247;
        border: 1px solid #D9E0E8; border-radius: 8px; gridline-color: #EDF1F5;
        selection-background-color: #E1ECF5; selection-color: #17365D;
    }
    QTableWidget::item { padding: 8px; border-bottom: 1px solid #EDF1F5; }
    QHeaderView::section {
        background: #EAF0F6; color: #17365D; padding: 10px; border: 0;
        border-bottom: 1px solid #D9E0E8; font-weight: 700;
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
    #brandingPanel, #sidebar { background: #17365D; }
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
    #contentArea, #dashboardPage, QScrollArea { background: #F4F6F9; border: 0; }
    #pageHeading { color: #17365D; font-size: 19pt; font-weight: 700; }
    QLabel#userName { color: #17365D; font-size: 10pt; font-weight: 700; }
    QLabel#userRole { color: #667085; font-size: 9pt; }
    #headerSeparator { background: #D9E0E8; border: 0; }
    #welcomeHeading { color: #17365D; font-size: 18pt; font-weight: 700; }
    #sectionHeading { color: #17365D; font-size: 16pt; font-weight: 700; }
    #statCard, #panelCard {
        background: #FFFFFF; border: 1px solid #E3E8EF; border-radius: 10px; padding: 12px;
    }
    #cardTitle { color: #667085; font-size: 9pt; }
    #cardValue { color: #17365D; font-size: 24pt; font-weight: 700; }
    #panelHeading { color: #17365D; font-size: 12pt; font-weight: 700; }
    #panelDescription { color: #667085; font-size: 9pt; }
    #noticeSummary { color: #17365D; font-size: 13pt; font-weight: 700; }
    #quickButton { background: #F0F5FA; color: #17365D; border-color: #D9E0E8; }
    #quickButton:hover { background: #2874A6; color: #FFFFFF; }
    #activityList { background: #F8FAFC; border: 1px solid #E3E8EF; border-radius: 7px; padding: 6px; }
    #activityList::item { color: #344054; padding: 7px; border-bottom: 1px solid #E8EDF2; }
    #activityList::item:selected { background: #EAF0F6; color: #17365D; }
"""


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

class RecordForm(QDialog):
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


class StudentProfileDialog(QDialog):
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


class AuditLogDialog(QDialog):
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
        self.setMinimumHeight(155)
        self.setAccessibleName("Enrolment status chart")

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
            painter.setPen(QColor("#52677F"))
            painter.drawText(0, y + 19, label)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#EDF1F6"))
            painter.drawRoundedRect(bar_x, y + 4, bar_width, 14, 7, 7)
            amount = self.counts[index]
            if amount and maximum:
                painter.setBrush(self.COLORS[index])
                painter.drawRoundedRect(bar_x, y + 4, max(7, int(bar_width * amount / maximum)), 14, 7, 7)
            painter.setPen(QColor("#243247"))
            painter.drawText(bar_x + bar_width + 8, y + 17, str(amount))
        if maximum == 0:
            painter.setPen(QColor("#667085"))
            painter.drawText(bar_x, 8 + len(self.LABELS) * row_height + 2, "No enrolment data yet")
        painter.end()


class BreakdownChart(QWidget):
    """Reusable horizontal breakdown chart for values in the loaded snapshot."""

    COLORS = (QColor("#2874A6"), QColor("#34866A"), QColor("#D28A36"),
              QColor("#8050A8"), QColor("#C85A4A"), QColor("#5D7895"))

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.setMinimumHeight(120)

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
            painter.setPen(QColor("#667085"))
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
            painter.setPen(QColor("#52677F"))
            painter.drawText(0, y, label_width - 8, 22, Qt.AlignmentFlag.AlignVCenter,
                             self.fontMetrics().elidedText(label, Qt.TextElideMode.ElideRight, label_width - 8))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#EDF1F6"))
            painter.drawRoundedRect(bar_x, y + 4, bar_width, 14, 7, 7)
            painter.setBrush(self.COLORS[index % len(self.COLORS)])
            painter.drawRoundedRect(bar_x, y + 4, max(7, int(bar_width * value / maximum)), 14, 7, 7)
            painter.setPen(QColor("#243247"))
            painter.drawText(bar_x + bar_width + 6, y, value_width - 6, 22,
                             Qt.AlignmentFlag.AlignVCenter, str(value))
        painter.end()


class DashboardReportDialog(QDialog):
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
        self.activities = []
        self.tables, self.searches, self.status_filters, self.quick_buttons = {}, {}, {}, {}
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
        ]
        self.revision = 0
        self.pending = None
        self.pending_action = None
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(4000)
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
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(232)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(18, 25, 18, 20)
        brand = QHBoxLayout()
        brand.addWidget(cap_badge(36))
        logo = QLabel("USLP")
        logo.setObjectName("sidebarLogo")
        brand.addWidget(logo)
        brand.addStretch()
        nav.addLayout(brand)
        nav.addSpacing(20)
        for i, title in enumerate(self.names):
            button = PortalButton(title, "quiet")
            button.setObjectName("menuButton")
            button.clicked.connect(lambda checked=False, idx=i: self.open_page(idx))
            nav.addWidget(button)
            self.menu_buttons.append(button)
        nav.addStretch()
        logout = PortalButton("Exit preview" if self.portal.preview else "Logout", "danger")
        logout.setObjectName("logoutButton")
        logout.clicked.connect(self.logout_requested.emit)
        nav.addWidget(logout)

        panel = QFrame()
        panel.setObjectName("contentArea")
        content = QVBoxLayout(panel)
        content.setContentsMargins(30, 22, 30, 24)
        content.setSpacing(16)
        bar = QHBoxLayout()
        self.heading = QLabel("Dashboard")
        self.heading.setObjectName("pageHeading")
        bar.addWidget(self.heading)
        bar.addStretch()
        self.global_search = QLineEdit()
        self.global_search.setMaximumWidth(300)
        self.global_search.setPlaceholderText("Search loaded records…")
        self.global_search.setAccessibleName("Search loaded student, course and enrolment records")
        self.global_search.returnPressed.connect(self.search_records)
        bar.addWidget(self.global_search)
        self.sync_label = QLabel("Offline preview · changes stay in this window" if self.portal.preview else "")
        self.sync_label.setObjectName("syncStatus")
        self.sync_label.setTextFormat(Qt.TextFormat.PlainText)
        bar.addWidget(self.sync_label)
        identity = QVBoxLayout()
        for value, style in [(self.user["name"], "userName"), (" · ".join(self.user["roles"]), "userRole")]:
            lab = QLabel(value)
            lab.setTextFormat(Qt.TextFormat.PlainText)
            lab.setObjectName(style)
            identity.addWidget(lab)
        identity_widget = QWidget()
        identity_widget.setObjectName("identityCard")
        identity_widget.setLayout(identity)
        bar.addWidget(identity_widget)
        content.addLayout(bar)
        divider = QFrame()
        divider.setObjectName("headerSeparator")
        divider.setFixedHeight(1)
        content.addWidget(divider)
        self.pages = QStackedWidget()
        self.pages.addWidget(self.dashboard())
        for idx, key in enumerate(HEADERS, 1):
            self.pages.addWidget(self.record_page(key, self.names[idx]))
        content.addWidget(self.pages)
        main.addWidget(sidebar)
        main.addWidget(panel)
        self.show_page(0)

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
            card = PortalCard("statCard")
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
        self.student_status_chart = BreakdownChart()
        self.semester_chart = BreakdownChart()
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
            "Enrolment status", "In progress, completed and withdrawn records", self.enrollment_chart
        ), 1, 1)

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
        analytics.addWidget(performance, 2, 0)

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
        analytics.addWidget(notices, 2, 1)
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
        return scroll

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
        table = QTableWidget(0, len(HEADERS[key]))
        table.setMouseTracking(True)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setHorizontalHeaderLabels(HEADERS[key])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.horizontalHeader().setStretchLastSection(True)
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
        self.enrollment_chart.set_records(enrollments)
        measurable = [e.progress for e in enrollments if e.progress is not None]
        average_progress = round(sum(measurable) / len(measurable)) if measurable else None
        self.academic_summary.setText(
            f"Completed enrolments: {completed} of {len(enrollments)}. "
            + (f"Average lesson completion: {average_progress}% across {len(measurable)} records."
               if measurable else "Lesson completion totals are unavailable for these enrolments.")
        )

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
        self.render_recent_activity()

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
        for i in range(table.rowCount()):
            cells = [table.item(i, j).text() for j in range(table.columnCount()) if table.item(i, j)]
            matches_query = query in " ".join(cells).casefold()
            status_filter = self.status_filters.get(key)
            matches_status = (
                status_filter is None
                or status_filter.currentData() == "all"
                or (table.item(i, 4) and table.item(i, 4).text().casefold() == status_filter.currentData())
            )
            table.setRowHidden(i, not (matches_query and matches_status))

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
        self.pages.setCurrentIndex(index)
        self.heading.setText(self.names[index])
        for i, button in enumerate(self.menu_buttons):
            button.setProperty("active", i == index)
            button.style().unpolish(button)
            button.style().polish(button)

    def open_page(self, index):
        self.show_page(index)
        if index == 0:
            self.load_recent_activity()
        if not self.portal.preview:
            self.refresh_async()

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
        if self.pending is None:
            self.sync_label.setText("Refreshing · showing last update")
            self.start_snapshot_task()

    def start_snapshot_task(self):
        self.revision += 1
        self.pending = SnapshotTask(self.portal, self.revision)
        self.pending.signals.finished.connect(self.poll_finished)
        QThreadPool.globalInstance().start(self.pending)

    @pyqtSlot(int, object)
    def poll_finished(self, revision, outcome):
        self.pending = None
        # A newer foreground read/write, a sign-out or an open form takes precedence.
        if revision != self.revision or not self.poll_timer.isActive() or QApplication.activeModalWidget() is not None:
            return
        if isinstance(outcome, PortalError):
            action_requested = self.pending_action is not None
            self.pending_action = None
            if outcome.status in (401, 403) or action_requested:
                self.handle_error(outcome)
            else:
                self.sync_label.setText("Reconnecting · showing last update")
            return
        try:
            changed = self.portal.apply_snapshot(outcome)
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

    def refresh(self):
        self.revision += 1
        try:
            changed = self.portal.refresh()
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
            s = self.selected("students") if action == "edit_student" else None
            if s:
                extra.update(id=s.id, version=s.version)
            else:
                form.line("number", "Official student ID", limit=40)
            form.line("name", "Full name", s.name if s else "", limit=240)
            form.choose(
                "programme", "Programme", lookups.get("programmes", []), s.programme_id if s else None
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
        return None if values is None else dict(values, **extra)

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
        self.remove_dashboard()
        self.dashboard_page = DashboardPage(self.portal)
        self.dashboard_page.logout_requested.connect(self.logout)
        self.dashboard_page.access_changed.connect(self.open_dashboard)
        self.stack.addWidget(self.dashboard_page)
        self.stack.setCurrentWidget(self.dashboard_page)

    def logout(self):
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
    app.setStyleSheet(DESIGN_STYLES + """
        QCheckBox:enabled:hover, QComboBox:enabled:hover, QSpinBox:enabled:hover,
        QLineEdit:enabled:hover { border-color: #A9B9CC; }
        QTableWidget::item:hover:!selected, QListWidget::item:hover:!selected,
        QHeaderView::section:hover, QMenu::item:selected { background: #EAF0F6; color: #17365D; }
        #identityCard { background: #FFFFFF; border: 1px solid #E3E8EF; border-radius: 8px; padding: 5px 10px; }
        #syncStatus { color: #52677F; background: #EAF0F6; border: 1px solid #D9E0E8;
                      border-radius: 10px; padding: 5px 9px; font-size: 9pt; }
    """)
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
