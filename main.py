import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel,
    QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout,
    QGridLayout, QStackedWidget, QTableWidget,
    QTableWidgetItem, QMessageBox, QInputDialog,
    QHeaderView, QAbstractItemView, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


# =========================================================
# 1. ASSIGNMENT 1 OOP CLASSES
# =========================================================

class Course:

    total_courses = 0

    def __init__(self, course_code, title, total_lessons):
        self.course_code = course_code
        self.title = title
        self.total_lessons = total_lessons
        Course.total_courses += 1

    def describe(self):
        return f"{self.course_code} - {self.title}"

    def detail_lines(self):
        return [
            f"Course Code: {self.course_code}",
            f"Title: {self.title}",
            f"Total Lessons: {self.total_lessons}"
        ]

    @classmethod
    def from_string(cls, text):
        code, title, lessons = text.split(",")
        return cls(
            code.strip().upper(),
            title.strip(),
            int(lessons)
        )

    @classmethod
    def count_courses(cls):
        return cls.total_courses


class Student:

    total_students = 0

    def __init__(self, student_id, Fullname):
        self.student_id = student_id
        self.Fullname = Fullname
        Student.total_students += 1

    def describe(self):
        return f"{self.student_id} - {self.Fullname}"

    def detail_lines(self):
        return [
            f"Student ID: {self.student_id}",
            f"Full Name: {self.Fullname}"
        ]

    @classmethod
    def from_string(cls, text):
        student_id, fullname = text.split(",")
        return cls(
            student_id.strip().upper(),
            fullname.strip()
        )

    @classmethod
    def count_students(cls):
        return cls.total_students


class Enrollment:

    def __init__(self, enrollment_id, student, course):
        self.enrollment_id = enrollment_id
        self.student = student
        self.course = course
        self.lessons_completed = 0

    def complete_lesson(self):

        if self.lessons_completed < self.course.total_lessons:
            self.lessons_completed += 1
            return True

        return False

    def is_finished(self):
        return self.lessons_completed >= self.course.total_lessons

    def progress_percent(self):

        if self.course.total_lessons <= 0:
            return 0

        return (
            self.lessons_completed /
            self.course.total_lessons
        ) * 100

    def status_text(self):
        return "Finished" if self.is_finished() else "In Progress"

    def detail_lines(self):
        return [
            f"Enrollment ID: {self.enrollment_id}",
            f"Student: {self.student.Fullname}",
            f"Course: {self.course.title}",
            f"Lessons: {self.lessons_completed}/"
            f"{self.course.total_lessons}",
            f"Progress: {self.progress_percent():.0f}%",
            f"Status: {self.status_text()}"
        ]


class Portal:

    def __init__(self):
        self.students = {}
        self.courses = {}
        self.enrollments = {}

    # -----------------------------
    # STUDENT MANAGEMENT
    # -----------------------------

    def add_student(self, student):

        if student.student_id in self.students:
            return False

        self.students[student.student_id] = student
        return True

    def delete_student(self, student_id):

        if student_id not in self.students:
            return False

        # Do not delete a student who has enrolments.
        for enrollment in self.enrollments.values():

            if enrollment.student.student_id == student_id:
                return False

        del self.students[student_id]
        return True

    # -----------------------------
    # COURSE MANAGEMENT
    # -----------------------------

    def add_course(self, course):

        if course.course_code in self.courses:
            return False

        self.courses[course.course_code] = course
        return True

    def delete_course(self, course_code):

        if course_code not in self.courses:
            return False

        # Do not delete a course with existing enrolments.
        for enrollment in self.enrollments.values():

            if enrollment.course.course_code == course_code:
                return False

        del self.courses[course_code]
        return True

    # -----------------------------
    # ENROLMENT MANAGEMENT
    # -----------------------------

    def next_enrollment_id(self):

        number = 1

        while f"E{number:03d}" in self.enrollments:
            number += 1

        return f"E{number:03d}"

    def find_enrollment_for(self, student, course):

        for enrollment in self.enrollments.values():

            if (
                enrollment.student.student_id == student.student_id
                and enrollment.course.course_code == course.course_code
            ):
                return enrollment

        return None

    def add_enrollment(self, student, course):

        if self.find_enrollment_for(student, course):
            return None

        enrollment_id = self.next_enrollment_id()

        enrollment = Enrollment(
            enrollment_id,
            student,
            course
        )

        self.enrollments[enrollment_id] = enrollment

        return enrollment

    def delete_enrollment(self, enrollment_id):

        if enrollment_id not in self.enrollments:
            return False

        del self.enrollments[enrollment_id]
        return True


# =========================================================
# 2. DEMO LOGIN ACCOUNTS
# =========================================================

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


# =========================================================
# 3. LOGIN PAGE
# =========================================================

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

        # LOGIN PANEL

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

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(
            "Enter your username"
        )
        self.username_input.setObjectName("inputField")

        password_label = QLabel("Password")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(
            "Enter your password"
        )
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.password_input.setObjectName("inputField")

        self.show_password_checkbox = QCheckBox("Show password")
        self.show_password_checkbox.toggled.connect(self.toggle_password)

        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)

        self.username_input.textChanged.connect(
            lambda: self.error_label.clear()
        )
        self.password_input.textChanged.connect(
            lambda: self.error_label.clear()
        )

        sign_in_button = QPushButton("Sign In")
        sign_in_button.setObjectName("signInButton")
        sign_in_button.clicked.connect(self.login)

        self.password_input.returnPressed.connect(self.login)

        self.username_input.returnPressed.connect(
        self.password_input.setFocus
)

        demo_notice = QLabel(
            "Demo accounts: admin, lecturer or student."
        )
        demo_notice.setObjectName("demoNotice")

        login_layout.addWidget(heading)
        login_layout.addWidget(description)
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
        login_layout.addWidget(demo_notice)

        login_layout.addStretch()

        # BRANDING PANEL

        branding_panel = QFrame()
        branding_panel.setObjectName("brandingPanel")

        branding_layout = QVBoxLayout(branding_panel)
        branding_layout.setContentsMargins(45, 50, 45, 45)

        logo = QLabel("🎓")
        logo.setObjectName("logo")
        logo.setFixedSize(60, 60)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        university_name = QLabel(
            "UNIVERSITY\nSTUDENT\nLEARNING PORTAL"
        )
        university_name.setObjectName("brandName")

        welcome = QLabel(
            "Your Academic Journey\nStarts Here."
        )
        welcome.setObjectName("welcomeText")

        branding_layout.addWidget(logo)
        branding_layout.addSpacing(20)
        branding_layout.addWidget(university_name)
        branding_layout.addStretch()
        branding_layout.addWidget(welcome)

        # Login is LEFT, branding is RIGHT
        
        main_layout.addWidget(branding_panel, 42)
        main_layout.addWidget(login_panel, 42)
       

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
                background-color: white;
            }

            #brandingPanel {
                background-color: #17365D;
            }

            #logo {
                font-size: 35px;
                background-color: white;
                border-radius: 30px;
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

            #demoNotice {
                color: #61758A;
                background-color: #F0F5FA;
                padding: 12px;
                border-radius: 5px;
            }

            #errorLabel {
                color: #A93232;
                font-size: 12px;
            }

        """)

    def toggle_password(self, checked):
        
        if checked:
           self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
           self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

# =========================================================
# 4. DASHBOARD AND MANAGEMENT PAGES
# =========================================================

class DashboardPage(QWidget):

    logout_requested = pyqtSignal()

    def __init__(self, portal, user):

        super().__init__()

        self.portal = portal
        self.user = user

        self.setup_ui()

    def setup_ui(self):

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # SIDEBAR

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 25, 18, 20)

        logo = QLabel("🎓 USLP")
        logo.setObjectName("sidebarLogo")

        sidebar_layout.addWidget(logo)
        sidebar_layout.addSpacing(25)

        self.pages = QStackedWidget()

        menu_items = [
            "Dashboard",
            "Students",
            "Courses",
            "Enrolments"
        ]

        for index, item in enumerate(menu_items):

            button = QPushButton(item)
            button.setObjectName("menuButton")

            button.clicked.connect(
                lambda checked=False, page=index:
                self.open_page(page)
            )

            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch()

        logout_button = QPushButton("Logout")
        logout_button.setObjectName("logoutButton")
        logout_button.setCursor(Qt.CursorShape.PointingHandCursor)

        logout_button.clicked.connect(
            self.logout_requested.emit
        )

        sidebar_layout.addWidget(logout_button)

        # MAIN CONTENT

        content = QFrame()
        content.setObjectName("contentArea")

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 25, 30, 25)

        top_bar = QHBoxLayout()

        self.page_heading = QLabel("Dashboard")
        self.page_heading.setObjectName("pageHeading")

        user_label = QLabel(
            f"{self.user['name']} | {self.user['role']}"
        )

        top_bar.addWidget(self.page_heading)
        top_bar.addStretch()
        top_bar.addWidget(user_label)

        content_layout.addLayout(top_bar)
        content_layout.addSpacing(20)

        # ADD THE FOUR PAGES

        self.pages.addWidget(self.create_dashboard())
        self.pages.addWidget(self.create_students_page())
        self.pages.addWidget(self.create_courses_page())
        self.pages.addWidget(self.create_enrollments_page())

        content_layout.addWidget(self.pages)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)

        self.apply_styles()

    # -----------------------------------------------------
    # DASHBOARD
    # -----------------------------------------------------

    def create_dashboard(self):

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(18)

        welcome = QLabel(
            f"Welcome, {self.user['name']}"
        )
        welcome.setObjectName("welcomeHeading")

        subtitle = QLabel(
            "Here is an overview of your learning portal."
        )

        layout.addWidget(welcome)
        layout.addWidget(subtitle)

        self.student_count = QLabel()
        self.course_count = QLabel()
        self.enrollment_count = QLabel()
        self.progress_count = QLabel()

        cards = [
            ("Total Students", self.student_count),
            ("Total Courses", self.course_count),
            ("Total Enrolments", self.enrollment_count),
            ("Finished Courses", self.progress_count)
        ]

        card_layout = QGridLayout()
        card_layout.setSpacing(15)

        for index, (title, value_label) in enumerate(cards):

            card = QFrame()
            card.setObjectName("statCard")

            card_box = QVBoxLayout(card)

            title_label = QLabel(title)
            title_label.setObjectName("cardTitle")

            value_label.setObjectName("cardValue")

            card_box.addWidget(title_label)
            card_box.addWidget(value_label)

            card_layout.addWidget(
                card,
                index // 2,
                index % 2
            )

        layout.addLayout(card_layout)

        refresh_button = QPushButton("Refresh Dashboard")
        refresh_button.clicked.connect(self.refresh_dashboard)

        layout.addWidget(refresh_button)
        layout.addStretch()

        self.refresh_dashboard()

        return page

    def refresh_dashboard(self):

        if hasattr(self, "student_count"):

            self.student_count.setText(
                str(len(self.portal.students))
            )

            self.course_count.setText(
                str(len(self.portal.courses))
            )

            self.enrollment_count.setText(
                str(len(self.portal.enrollments))
            )

            finished = sum(
                1 for enrollment in self.portal.enrollments.values()
                if enrollment.is_finished()
            )

            self.progress_count.setText(str(finished))

    # -----------------------------------------------------
    # STUDENT MANAGEMENT
    # -----------------------------------------------------

    def create_students_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("Student Management")
        title.setObjectName("sectionHeading")

        description = QLabel(
            "Add, search, view and remove student records."
        )

        self.student_search = QLineEdit()
        self.student_search.setPlaceholderText(
            "Search by student ID or full name..."
        )
        self.student_search.textChanged.connect(
            self.filter_students
        )

        self.student_table = QTableWidget()
        self.student_table.setColumnCount(2)
        self.student_table.setHorizontalHeaderLabels([
            "Student ID",
            "Full Name"
        ])

        self.student_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.student_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.student_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        add_button = QPushButton("Add Student")
        add_button.clicked.connect(self.add_student)

        delete_button = QPushButton("Delete Selected Student")
        delete_button.clicked.connect(self.delete_student)

        buttons = QHBoxLayout()
        buttons.addWidget(add_button)
        buttons.addWidget(delete_button)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(self.student_search)
        layout.addWidget(self.student_table)
        layout.addLayout(buttons)

        self.refresh_students()

        return page

    def refresh_students(self):

        self.student_table.setRowCount(
            len(self.portal.students)
        )

        for row, student in enumerate(
            self.portal.students.values()
        ):

            self.student_table.setItem(
                row, 0, QTableWidgetItem(student.student_id)
            )

            self.student_table.setItem(
                row, 1, QTableWidgetItem(student.Fullname)
            )

    def filter_students(self, search_text):

        search_text = search_text.lower()

        for row in range(self.student_table.rowCount()):

            student_id = self.student_table.item(row, 0).text().lower()
            fullname = self.student_table.item(row, 1).text().lower()

            self.student_table.setRowHidden(
                row,
                search_text not in student_id
                and search_text not in fullname
            )

    def add_student(self):

        student_id, ok = QInputDialog.getText(
            self,
            "Add Student",
            "Enter Student ID:"
        )

        if not ok:
            return

        student_id = student_id.strip().upper()

        if not student_id:
            QMessageBox.warning(self, "Invalid ID", "Student ID is required.")
            return

        fullname, ok = QInputDialog.getText(
            self,
            "Add Student",
            "Enter Full Name:"
        )

        if not ok:
            return

        fullname = fullname.strip()

        if not fullname:
            QMessageBox.warning(self, "Invalid Name", "Full name is required.")
            return

        student = Student(student_id, fullname)

        if self.portal.add_student(student):

            QMessageBox.information(
                self, "Success", "Student added successfully."
            )

            self.refresh_students()
            self.refresh_dashboard()

        else:

            QMessageBox.warning(
                self, "Duplicate Student",
                "That student ID already exists."
            )

    def delete_student(self):

        row = self.student_table.currentRow()

        if row < 0:
            QMessageBox.warning(
                self, "Select Student",
                "Please select a student first."
            )
            return

        student_id = self.student_table.item(row, 0).text()

        answer = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete student {student_id}?"
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        if self.portal.delete_student(student_id):

            QMessageBox.information(
                self, "Deleted", "Student deleted successfully."
            )

        else:

            QMessageBox.warning(
                self,
                "Cannot Delete",
                "This student has enrolments. Remove those enrolments first."
            )

        self.refresh_students()
        self.refresh_dashboard()

    # -----------------------------------------------------
    # COURSE MANAGEMENT
    # -----------------------------------------------------

    def create_courses_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("Course Management")
        title.setObjectName("sectionHeading")

        description = QLabel(
            "View and manage available courses."
        )

        self.course_search = QLineEdit()
        self.course_search.setPlaceholderText(
            "Search by course code or title..."
        )
        self.course_search.textChanged.connect(
            self.filter_courses
        )

        self.course_table = QTableWidget()
        self.course_table.setColumnCount(3)
        self.course_table.setHorizontalHeaderLabels([
            "Course Code",
            "Course Title",
            "Total Lessons"
        ])

        self.course_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.course_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.course_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        add_button = QPushButton("Add Course")
        add_button.clicked.connect(self.add_course)

        delete_button = QPushButton("Delete Selected Course")
        delete_button.clicked.connect(self.delete_course)

        buttons = QHBoxLayout()
        buttons.addWidget(add_button)
        buttons.addWidget(delete_button)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(self.course_search)
        layout.addWidget(self.course_table)
        layout.addLayout(buttons)

        self.refresh_courses()

        return page

    def refresh_courses(self):

        self.course_table.setRowCount(
            len(self.portal.courses)
        )

        for row, course in enumerate(
            self.portal.courses.values()
        ):

            self.course_table.setItem(
                row, 0, QTableWidgetItem(course.course_code)
            )

            self.course_table.setItem(
                row, 1, QTableWidgetItem(course.title)
            )

            self.course_table.setItem(
                row, 2, QTableWidgetItem(str(course.total_lessons))
            )

    def filter_courses(self, search_text):

        search_text = search_text.lower()

        for row in range(self.course_table.rowCount()):

            code = self.course_table.item(row, 0).text().lower()
            title = self.course_table.item(row, 1).text().lower()

            self.course_table.setRowHidden(
                row,
                search_text not in code
                and search_text not in title
            )

    def add_course(self):

        code, ok = QInputDialog.getText(
            self,
            "Add Course",
            "Enter Course Code:"
        )

        if not ok:
            return

        code = code.strip().upper()

        if not code:
            QMessageBox.warning(self, "Invalid Code", "Course code is required.")
            return

        title, ok = QInputDialog.getText(
            self,
            "Add Course",
            "Enter Course Title:"
        )

        if not ok:
            return

        title = title.strip()

        if not title:
            QMessageBox.warning(self, "Invalid Title", "Course title is required.")
            return

        lessons, ok = QInputDialog.getInt(
            self,
            "Add Course",
            "Enter Total Lessons:",
            5,
            1,
            1000
        )

        if not ok:
            return

        course = Course(code, title, lessons)

        if self.portal.add_course(course):

            QMessageBox.information(
                self, "Success", "Course added successfully."
            )

            self.refresh_courses()
            self.refresh_dashboard()

        else:

            QMessageBox.warning(
                self, "Duplicate Course",
                "That course code already exists."
            )

    def delete_course(self):

        row = self.course_table.currentRow()

        if row < 0:
            QMessageBox.warning(
                self, "Select Course",
                "Please select a course first."
            )
            return

        code = self.course_table.item(row, 0).text()

        answer = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete course {code}?"
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        if self.portal.delete_course(code):

            QMessageBox.information(
                self, "Deleted", "Course deleted successfully."
            )

        else:

            QMessageBox.warning(
                self,
                "Cannot Delete",
                "This course has enrolments. Remove those enrolments first."
            )

        self.refresh_courses()
        self.refresh_dashboard()

    # -----------------------------------------------------
    # ENROLMENT MANAGEMENT
    # -----------------------------------------------------

    def create_enrollments_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("Enrolment Management")
        title.setObjectName("sectionHeading")

        description = QLabel(
            "Connect students to courses and monitor lesson progress."
        )

        self.enrollment_search = QLineEdit()
        self.enrollment_search.setPlaceholderText(
            "Search by enrolment ID, student or course..."
        )
        self.enrollment_search.textChanged.connect(
            self.filter_enrollments
        )

        self.enrollment_table = QTableWidget()
        self.enrollment_table.setColumnCount(6)

        self.enrollment_table.setHorizontalHeaderLabels([
            "Enrolment ID",
            "Student",
            "Course",
            "Lessons",
            "Progress",
            "Status"
        ])

        self.enrollment_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.enrollment_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.enrollment_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        add_button = QPushButton("Create Enrolment")
        add_button.clicked.connect(self.add_enrollment)

        progress_button = QPushButton("Complete Lesson")
        progress_button.clicked.connect(self.complete_lesson)

        delete_button = QPushButton("Remove Enrolment")
        delete_button.clicked.connect(self.delete_enrollment)

        buttons = QHBoxLayout()
        buttons.addWidget(add_button)
        buttons.addWidget(progress_button)
        buttons.addWidget(delete_button)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(self.enrollment_search)
        layout.addWidget(self.enrollment_table)
        layout.addLayout(buttons)

        self.refresh_enrollments()

        return page

    def refresh_enrollments(self):

        self.enrollment_table.setRowCount(
            len(self.portal.enrollments)
        )

        for row, enrollment in enumerate(
            self.portal.enrollments.values()
        ):

            values = [
                enrollment.enrollment_id,
                enrollment.student.Fullname,
                enrollment.course.title,
                f"{enrollment.lessons_completed}/"
                f"{enrollment.course.total_lessons}",
                f"{enrollment.progress_percent():.0f}%",
                enrollment.status_text()
            ]

            for column, value in enumerate(values):

                self.enrollment_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(str(value))
                )

    def filter_enrollments(self, search_text):

        search_text = search_text.lower()

        for row in range(self.enrollment_table.rowCount()):

            row_text = " ".join(
                self.enrollment_table.item(row, column).text().lower()
                for column in range(self.enrollment_table.columnCount())
            )

            self.enrollment_table.setRowHidden(
                row,
                search_text not in row_text
            )

    def add_enrollment(self):

        if not self.portal.students or not self.portal.courses:

            QMessageBox.warning(
                self,
                "Missing Records",
                "Add at least one student and one course first."
            )
            return

        student_options = [
            f"{student.student_id} - {student.Fullname}"
            for student in self.portal.students.values()
        ]

        selected_student, ok = QInputDialog.getItem(
            self,
            "Create Enrolment",
            "Select Student:",
            student_options,
            0,
            False
        )

        if not ok:
            return

        student_id = selected_student.split(" - ")[0]
        student = self.portal.students[student_id]

        course_options = [
            f"{course.course_code} - {course.title}"
            for course in self.portal.courses.values()
        ]

        selected_course, ok = QInputDialog.getItem(
            self,
            "Create Enrolment",
            "Select Course:",
            course_options,
            0,
            False
        )

        if not ok:
            return

        course_code = selected_course.split(" - ")[0]
        course = self.portal.courses[course_code]

        enrollment = self.portal.add_enrollment(
            student,
            course
        )

        if enrollment is None:

            QMessageBox.warning(
                self,
                "Duplicate Enrolment",
                "This student is already enrolled in this course."
            )
            return

        QMessageBox.information(
            self,
            "Success",
            f"Enrolment {enrollment.enrollment_id} created."
        )

        self.refresh_enrollments()
        self.refresh_dashboard()

    def complete_lesson(self):

        row = self.enrollment_table.currentRow()

        if row < 0:
            QMessageBox.warning(
                self,
                "Select Enrolment",
                "Select an enrolment first."
            )
            return

        enrollment_id = self.enrollment_table.item(row, 0).text()

        enrollment = self.portal.enrollments[enrollment_id]

        if enrollment.complete_lesson():

            QMessageBox.information(
                self,
                "Lesson Completed",
                f"Progress is now {enrollment.progress_percent():.0f}%."
            )

        else:

            QMessageBox.information(
                self,
                "Course Finished",
                "All lessons in this course are already completed."
            )

        self.refresh_enrollments()
        self.refresh_dashboard()

    def delete_enrollment(self):

        row = self.enrollment_table.currentRow()

        if row < 0:
            QMessageBox.warning(
                self,
                "Select Enrolment",
                "Select an enrolment first."
            )
            return

        enrollment_id = self.enrollment_table.item(row, 0).text()

        answer = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Remove enrolment {enrollment_id}?"
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.portal.delete_enrollment(enrollment_id)

        QMessageBox.information(
            self,
            "Removed",
            "Enrolment removed successfully."
        )

        self.refresh_enrollments()
        self.refresh_dashboard()

    # -----------------------------------------------------
    # PAGE NAVIGATION
    # -----------------------------------------------------

    def open_page(self, page_number):

        self.pages.setCurrentIndex(page_number)

        headings = [
            "Dashboard",
            "Students",
            "Courses",
            "Enrolments"
        ]

        self.page_heading.setText(headings[page_number])

        if page_number == 0:
            self.refresh_dashboard()

        elif page_number == 1:
            self.refresh_students()

        elif page_number == 2:
            self.refresh_courses()

        elif page_number == 3:
            self.refresh_enrollments()

    # -----------------------------------------------------
    # STYLING
    # -----------------------------------------------------

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

            #logoutButton {
                background-color: #A93232;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 5px;
            }
            #logoutButton:hover {
            background-color: #C0392B;
            border: 1px solid #E74C3C;
            }
            #logoutButton:pressed {
            background-color: #7B241C;
            border: 1px solid #641E16;
            }
            

            #contentArea {
                background-color: #F4F6F9;
            }

            #pageHeading {
                color: #17365D;
                font-size: 23px;
                font-weight: bold;
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

        """)


# =========================================================
# 5. MAIN APPLICATION
# =========================================================

class StudentPortalApp(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "University Student Learning Portal"
        )

        self.setMinimumSize(1000, 650)
        self.resize(1200, 750)

        # One Portal object manages the application records.

        self.portal = Portal()

        self.load_sample_data()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_page = LoginPage()

        self.stack.addWidget(self.login_page)

        self.login_page.login_success.connect(
            self.open_dashboard
        )

        self.dashboard_page = None

    # -----------------------------------------------------
    # SAMPLE DATA FROM ASSIGNMENT 1
    # -----------------------------------------------------

    def load_sample_data(self):

        students = [
            ("S001", "Ama"),
            ("S002", "Kofi"),
            ("S003", "Musa"),
            ("S004", "Fatmata")
        ]

        courses = [
            ("PY101", "Intro to Python", 5),
            ("MTH102", "Basic Algebra", 4),
            ("ENG103", "Study Skills", 3)
        ]

        for student_id, fullname in students:

            self.portal.add_student(
                Student(student_id, fullname)
            )

        for code, title, lessons in courses:

            self.portal.add_course(
                Course(code, title, lessons)
            )

        first = self.portal.add_enrollment(
            self.portal.students["S001"],
            self.portal.courses["PY101"]
        )

        second = self.portal.add_enrollment(
            self.portal.students["S002"],
            self.portal.courses["PY101"]
        )

        third = self.portal.add_enrollment(
            self.portal.students["S002"],
            self.portal.courses["MTH102"]
        )

        fourth = self.portal.add_enrollment(
            self.portal.students["S003"],
            self.portal.courses["ENG103"]
        )

        # Demonstration progress

        for _ in range(2):
            first.complete_lesson()

        for _ in range(1):
            second.complete_lesson()

        for _ in range(4):
            third.complete_lesson()

        for _ in range(3):
            fourth.complete_lesson()

    # -----------------------------------------------------
    # OPEN DASHBOARD
    # -----------------------------------------------------

    def open_dashboard(self, user):

        self.dashboard_page = DashboardPage(
            self.portal,
            user
        )

        self.stack.addWidget(self.dashboard_page)

        self.dashboard_page.logout_requested.connect(
            self.logout
        )

        self.stack.setCurrentWidget(
            self.dashboard_page
        )

    # -----------------------------------------------------
    # LOGOUT
    # -----------------------------------------------------

    def logout(self):

        self.stack.setCurrentWidget(self.login_page)

        self.stack.removeWidget(self.dashboard_page)

        self.dashboard_page.deleteLater()

        self.dashboard_page = None

        self.login_page.username_input.clear()
        self.login_page.password_input.clear()

        self.login_page.error_label.clear()
        self.login_page.username_input.setFocus()


# =========================================================
# 6. START APPLICATION
# =========================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    app.setFont(QFont("Segoe UI", 10))

    window = StudentPortalApp()

    window.show()

    sys.exit(app.exec())