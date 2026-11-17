import sys

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QSizePolicy
)

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


# =====================================================
# DEMO LOGIN ACCOUNTS
# =====================================================

DEMO_ACCOUNTS = {
    "admin": {
        "password": "Admin@123",
        "name": "System Administrator",
        "role": "Administrator"
    },

    "lecturer": {
        "password": "Lecturer@123",
        "name": "Demo Lecturer",
        "role": "Lecturer"
    },

    "student": {
        "password": "Student@123",
        "name": "Demo Student",
        "role": "Student"
    }
}


# =====================================================
# LOGIN PAGE
# =====================================================

class LoginPage(QWidget):

    login_success = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # LEFT PANEL: LOGIN FORM

        login_panel = QFrame()
        login_panel.setObjectName("loginPanel")

        login_layout = QVBoxLayout(login_panel)
        login_layout.setContentsMargins(65, 55, 65, 55)

        login_layout.addStretch()

        heading = QLabel("Welcome Back")
        heading.setObjectName("loginHeading")

        description = QLabel(
            "Sign in to access your learning portal."
        )

        username_label = QLabel("Username")
        username_label.setObjectName("fieldLabel")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(
            "Enter your username"
        )
        self.username_input.setObjectName("inputField")

        password_label = QLabel("Password")
        password_label.setObjectName("fieldLabel")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(
            "Enter your password"
        )
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.password_input.setObjectName("inputField")

        self.remember_checkbox = QCheckBox(
            "Remember me"
        )

        sign_in_button = QPushButton("Sign In")
        sign_in_button.setObjectName("signInButton")
        sign_in_button.clicked.connect(self.login)

        self.password_input.returnPressed.connect(
            self.login
        )

        login_layout.addWidget(heading)
        login_layout.addWidget(description)
        login_layout.addSpacing(25)

        login_layout.addWidget(username_label)
        login_layout.addWidget(self.username_input)

        login_layout.addSpacing(12)

        login_layout.addWidget(password_label)
        login_layout.addWidget(self.password_input)

        login_layout.addSpacing(12)

        login_layout.addWidget(self.remember_checkbox)
        login_layout.addSpacing(15)

        login_layout.addWidget(sign_in_button)

        login_layout.addSpacing(20)

        demo_text = QLabel(
            "Demo accounts are available for testing."
        )
        demo_text.setObjectName("demoNotice")
        demo_text.setWordWrap(True)

        login_layout.addWidget(demo_text)

        login_layout.addStretch()

        # RIGHT PANEL: UNIVERSITY BRANDING

        branding_panel = QFrame()
        branding_panel.setObjectName("brandingPanel")

        branding_layout = QVBoxLayout(branding_panel)
        branding_layout.setContentsMargins(45, 50, 45, 45)

        logo = QLabel("🎓")
        logo.setObjectName("logo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        university_name = QLabel(
            "UNIVERSITY\nSTUDENT\nLEARNING PORTAL"
        )
        university_name.setObjectName("brandName")

        welcome_text = QLabel(
            "Your Academic Journey\nStarts Here."
        )
        welcome_text.setObjectName("welcomeText")

        description = QLabel(
            "A central platform for managing academic "
            "activities, student information and learning progress."
        )
        description.setObjectName("brandDescription")
        description.setWordWrap(True)

        branding_layout.addWidget(logo)
        branding_layout.addSpacing(20)
        branding_layout.addWidget(university_name)
        branding_layout.addStretch()
        branding_layout.addWidget(welcome_text)
        branding_layout.addWidget(description)

        # Login is LEFT, branding is RIGHT

        main_layout.addWidget(login_panel, 58)
        main_layout.addWidget(branding_panel, 42)

    def login(self):

        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username:

            QMessageBox.warning(
                self,
                "Username Required",
                "Please enter your username."
            )

            self.username_input.setFocus()
            return

        if not password:

            QMessageBox.warning(
                self,
                "Password Required",
                "Please enter your password."
            )

            self.password_input.setFocus()
            return

        account = DEMO_ACCOUNTS.get(username.lower())

        if account and account["password"] == password:

            self.login_success.emit({
                "username": username,
                "name": account["name"],
                "role": account["role"]
            })

            self.password_input.clear()

        else:

            QMessageBox.critical(
                self,
                "Login Failed",
                "Incorrect username or password."
            )

    def apply_styles(self):

        self.setStyleSheet("""

            #loginPanel {
                background-color: #FFFFFF;
            }

            #brandingPanel {
                background-color: #17365D;
            }

            #logo {
                background-color: white;
                border-radius: 35px;
                min-width: 70px;
                max-width: 70px;
                min-height: 70px;
                max-height: 70px;
                font-size: 35px;
            }

            #loginHeading {
                color: #17365D;
                font-size: 31px;
                font-weight: bold;
            }

            #fieldLabel {
                color: #263747;
                font-size: 13px;
                font-weight: bold;
            }

            #inputField {
                background-color: #F8FAFC;
                border: 1px solid #D9E0E8;
                border-radius: 6px;
                padding: 13px;
                font-size: 13px;
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
                font-size: 14px;
                font-weight: bold;
            }

            #signInButton:hover {
                background-color: #2874A6;
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

            #brandDescription {
                color: #DCE6F1;
                font-size: 13px;
            }

            #demoNotice {
                color: #61758A;
                background-color: #F0F5FA;
                padding: 12px;
                border-radius: 5px;
                font-size: 11px;
            }

        """)


# =====================================================
# DASHBOARD PAGE
# =====================================================

class DashboardPage(QWidget):

    logout_requested = pyqtSignal()

    def __init__(self, user):

        super().__init__()

        self.user = user

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # =============================================
        # SIDEBAR
        # =============================================

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(225)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 25, 18, 20)
        sidebar_layout.setSpacing(12)

        logo = QLabel("🎓 USLP")
        logo.setObjectName("sidebarLogo")

        sidebar_layout.addWidget(logo)
        sidebar_layout.addSpacing(25)

        menu_items = [
            "Dashboard",
            "Students",
            "Courses",
            "Enrolments",
            "Learning Materials",
            "Reports"
        ]

        for item in menu_items:

            button = QPushButton(item)
            button.setObjectName("menuButton")
            button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            button.clicked.connect(
                lambda checked=False, name=item:
                self.change_page(name)
            )

            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch()

        logout_button = QPushButton("Logout")
        logout_button.setObjectName("logoutButton")
        logout_button.clicked.connect(
            self.logout_requested.emit
        )

        sidebar_layout.addWidget(logout_button)

        # =============================================
        # MAIN CONTENT AREA
        # =============================================

        content_area = QFrame()
        content_area.setObjectName("contentArea")

        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(30, 25, 30, 25)

        # TOP BAR

        top_bar = QHBoxLayout()

        self.page_heading = QLabel("Dashboard")
        self.page_heading.setObjectName("pageHeading")

        user_info = QLabel(
            f"{self.user['name']}  |  {self.user['role']}"
        )
        user_info.setObjectName("userInfo")

        top_bar.addWidget(self.page_heading)
        top_bar.addStretch()
        top_bar.addWidget(user_info)

        content_layout.addLayout(top_bar)
        content_layout.addSpacing(25)

        # STACKED PAGE AREA

        self.pages = QStackedWidget()

        self.pages.addWidget(self.create_dashboard())
        self.pages.addWidget(
            self.create_simple_page(
                "Student Management",
                "View and manage student information."
            )
        )
        self.pages.addWidget(
            self.create_simple_page(
                "Course Management",
                "View available university courses."
            )
        )
        self.pages.addWidget(
            self.create_simple_page(
                "Enrolment Management",
                "Review student course enrolments."
            )
        )
        self.pages.addWidget(
            self.create_simple_page(
                "Learning Materials",
                "Access learning resources and materials."
            )
        )
        self.pages.addWidget(
            self.create_simple_page(
                "Reports",
                "Academic reports and system summaries."
            )
        )

        content_layout.addWidget(self.pages)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_area)

    # =============================================
    # DASHBOARD OVERVIEW
    # =============================================

    def create_dashboard(self):

        page = QWidget()

        layout = QVBoxLayout(page)
        layout.setSpacing(20)

        welcome = QLabel(
            f"Welcome, {self.user['name']}"
        )
        welcome.setObjectName("welcomeHeading")

        subtitle = QLabel(
            "Here is an overview of the learning portal."
        )

        layout.addWidget(welcome)
        layout.addWidget(subtitle)

        # STATISTICS CARDS

        cards_layout = QGridLayout()
        cards_layout.setSpacing(15)

        card_data = [
            ("Total Students", "1,250", "Registered students"),
            ("Total Courses", "48", "Available courses"),
            ("Enrolments", "3,420", "Course registrations"),
            ("Lecturers", "65", "Academic staff")
        ]

        for index, data in enumerate(card_data):

            card = QFrame()
            card.setObjectName("statCard")

            card_layout = QVBoxLayout(card)

            title = QLabel(data[0])
            title.setObjectName("cardTitle")

            value = QLabel(data[1])
            value.setObjectName("cardValue")

            description = QLabel(data[2])
            description.setObjectName("cardDescription")

            card_layout.addWidget(title)
            card_layout.addWidget(value)
            card_layout.addWidget(description)

            cards_layout.addWidget(
                card,
                index // 2,
                index % 2
            )

        layout.addLayout(cards_layout)

        # RECENT ACTIVITY

        activity_heading = QLabel("Recent Activity")
        activity_heading.setObjectName("sectionHeading")

        layout.addWidget(activity_heading)

        activity_table = QTableWidget()

        activity_table.setColumnCount(3)
        activity_table.setHorizontalHeaderLabels([
            "Activity",
            "Date",
            "Status"
        ])

        activities = [
            ("New student registered", "16 Nov 2026", "Completed"),
            ("Course added", "15 Nov 2026", "Completed"),
            ("Student enrolled", "14 Nov 2026", "Completed"),
            ("Learning material uploaded", "13 Nov 2026", "Completed")
        ]

        activity_table.setRowCount(len(activities))

        for row, activity in enumerate(activities):

            for column, value in enumerate(activity):

                activity_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(value)
                )

        activity_table.horizontalHeader().setStretchLastSection(
            True
        )

        activity_table.horizontalHeader().setSectionResizeMode(
            0,
            activity_table.horizontalHeader().ResizeMode.Stretch
        )

        activity_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        activity_table.setMinimumHeight(200)

        layout.addWidget(activity_table)

        layout.addStretch()

        return page

    # =============================================
    # OTHER BASIC FRONTEND PAGES
    # =============================================

    def create_simple_page(self, heading, description):

        page = QWidget()

        layout = QVBoxLayout(page)
        layout.setSpacing(15)

        title = QLabel(heading)
        title.setObjectName("welcomeHeading")

        details = QLabel(description)
        details.setObjectName("pageDescription")

        information = QLabel(
            "This section is part of the frontend preview. "
            "Full management functions will be developed "
            "in later stages."
        )
        information.setObjectName("demoNotice")
        information.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(details)
        layout.addWidget(information)
        layout.addStretch()

        return page

    # =============================================
    # NAVIGATION
    # =============================================

    def change_page(self, page_name):

        pages = {
            "Dashboard": 0,
            "Students": 1,
            "Courses": 2,
            "Enrolments": 3,
            "Learning Materials": 4,
            "Reports": 5
        }

        self.pages.setCurrentIndex(pages[page_name])

        self.page_heading.setText(page_name)

    # =============================================
    # DASHBOARD STYLING
    # =============================================

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
                color: #E5EDF5;
                border: none;
                text-align: left;
                padding: 13px;
                border-radius: 5px;
                font-size: 13px;
            }

            #menuButton:hover {
                background-color: #2874A6;
                color: white;
            }

            #logoutButton {
                background-color: #A93232;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
            }

            #logoutButton:hover {
                background-color: #C0392B;
            }

            #contentArea {
                background-color: #F4F6F9;
            }

            #pageHeading {
                color: #17365D;
                font-size: 23px;
                font-weight: bold;
            }

            #userInfo {
                color: #526579;
                font-size: 12px;
            }

            #welcomeHeading {
                color: #17365D;
                font-size: 22px;
                font-weight: bold;
            }

            #pageDescription {
                color: #667085;
                font-size: 14px;
            }

            #statCard {
                background-color: white;
                border: 1px solid #E3E8EF;
                border-radius: 8px;
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

            #cardDescription {
                color: #8995A3;
                font-size: 11px;
            }

            #sectionHeading {
                color: #17365D;
                font-size: 17px;
                font-weight: bold;
            }

            #demoNotice {
                color: #61758A;
                background-color: #E8EFF6;
                border-radius: 6px;
                padding: 15px;
            }

            QTableWidget {
                background-color: white;
                border: 1px solid #E3E8EF;
                gridline-color: #E8EDF2;
                border-radius: 5px;
            }

            QHeaderView::section {
                background-color: #EAF0F6;
                color: #17365D;
                padding: 10px;
                border: none;
                font-weight: bold;
            }

        """)


# =====================================================
# MAIN APPLICATION WINDOW
# =====================================================

class StudentPortal(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "University Student Learning Portal"
        )

        self.setMinimumSize(1000, 650)
        self.resize(1200, 750)

        self.stack = QStackedWidget()

        self.setCentralWidget(self.stack)

        # Create login page

        self.login_page = LoginPage()

        self.stack.addWidget(self.login_page)

        self.login_page.login_success.connect(
            self.open_dashboard
        )

    # =============================================
    # OPEN DASHBOARD AFTER LOGIN
    # =============================================

    def open_dashboard(self, user):

        self.dashboard_page = DashboardPage(user)

        self.dashboard_page.logout_requested.connect(
            self.logout
        )

        self.stack.addWidget(self.dashboard_page)

        self.stack.setCurrentWidget(
            self.dashboard_page
        )

    # =============================================
    # LOGOUT
    # =============================================

    def logout(self):

        self.stack.setCurrentWidget(
            self.login_page
        )

        self.stack.removeWidget(
            self.dashboard_page
        )

        self.dashboard_page.deleteLater()

        self.login_page.username_input.clear()
        self.login_page.password_input.clear()


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    app.setFont(QFont("Segoe UI", 10))

    window = StudentPortal()

    window.show()

    sys.exit(app.exec())
