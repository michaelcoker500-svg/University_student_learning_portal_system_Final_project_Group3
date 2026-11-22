"""University Student Learning Portal desktop GUI. Connect to the team API or use an offline preview."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from .portal_client import DEFAULT_PROFILE, SAVED_PROFILE, Portal, PortalError
from PyQt6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont
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
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class LoginPage(QWidget):
    signed_in = pyqtSignal()

    def __init__(self, portal):
        super().__init__()
        self.portal = portal
        self.setup_ui()
        self.apply_styles()

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

        sign_in_button = QPushButton("Sign In")
        sign_in_button.setObjectName("signInButton")
        sign_in_button.clicked.connect(self.login)

        self.password_input.returnPressed.connect(self.login)

        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.connection_label = QLabel()
        self.connection_label.setWordWrap(True)
        self.show_connection()
        choose = QPushButton("Choose team connection file")
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

        logo = QLabel("🎓")
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

    def apply_styles(self):

        self.setStyleSheet("""

            #loginPanel {
                background-color: white;
            }

            #brandingPanel {
                background-color: #17365D;
            }

            #logo {
                font-size: 35px;
            }

            #loginHeading {
                color: #17365D;
                font-size: 31px;
                font-weight: bold;
            }

            #brandName {
                color: white;
                font-size: 24px;
                font-weight: bold;
            }

            #welcomeText {
                color: white;
                font-size: 25px;
                font-weight: bold;
            }

            #inputField {
                background-color: #F8FAFC;
                border: 1px solid #D9E0E8;
                border-radius: 6px;
                padding: 13px;
            }

            #inputField:focus {
                border: 1px solid #2874A6;
            }

            #signInButton {
                background-color: #17365D;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 14px;
                font-weight: bold;
            }

            #signInButton:hover {
                background-color: #2874A6;
            }

            #errorLabel {
                color: #A93232;
                font-size: 12px;
            }

        """)


class RecordForm(QDialog):
    """Build a labelled form. Each dropdown retains the database ID of its selection."""

    def __init__(self, parent, title):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self.layout = QFormLayout(self)
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
    "students": ["Student ID", "Full name", "Programme", "Status"],
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
        sidebar.setFixedWidth(205)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(18, 25, 18, 20)
        logo = QLabel("🎓 USLP")
        logo.setObjectName("sidebarLogo")
        nav.addWidget(logo)
        nav.addSpacing(20)
        for i, title in enumerate(self.names):
            button = QPushButton(title)
            button.setObjectName("menuButton")
            button.clicked.connect(lambda checked=False, idx=i: self.open_page(idx))
            nav.addWidget(button)
            self.menu_buttons.append(button)
        nav.addStretch()
        logout = QPushButton("Exit preview" if self.portal.preview else "Logout")
        logout.setObjectName("logoutButton")
        logout.clicked.connect(self.logout_requested.emit)
        nav.addWidget(logout)

        panel = QFrame()
        panel.setObjectName("contentArea")
        content = QVBoxLayout(panel)
        content.setContentsMargins(24, 22, 24, 20)
        bar = QHBoxLayout()
        self.heading = QLabel("Dashboard")
        self.heading.setObjectName("pageHeading")
        bar.addWidget(self.heading)
        bar.addStretch()
        self.sync_label = QLabel("Offline preview · changes stay in this window" if self.portal.preview else "")
        self.sync_label.setTextFormat(Qt.TextFormat.PlainText)
        bar.addWidget(self.sync_label)
        identity = QVBoxLayout()
        for value, style in [(self.user["name"], "userName"), (" · ".join(self.user["roles"]), "userRole")]:
            lab = QLabel(value)
            lab.setTextFormat(Qt.TextFormat.PlainText)
            lab.setObjectName(style)
            identity.addWidget(lab)
        bar.addLayout(identity)
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
        self.apply_styles()
        self.show_page(0)

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
            card = QFrame()
            card.setObjectName("statCard")
            box = QVBoxLayout(card)
            caption = QLabel(title)
            caption.setObjectName("cardTitle")
            value = QLabel()
            value.setObjectName("cardValue")
            box.addWidget(caption)
            box.addWidget(value)
            grid.addWidget(card, i // 2, i % 2)
            self.stats.append(value)
        lay.addLayout(grid)
        actions = QFrame()
        actions.setObjectName("panelCard")
        buttons = QHBoxLayout(actions)
        for action, page_index, text in [
            ("add_student", 1, "Add student"),
            ("add_course", 2, "Add course"),
            ("add_enrollment", 3, "Create enrolment"),
        ]:
            if action in self.portal.actions:
                btn = QPushButton(text)
                btn.setObjectName("quickButton")
                btn.clicked.connect(lambda checked=False, a=action, p=page_index: self.quick_action(p, a))
                buttons.addWidget(btn)
                self.quick_buttons[action] = btn
        if not self.user["staff"]:
            btn = QPushButton("View my enrolments")
            btn.setObjectName("quickButton")
            btn.clicked.connect(lambda: self.open_page(3))
            buttons.addWidget(btn)
        refresh = QPushButton("Refresh overview")
        refresh.setObjectName("quickButton")
        refresh.clicked.connect(self.refresh)
        buttons.addWidget(refresh)
        lay.addWidget(actions)
        activity = QFrame()
        activity.setObjectName("panelCard")
        activity_lay = QVBoxLayout(activity)
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
        search = QLineEdit()
        search.setPlaceholderText("Search " + title.lower() + "…")
        layout.addWidget(search)
        table = QTableWidget(0, len(HEADERS[key]))
        table.setHorizontalHeaderLabels(HEADERS[key])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().hide()
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        layout.addWidget(table)
        self.tables[key], self.searches[key] = table, search
        search.textChanged.connect(lambda value: self.filter_table(key, value))
        out = QHBoxLayout()
        for action, text in BUTTONS[key]:
            if action in self.portal.actions:
                btn = QPushButton(text)
                btn.clicked.connect(lambda checked=False, a=action: self.perform(a))
                out.addWidget(btn)
        if key == "courses":
            options = [(a, t) for a, t in ACADEMIC if a in self.portal.actions]
            if options:
                academic = QPushButton("Academic setup")
                menu = QMenu(academic)
                for action, text in options:
                    menu.addAction(text).triggered.connect(lambda checked=False, a=action: self.perform(a))
                academic.setMenu(menu)
                out.addWidget(academic)
        out.addStretch()
        refresh = QPushButton("Refresh")
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

    def apply_styles(self):

        self.setStyleSheet("""

            #sidebar {
                background-color: #17365D;
            }

            #sidebarLogo {
                color: white;
                font-size: 21px;
                font-weight: bold;
            }

            #menuButton {
                background-color: transparent;
                color: white;
                border: none;
                text-align: left;
                padding: 13px;
                border-radius: 5px;
            }

            #menuButton:hover {
                background-color: #2874A6;
            }

            QPushButton#menuButton[active="true"] {
                background-color: #2874A6;
                color: white;
                border-left: 4px solid #FFFFFF;
                font-weight: bold;
            }

            QPushButton#menuButton[active="false"] {
                background-color: transparent;
                color: white;
                border: none;
                text-align: left;
                padding: 13px;
                border-radius: 5px;
            }

            #logoutButton {
                background-color: #A93232;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 5px;
            }

            #contentArea {
                background-color: #F4F6F9;
            }

            #pageHeading {
                color: #17365D;
                font-size: 23px;
                font-weight: bold;
            }

            QLabel#userName {
                color: #17365D;
                font-size: 13px;
                font-weight: bold;
            }

            QLabel#userRole {
                color: #667085;
                font-size: 11px;
            }

            QFrame#headerSeparator {
                background-color: #D9E0E8;
                border: none;
            }

            #welcomeHeading {
                color: #17365D;
                font-size: 22px;
                font-weight: bold;
            }

            #sectionHeading {
                color: #17365D;
                font-size: 21px;
                font-weight: bold;
            }

            #statCard {
                background-color: white;
                border: 1px solid #E3E8EF;
                border-radius: 8px;
                padding: 10px;
            }

            #cardTitle {
                color: #667085;
                font-size: 12px;
            }

            #cardValue {
                color: #17365D;
                font-size: 27px;
                font-weight: bold;
            }

            QLineEdit {
                background-color: white;
                border: 1px solid #D9E0E8;
                border-radius: 5px;
                padding: 10px;
            }

            QPushButton {
                background-color: #17365D;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }

            QPushButton:hover {
                background-color: #2874A6;
            }

            QTableWidget {
                background-color: white;
                border: 1px solid #E3E8EF;
                gridline-color: #E8EDF2;
            }

            QHeaderView::section {
                background-color: #EAF0F6;
                color: #17365D;
                padding: 10px;
                border: none;
                font-weight: bold;
            }

            /* Dashboard page background inside the scroll area */

            #dashboardPage {
                background-color: #F4F6F9;
            }

            QScrollArea {
                background-color: #F4F6F9;
                border: none;
            }

            /* Quick Actions and Recent Activity panels */

            #panelCard {
                background-color: white;
                border: 1px solid #E3E8EF;
                border-radius: 8px;
                padding: 14px;
            }

            #panelCard:hover,
            #statCard:hover {
                border: 1px solid #B9C7D8;
            }

            #panelHeading {
                color: #17365D;
                font-size: 15px;
                font-weight: bold;
            }

            #panelDescription {
                color: #667085;
                font-size: 12px;
            }

            #quickButton {
                background-color: #F0F5FA;
                color: #17365D;
                border: 1px solid #D9E0E8;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }

            #quickButton:hover {
                background-color: #2874A6;
                color: white;
            }

            #activityList {
                background-color: #F8FAFC;
                border: 1px solid #E3E8EF;
                border-radius: 5px;
                padding: 6px;
            }

            #activityList::item {
                color: #344054;
                padding: 7px;
                border-bottom: 1px solid #E8EDF2;
            }

            #activityList::item:selected {
                background-color: #EAF0F6;
                color: #17365D;
            }

            /* Slim modern scroll bars */

            QScrollBar:vertical {
                background: #EDF1F6;
                width: 10px;
                margin: 0;
            }

            QScrollBar:horizontal {
                background: #EDF1F6;
                height: 10px;
                margin: 0;
            }

            QScrollBar::handle:vertical {
                background: #C3CFDD;
                border-radius: 5px;
                min-height: 30px;
            }

            QScrollBar::handle:horizontal {
                background: #C3CFDD;
                border-radius: 5px;
                min-width: 30px;
            }

            QScrollBar::handle:vertical:hover,
            QScrollBar::handle:horizontal:hover {
                background: #2874A6;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0;
                height: 0;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical,
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background: transparent;
            }

        """)


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
