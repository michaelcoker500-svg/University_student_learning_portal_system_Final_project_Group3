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
    QMessageBox
)

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class LoginWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # Window settings
        self.setWindowTitle("University Student Learning Portal")
        self.setMinimumSize(900, 600)
        self.resize(1100, 680)

        # Create the main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Main horizontal layout
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create both sides of the login screen
        self.create_branding_panel(main_layout)
        self.create_login_panel(main_layout)

        # Apply the application stylesheet
        self.apply_styles()

    # --------------------------------------------------
    # LEFT SIDE: BRANDING PANEL
    # --------------------------------------------------

    def create_branding_panel(self, main_layout):

        branding_panel = QFrame()
        branding_panel.setObjectName("brandingPanel")

        branding_layout = QVBoxLayout(branding_panel)
        branding_layout.setContentsMargins(55, 50, 55, 40)
        branding_layout.setSpacing(20)

        # Placeholder logo
        logo = QLabel("🎓")
        logo.setObjectName("logo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # University portal name
        brand_name = QLabel("UNIVERSITY\nSTUDENT\nLEARNING PORTAL")
        brand_name.setObjectName("brandName")

        # Short description
        brand_description = QLabel(
            "A central platform for managing academic "
            "activities, student information and learning progress."
        )
        brand_description.setObjectName("brandDescription")
        brand_description.setWordWrap(True)

        # Welcome message
        welcome_message = QLabel(
            "Your Academic Journey\nStarts Here."
        )
        welcome_message.setObjectName("welcomeMessage")

        # Footer
        footer = QLabel(
            "EDUCATION • TECHNOLOGY • EXCELLENCE"
        )
        footer.setObjectName("brandingFooter")

        # Add widgets to the layout
        branding_layout.addWidget(logo)
        branding_layout.addSpacing(15)
        branding_layout.addWidget(brand_name)
        branding_layout.addWidget(brand_description)
        branding_layout.addStretch()
        branding_layout.addWidget(welcome_message)
        branding_layout.addSpacing(35)
        branding_layout.addWidget(footer)

        main_layout.addWidget(branding_panel, 42)

    # --------------------------------------------------
    # RIGHT SIDE: LOGIN PANEL
    # --------------------------------------------------

    def create_login_panel(self, main_layout):

        login_panel = QFrame()
        login_panel.setObjectName("loginPanel")

        login_layout = QVBoxLayout(login_panel)
        login_layout.setContentsMargins(75, 55, 75, 55)
        login_layout.setSpacing(15)

        # Heading
        heading = QLabel("Welcome Back")
        heading.setObjectName("loginHeading")

        # Description
        description = QLabel(
            "Sign in to access your student learning portal."
        )
        description.setObjectName("loginDescription")
        description.setWordWrap(True)

        # Username label
        username_label = QLabel("Username / Staff ID")
        username_label.setObjectName("fieldLabel")

        # Username input
        self.username_input = QLineEdit()
        self.username_input.setObjectName("inputField")
        self.username_input.setPlaceholderText(
            "Enter your username or Staff ID"
        )

        # Password label
        password_label = QLabel("Password")
        password_label.setObjectName("fieldLabel")

        # Password input
        self.password_input = QLineEdit()
        self.password_input.setObjectName("inputField")
        self.password_input.setPlaceholderText(
            "Enter your password"
        )
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        # Show / Hide password button
        self.show_password_button = QPushButton("Show")
        self.show_password_button.setObjectName(
            "showPasswordButton"
        )
        self.show_password_button.setCheckable(True)
        self.show_password_button.clicked.connect(
            self.toggle_password
        )

        # Password row
        password_layout = QHBoxLayout()
        password_layout.setSpacing(8)
        password_layout.addWidget(self.password_input)
        password_layout.addWidget(self.show_password_button)

        # Remember me checkbox
        self.remember_checkbox = QCheckBox("Remember me")
        self.remember_checkbox.setObjectName(
            "rememberCheckbox"
        )

        # Forgot password button
        forgot_button = QPushButton("Forgot password?")
        forgot_button.setObjectName("forgotPasswordButton")
        forgot_button.clicked.connect(
            self.forgot_password
        )

        # Remember and forgot password row
        options_layout = QHBoxLayout()
        options_layout.addWidget(self.remember_checkbox)
        options_layout.addStretch()
        options_layout.addWidget(forgot_button)

        # Sign in button
        sign_in_button = QPushButton("Sign In")
        sign_in_button.setObjectName("signInButton")
        sign_in_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        sign_in_button.clicked.connect(
            self.handle_sign_in
        )

        # Press Enter in password field to submit
        self.password_input.returnPressed.connect(
            self.handle_sign_in
        )

        # Information notice
        notice = QLabel(
            "Frontend demonstration only. "
            "Authentication and database connection "
            "will be added in later stages."
        )
        notice.setObjectName("demoNotice")
        notice.setWordWrap(True)

        # Add everything to the login layout
        login_layout.addStretch()
        login_layout.addWidget(heading)
        login_layout.addWidget(description)
        login_layout.addSpacing(25)

        login_layout.addWidget(username_label)
        login_layout.addWidget(self.username_input)

        login_layout.addSpacing(10)

        login_layout.addWidget(password_label)
        login_layout.addLayout(password_layout)

        login_layout.addSpacing(10)

        login_layout.addLayout(options_layout)
        login_layout.addSpacing(20)

        login_layout.addWidget(sign_in_button)
        login_layout.addSpacing(20)
        login_layout.addWidget(notice)

        login_layout.addStretch()

        main_layout.addWidget(login_panel, 58)

    # --------------------------------------------------
    # SHOW / HIDE PASSWORD
    # --------------------------------------------------

    def toggle_password(self):

        if self.show_password_button.isChecked():

            self.password_input.setEchoMode(
                QLineEdit.EchoMode.Normal
            )

            self.show_password_button.setText("Hide")

        else:

            self.password_input.setEchoMode(
                QLineEdit.EchoMode.Password
            )

            self.show_password_button.setText("Show")

    # --------------------------------------------------
    # FORGOT PASSWORD
    # --------------------------------------------------

    def forgot_password(self):

        QMessageBox.information(
            self,
            "Forgot Password",
            "Please contact the university system "
            "administrator for password assistance."
        )

    # --------------------------------------------------
    # SIGN IN VALIDATION
    # --------------------------------------------------

    def handle_sign_in(self):

        username = self.username_input.text().strip()
        password = self.password_input.text()

        # Check whether the username is empty
        if not username:

            QMessageBox.warning(
                self,
                "Missing Username",
                "Please enter your username or Staff ID."
            )

            self.username_input.setFocus()
            return

        # Check whether the password is empty
        if not password:

            QMessageBox.warning(
                self,
                "Missing Password",
                "Please enter your password."
            )

            self.password_input.setFocus()
            return

        # Frontend demonstration message
        QMessageBox.information(
            self,
            "Login Demonstration",
            "Your information has been entered successfully.\n\n"
            "Real account verification will be implemented "
            "when we connect the application to the database."
        )

    # --------------------------------------------------
    # APPLICATION STYLING
    # --------------------------------------------------

    def apply_styles(self):

        self.setStyleSheet("""

            QMainWindow {
                background-color: #F4F6F9;
            }

            #brandingPanel {
                background-color: #17365D;
            }

            #loginPanel {
                background-color: #FFFFFF;
            }

            #logo {
                background-color: #FFFFFF;
                color: #17365D;
                border-radius: 35px;
                min-width: 70px;
                max-width: 70px;
                min-height: 70px;
                max-height: 70px;
                font-size: 35px;
            }

            #brandName {
                color: #FFFFFF;
                font-size: 25px;
                font-weight: bold;
            }

            #brandDescription {
                color: #DCE6F1;
                font-size: 13px;
                line-height: 1.5;
            }

            #welcomeMessage {
                color: #FFFFFF;
                font-size: 27px;
                font-weight: bold;
            }

            #brandingFooter {
                color: #B8C7D9;
                font-size: 10px;
                letter-spacing: 2px;
            }

            #loginHeading {
                color: #17365D;
                font-size: 32px;
                font-weight: bold;
            }

            #loginDescription {
                color: #777777;
                font-size: 13px;
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
                color: #263747;
                font-size: 13px;
                min-height: 22px;
            }

            #inputField:focus {
                border: 1px solid #2874A6;
                background-color: #FFFFFF;
            }

            #showPasswordButton {
                background-color: transparent;
                color: #2874A6;
                border: none;
                font-size: 12px;
                font-weight: bold;
                min-width: 45px;
            }

            #rememberCheckbox {
                color: #555555;
                font-size: 12px;
            }

            #rememberCheckbox::indicator {
                width: 15px;
                height: 15px;
            }

            #forgotPasswordButton {
                background-color: transparent;
                color: #2874A6;
                border: none;
                font-size: 12px;
            }

            #forgotPasswordButton:hover {
                color: #17365D;
            }

            #signInButton {
                background-color: #17365D;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 14px;
                font-size: 14px;
                font-weight: bold;
            }

            #signInButton:hover {
                background-color: #2874A6;
            }

            #signInButton:pressed {
                background-color: #102944;
            }

            #demoNotice {
                background-color: #F0F5FA;
                color: #61758A;
                border-radius: 5px;
                padding: 12px;
                font-size: 11px;
            }

        """)


# --------------------------------------------------
# START THE APPLICATION
# --------------------------------------------------

if __name__ == "__main__":

    app = QApplication(sys.argv)

    app.setFont(QFont("Segoe UI", 10))

    window = LoginWindow()
    window.show()

    sys.exit(app.exec())