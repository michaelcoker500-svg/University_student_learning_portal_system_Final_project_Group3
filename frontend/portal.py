"""University Student Learning Portal desktop GUI. Connect to the team API or use an offline preview."""

import argparse
import sys
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
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStyle,
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
    #quickButton { background: #F0F5FA; color: #17365D; border-color: #D9E0E8; }
    #quickButton:hover { background: #2874A6; color: #FFFFFF; }
    #activityList { background: #F8FAFC; border: 1px solid #E3E8EF; border-radius: 7px; padding: 6px; }
    #activityList::item { color: #344054; padding: 7px; border-bottom: 1px solid #E8EDF2; }
    #activityList::item:selected { background: #EAF0F6; color: #17365D; }
"""


class PortalButton(QPushButton):
    """Shared button with an optional platform icon and visual variant."""

    def __init__(self, text, variant="primary", icon=None, parent=None):
        super().__init__(text, parent)
        self.setProperty("variant", variant)
        if icon is not None:
            self.setIcon(self.style().standardIcon(icon))


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

        sign_in_button = PortalButton("Sign In", icon=QStyle.StandardPixmap.SP_DialogApplyButton)
        sign_in_button.setObjectName("signInButton")
        sign_in_button.clicked.connect(self.login)

        self.password_input.returnPressed.connect(self.login)

        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.connection_label = QLabel()
        self.connection_label.setWordWrap(True)
        self.show_connection()
        choose = PortalButton("Choose team connection file", "secondary",
                              QStyle.StandardPixmap.SP_DialogOpenButton)
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


class DashboardPage(QWidget):
    logout_requested = pyqtSignal()
    access_changed = pyqtSignal()

    def __init__(self, portal):
        super().__init__()
        self.portal = portal
        self.user = portal.user.copy()
        self.initial_actions = portal.actions.copy()
        self.activities = []
        self.tables, self.searches, self.quick_buttons = {}, {}, {}
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
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(4000)
        self.poll_timer.timeout.connect(self.poll)
        self.setup_ui()
        self.display()
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
            button = PortalButton(title, "quiet", self._nav_icon(i))
            button.setObjectName("menuButton")
            button.clicked.connect(lambda checked=False, idx=i: self.open_page(idx))
            nav.addWidget(button)
            self.menu_buttons.append(button)
        nav.addStretch()
        logout = PortalButton("Exit preview" if self.portal.preview else "Logout", "danger",
                              QStyle.StandardPixmap.SP_DialogCloseButton)
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

    @staticmethod
    def _nav_icon(index):
        icons = (
            QStyle.StandardPixmap.SP_ComputerIcon,
            QStyle.StandardPixmap.SP_FileDialogInfoView,
            QStyle.StandardPixmap.SP_DirIcon,
            QStyle.StandardPixmap.SP_FileDialogDetailedView,
        )
        return icons[index] if index < len(icons) else QStyle.StandardPixmap.SP_FileIcon

    def dashboard(self):
        page = QFrame()
        page.setObjectName("dashboardPage")
        lay = QVBoxLayout(page)
        lay.setSpacing(15)
        welcome = QLabel("Welcome, " + self.user["name"])
        welcome.setTextFormat(Qt.TextFormat.PlainText)
        welcome.setObjectName("welcomeHeading")
        lay.addWidget(welcome)
        staff = self.user["staff"]
        lay.addWidget(
            QLabel(
                "University academic records"
                if staff
                else "Your assigned teaching and class records"
                if self.lecturer
                else "Your student record, courses and learning progress"
            )
        )
        grid = QGridLayout()
        self.stats = []
        labels = [
            "Students" if staff else "My students" if self.lecturer else "Student ID",
            "Courses" if staff else "My courses",
            "Enrolments" if staff else "My enrolments",
            "Completed enrolments",
        ]
        for i, title in enumerate(labels):
            card = PortalCard("statCard")
            box = card.content_layout
            caption = QLabel(title)
            caption.setObjectName("cardTitle")
            value = QLabel()
            value.setObjectName("cardValue")
            box.addWidget(caption)
            box.addWidget(value)
            grid.addWidget(card, i // 2, i % 2)
            self.stats.append(value)
        lay.addLayout(grid)
        actions = PortalCard("panelCard")
        buttons = QHBoxLayout()
        actions.content_layout.addLayout(buttons)
        for action, page_index, text in [
            ("add_student", 1, "Add student"),
            ("add_course", 2, "Add course"),
            ("add_enrollment", 3, "Create enrolment"),
        ]:
            if action in self.portal.actions:
                btn = PortalButton(text, "secondary")
                btn.setObjectName("quickButton")
                btn.clicked.connect(lambda checked=False, a=action, p=page_index: self.quick_action(p, a))
                buttons.addWidget(btn)
                self.quick_buttons[action] = btn
        if not self.user["staff"]:
            btn = PortalButton("View my enrolments", "secondary")
            btn.setObjectName("quickButton")
            btn.clicked.connect(lambda: self.open_page(3))
            buttons.addWidget(btn)
        refresh = PortalButton("Refresh overview", "secondary", QStyle.StandardPixmap.SP_BrowserReload)
        refresh.setObjectName("quickButton")
        refresh.clicked.connect(self.refresh)
        buttons.addWidget(refresh)
        lay.addWidget(actions)
        activity = PortalCard("panelCard")
        activity_lay = activity.content_layout
        label = QLabel("Recent activity this session")
        label.setObjectName("panelHeading")
        activity_lay.addWidget(label)
        self.activity_list = QListWidget()
        self.activity_list.setObjectName("activityList")
        self.activity_list.addItem("No activity yet.")
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
        search = QLineEdit()
        search.setPlaceholderText("Search " + title.lower() + "…")
        search.setClearButtonEnabled(True)
        search.setAccessibleName("Search " + title.lower())
        layout.addWidget(search)
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
        search.textChanged.connect(lambda value: self.filter_table(key, value))
        out = QHBoxLayout()
        for action, text in BUTTONS[key]:
            if action in self.portal.actions:
                destructive = action in {"delete_student", "delete_course", "delete_enrollment"}
                btn = PortalButton(text, "danger" if destructive else "secondary")
                btn.clicked.connect(lambda checked=False, a=action: self.perform(a))
                out.addWidget(btn)
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
        refresh = PortalButton("Refresh", "secondary", QStyle.StandardPixmap.SP_BrowserReload)
        refresh.clicked.connect(self.refresh)
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
        student_value = str(len(self.portal.students))
        if not self.user["staff"] and not self.lecturer:
            record = next(iter(self.portal.students.values()), None)
            student_value = record.number if record else "—"
        totals = [
            student_value,
            len(self.portal.courses),
            len(self.portal.enrollments),
            sum(e.status == "completed" for e in self.portal.enrollments.values()),
        ]
        for widget, value in zip(self.stats, totals):
            widget.setText(str(value))

    def filter_table(self, key, value):
        table = self.tables[key]
        query = value.casefold().strip()
        for i in range(table.rowCount()):
            cells = [table.item(i, j).text() for j in range(table.columnCount()) if table.item(i, j)]
            table.setRowHidden(i, query not in " ".join(cells).casefold())

    def show_page(self, index):
        self.pages.setCurrentIndex(index)
        self.heading.setText(self.names[index])
        for i, button in enumerate(self.menu_buttons):
            button.setProperty("active", i == index)
            button.style().unpolish(button)
            button.style().polish(button)

    def open_page(self, index):
        if self.refresh():
            self.show_page(index)

    def quick_action(self, page, action):
        if self.refresh():
            self.show_page(page)
            self.perform(action)

    def stop_sync(self):
        self.poll_timer.stop()
        self.revision += 1

    def mark_updated(self):
        if not self.portal.preview:
            self.sync_label.setText("Updated " + datetime.now().strftime("%H:%M:%S"))

    def poll(self):
        if self.pending is not None or not self.isVisible() or QApplication.activeModalWidget() is not None:
            return
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
            if outcome.status in (401, 403):
                self.handle_error(outcome)
            else:
                self.sync_label.setText("Reconnecting · showing last update")
            return
        try:
            changed = self.portal.apply_snapshot(outcome)
        except PortalError as error:
            self.sync_label.setText(str(error))
            return
        self.show_snapshot(changed)

    def show_snapshot(self, changed):
        if self.user != self.portal.user or self.initial_actions != self.portal.actions:
            self.stop_sync()
            self.access_changed.emit()
            return False
        if changed:
            self.display()
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
            self.revision += 1
            result = self.portal.request(action, **fields)
        except PortalError as error:
            self.handle_error(error)
            return
        message = TITLES[action] + " · record " + str(result["id"])
        if action == "complete_lesson":
            message += f" · {result['lessons_completed']}/{result['total_lessons']} lessons"
        self.activities.insert(0, datetime.now().strftime("%H:%M") + "   " + message)
        self.activity_list.clear()
        self.activity_list.addItems(self.activities[:8])
        self.refresh()

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
