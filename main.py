import sys
import sqlite3

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QComboBox
)

from PySide6.QtCore import Qt

from database import init_db

DB_NAME = "my_athletics.db"


# =========================
# CREATE MEETING SCREEN
# =========================
class CreateMeetingScreen(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        title = QLabel("Create Meeting")
        title.setAlignment(Qt.AlignCenter)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Meeting Name")

        save_button = QPushButton("Save Meeting")
        save_button.clicked.connect(self.save_meeting)

        layout.addWidget(title)
        layout.addWidget(self.name_input)
        layout.addWidget(save_button)
        layout.addStretch()

        self.setLayout(layout)

    def save_meeting(self):

        name = self.name_input.text().strip()

        if not name:
            QMessageBox.warning(
                self,
                "Missing Name",
                "Enter a meeting name."
            )
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO meetings
        (name, date, team_mode, status)
        VALUES (?, '', '', 'Draft')
        """, (name,))

        conn.commit()
        conn.close()

        QMessageBox.information(
            self,
            "Saved",
            "Meeting created successfully."
        )

        self.name_input.clear()


# =========================
# LOAD MEETING SCREEN
# =========================
class LoadMeetingScreen(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        title = QLabel("Load Meeting")
        title.setAlignment(Qt.AlignCenter)

        self.list_widget = QListWidget()

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_meetings)

        layout.addWidget(title)
        layout.addWidget(self.list_widget)
        layout.addWidget(refresh_button)

        self.setLayout(layout)

        self.load_meetings()

    def load_meetings(self):

        self.list_widget.clear()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        SELECT id, name
        FROM meetings
        ORDER BY id DESC
        """)

        rows = cur.fetchall()

        conn.close()

        for meeting_id, name in rows:
            self.list_widget.addItem(
                f"{meeting_id} - {name}"
            )

# =========================
# TEAM MANAGEMENT SCREEN
# =========================
class TeamManagementScreen(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        title = QLabel("Team Management")
        title.setAlignment(Qt.AlignCenter)

        self.team_name = QLineEdit()
        self.team_name.setPlaceholderText("Team Name")

        self.team_type = QComboBox()
        self.team_type.addItems(["School", "House"])

        save_button = QPushButton("Add Team")
        save_button.clicked.connect(self.add_team)

        self.team_list = QListWidget()

        refresh_button = QPushButton("Refresh Teams")
        refresh_button.clicked.connect(self.load_teams)

        layout.addWidget(title)
        layout.addWidget(self.team_name)
        layout.addWidget(self.team_type)
        layout.addWidget(save_button)
        layout.addWidget(self.team_list)
        layout.addWidget(refresh_button)

        self.setLayout(layout)

        self.load_teams()

    def add_team(self):

        name = self.team_name.text().strip()

        if not name:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO teams
        (name, team_type)
        VALUES (?, ?)
        """, (
            name,
            self.team_type.currentText()
        ))

        conn.commit()
        conn.close()

        self.team_name.clear()

        self.load_teams()

    def load_teams(self):

        self.team_list.clear()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        SELECT name, team_type
        FROM teams
        ORDER BY name
        """)

        rows = cur.fetchall()

        conn.close()

        for name, team_type in rows:
            self.team_list.addItem(
                f"{name} ({team_type})"
            )
# =========================
# DASHBOARD SCREEN
# =========================
class DashboardScreen(QWidget):

    def __init__(self, stack):
        super().__init__()

        self.stack = stack

        layout = QVBoxLayout()

        title = QLabel("MY ATHLETICS")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Version 1.0 Foundation")
        subtitle.setAlignment(Qt.AlignCenter)

        create_button = QPushButton("Create Meeting")
        create_button.clicked.connect(
            lambda: self.stack.setCurrentIndex(1)
        )

        load_button = QPushButton("Load Meeting")
        teams_button = QPushButton("Teams")
        load_button = QPushButton("Load Meeting")
        teams_button = QPushButton("Teams")

        load_button.clicked.connect(
            lambda: self.stack.setCurrentIndex(2)
        )

        teams_button.clicked.connect(
            lambda: self.stack.setCurrentIndex(3)
        )
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(create_button)
        layout.addWidget(load_button)
        layout.addWidget(teams_button)
        layout.addStretch()

        self.setLayout(layout)


# =========================
# MAIN WINDOW
# =========================
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("My Athletics")
        self.resize(1000, 700)

        self.stack = QStackedWidget()

        self.dashboard = DashboardScreen(self.stack)
        self.create_meeting = CreateMeetingScreen()
        self.load_meeting = LoadMeetingScreen()
        self.teams = TeamManagementScreen()

        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.create_meeting)
        self.stack.addWidget(self.load_meeting)
        self.stack.addWidget(self.teams)

        container = QWidget()

        main_layout = QHBoxLayout()

        menu = QVBoxLayout()

        home_button = QPushButton("Dashboard")
        home_button.clicked.connect(
            lambda: self.stack.setCurrentIndex(0)
        )

        menu.addWidget(home_button)
        menu.addStretch()

        main_layout.addLayout(menu)
        main_layout.addWidget(self.stack)

        container.setLayout(main_layout)

        self.setCentralWidget(container)


# =========================
# PROGRAM START
# =========================
if __name__ == "__main__":

    init_db()

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
    