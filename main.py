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
    QListWidgetItem,
    QMessageBox,
    QComboBox,
    QDateEdit,
    QTableWidget,
    QTableWidgetItem
)

from PySide6.QtCore import Qt, QDate

from database import (
    init_db,
    set_active_meeting,
    get_active_meeting,
    set_user_mode,
    get_user_mode
)

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
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)

        self.team_mode = QComboBox()
        self.team_mode.addItems([
            "School",
            "House"
        ])

        save_button = QPushButton("Save Meeting")
        save_button.clicked.connect(self.save_meeting)

        layout.addWidget(title)
        layout.addWidget(self.name_input)
        layout.addWidget(self.date_input)
        layout.addWidget(self.team_mode)
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

        meeting_date = self.date_input.date().toString(
            "yyyy-MM-dd"
        )

        team_mode = self.team_mode.currentText()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO meetings
        (name, date, team_mode, status)
        VALUES (?, ?, ?, 'Draft')
        """, (
            name,
            meeting_date,
            team_mode
        ))

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

        activate_button = QPushButton("Set Active Meeting")
        activate_button.clicked.connect(self.activate_meeting)

        layout.addWidget(title)
        layout.addWidget(self.list_widget)
        layout.addWidget(refresh_button)
        layout.addWidget(activate_button)

        self.setLayout(layout)

        self.load_meetings()

    def load_meetings(self):

        self.list_widget.clear()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        SELECT id, name, date, team_mode
        FROM meetings
        ORDER BY id DESC
        """)

        rows = cur.fetchall()

        conn.close()

        for meeting_id, name, date, mode in rows:
            self.list_widget.addItem(
                f"{meeting_id} - {name} | {date} | {mode}"
            )
    def activate_meeting(self):

        item = self.list_widget.currentItem()

        if not item:
            QMessageBox.warning(
                self,
                "Select Meeting",
                "Choose a meeting first."
            )
            return

        meeting_id = int(
            item.text().split(" - ")[0]
        )

        set_active_meeting(meeting_id)

        QMessageBox.information(
            self,
            "Active Meeting",
            f"Meeting {meeting_id} activated."
        )

# =========================
# TEAM MANAGEMENT SCREEN
# =========================
class TeamManagementScreen(QWidget):

    def __init__(self):
        super().__init__()

        self.selected_team_id = None

        layout = QVBoxLayout()

        title = QLabel("Team Management")
        title.setAlignment(Qt.AlignCenter)

        self.team_name = QLineEdit()
        self.team_name.setPlaceholderText("Team Name")

        self.team_type = QComboBox()
        self.team_type.addItems([
            "School",
            "House"
        ])

        add_button = QPushButton(
            "Add Team"
        )
        add_button.clicked.connect(
            self.add_team
        )

        update_button = QPushButton(
            "Update Selected Team"
        )
        update_button.clicked.connect(
            self.update_team
        )

        delete_button = QPushButton(
            "Delete Selected Team"
        )
        delete_button.clicked.connect(
            self.delete_team
        )

        clear_button = QPushButton(
            "Clear Selection"
        )
        clear_button.clicked.connect(
            self.clear_selection
        )

        self.team_list = QListWidget()

        self.team_list.itemClicked.connect(
            self.load_selected_team
        )

        refresh_button = QPushButton(
            "Refresh Teams"
        )
        refresh_button.clicked.connect(
            self.load_teams
        )

        layout.addWidget(title)

        layout.addWidget(
            QLabel("Team / House Name")
        )
        layout.addWidget(self.team_name)

        layout.addWidget(
            QLabel("Type")
        )
        layout.addWidget(self.team_type)

        layout.addWidget(add_button)
        layout.addWidget(update_button)
        layout.addWidget(delete_button)
        layout.addWidget(clear_button)

        layout.addWidget(
            QLabel("Existing Teams / Houses")
        )

        layout.addWidget(self.team_list)
        layout.addWidget(refresh_button)

        self.setLayout(layout)

        self.load_teams()


    # =========================
    # ADD TEAM
    # =========================
    def add_team(self):

        meeting_id = get_active_meeting()

        if not meeting_id:

            QMessageBox.warning(
                self,
                "No Active Meeting",
                "Select an active meeting first."
            )

            return

        name = self.team_name.text().strip()

        if not name:

            QMessageBox.warning(
                self,
                "Missing Name",
                "Enter a team or house name."
            )

            return

        team_type = (
            self.team_type.currentText()
        )

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Prevent duplicate team names
        # inside the same meeting
        cur.execute("""
        SELECT id
        FROM teams
        WHERE meeting_id = ?
        AND LOWER(name) = LOWER(?)
        """, (
            meeting_id,
            name
        ))

        if cur.fetchone():

            conn.close()

            QMessageBox.warning(
                self,
                "Duplicate Team",
                (
                    "A team or house with this "
                    "name already exists."
                )
            )

            return

        cur.execute("""
        INSERT INTO teams
        (
            meeting_id,
            name,
            team_type
        )
        VALUES (?, ?, ?)
        """, (
            meeting_id,
            name,
            team_type
        ))

        conn.commit()
        conn.close()

        QMessageBox.information(
            self,
            "Team Added",
            "Team or house added successfully."
        )

        self.clear_selection()
        self.load_teams()


    # =========================
    # LOAD TEAMS
    # =========================
    def load_teams(self):

        self.team_list.clear()

        meeting_id = get_active_meeting()

        if not meeting_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        SELECT
            id,
            name,
            team_type
        FROM teams
        WHERE meeting_id = ?
        ORDER BY name
        """, (meeting_id,))

        rows = cur.fetchall()

        conn.close()

        for (
            team_id,
            name,
            team_type
        ) in rows:

            item = QListWidgetItem(
                f"{name} ({team_type})"
            )

            item.setData(
                Qt.UserRole,
                team_id
            )

            self.team_list.addItem(
                item
            )


    # =========================
    # LOAD SELECTED TEAM
    # =========================
    def load_selected_team(
        self,
        item
    ):

        team_id = item.data(
            Qt.UserRole
        )

        if not team_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        SELECT
            name,
            team_type
        FROM teams
        WHERE id = ?
        """, (team_id,))

        team = cur.fetchone()

        conn.close()

        if not team:
            return

        self.selected_team_id = team_id

        name = team[0]
        team_type = team[1]

        self.team_name.setText(
            name
        )

        type_index = (
            self.team_type.findText(
                team_type
            )
        )

        if type_index >= 0:

            self.team_type.setCurrentIndex(
                type_index
            )


    # =========================
    # UPDATE TEAM
    # =========================
    def update_team(self):

        if not self.selected_team_id:

            QMessageBox.warning(
                self,
                "No Team Selected",
                (
                    "Select a team or house "
                    "from the list first."
                )
            )

            return

        name = self.team_name.text().strip()

        if not name:

            QMessageBox.warning(
                self,
                "Missing Name",
                "Enter a team or house name."
            )

            return

        meeting_id = get_active_meeting()

        team_type = (
            self.team_type.currentText()
        )

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Make sure another team does
        # not already use this name.
        cur.execute("""
        SELECT id
        FROM teams
        WHERE meeting_id = ?
        AND LOWER(name) = LOWER(?)
        AND id != ?
        """, (
            meeting_id,
            name,
            self.selected_team_id
        ))

        if cur.fetchone():

            conn.close()

            QMessageBox.warning(
                self,
                "Duplicate Team",
                (
                    "Another team or house "
                    "already uses this name."
                )
            )

            return

        cur.execute("""
        UPDATE teams
        SET
            name = ?,
            team_type = ?
        WHERE id = ?
        """, (
            name,
            team_type,
            self.selected_team_id
        ))

        conn.commit()
        conn.close()

        QMessageBox.information(
            self,
            "Team Updated",
            "Team or house updated successfully."
        )

        self.clear_selection()
        self.load_teams()


    # =========================
    # DELETE TEAM
    # =========================
    def delete_team(self):

        if not self.selected_team_id:

            QMessageBox.warning(
                self,
                "No Team Selected",
                (
                    "Select a team or house "
                    "from the list first."
                )
            )

            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Check whether athletes
        # are still assigned to it.
        cur.execute("""
        SELECT COUNT(*)
        FROM athletes
        WHERE team_id = ?
        """, (
            self.selected_team_id,
        ))

        athlete_count = cur.fetchone()[0]

        if athlete_count > 0:

            conn.close()

            QMessageBox.warning(
                self,
                "Team Cannot Be Deleted",
                (
                    f"{athlete_count} athlete(s) "
                    "are still assigned to this "
                    "team or house.\n\n"
                    "Move or delete those athletes "
                    "before deleting the team."
                )
            )

            return

        name = self.team_name.text().strip()

        answer = QMessageBox.question(
            self,
            "Delete Team",
            (
                f"Are you sure you want to "
                f"delete {name}?"
            ),
            QMessageBox.Yes
            | QMessageBox.No
        )

        if answer != QMessageBox.Yes:

            conn.close()
            return

        cur.execute("""
        DELETE FROM teams
        WHERE id = ?
        """, (
            self.selected_team_id,
        ))

        conn.commit()
        conn.close()

        QMessageBox.information(
            self,
            "Team Deleted",
            "Team or house deleted successfully."
        )

        self.clear_selection()
        self.load_teams()


    # =========================
    # CLEAR SELECTION
    # =========================
    def clear_selection(self):

        self.selected_team_id = None

        self.team_list.clearSelection()

        self.team_name.clear()

        if self.team_type.count() > 0:

            self.team_type.setCurrentIndex(0)

# =========================
# ATHLETE SCREEN
# =========================
class AthleteScreen(QWidget):

    def __init__(self):
        super().__init__()

        self.selected_athlete_id = None

        layout = QVBoxLayout()

        title = QLabel("Athletes")
        title.setAlignment(Qt.AlignCenter)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Athlete Name")

        self.gender_combo = QComboBox()
        self.gender_combo.addItems([
            "Male",
            "Female"
        ])

        self.age_combo = QComboBox()
        self.age_combo.addItems([
            "U7","U8","U9","U10",
            "U11","U12","U13","U14",
            "U15","U16","U17","Open"
        ])

        self.team_combo = QComboBox()

        # -------------------------
        # BUTTONS
        # -------------------------
        add_button = QPushButton("Add Athlete")
        add_button.clicked.connect(
            self.save_athlete
        )

        update_button = QPushButton(
            "Update Selected Athlete"
        )
        update_button.clicked.connect(
            self.update_athlete
        )

        delete_button = QPushButton(
            "Delete Selected Athlete"
        )
        delete_button.clicked.connect(
            self.delete_athlete
        )

        withdraw_button = QPushButton(
            "Withdraw Selected Athlete"
        )

        withdraw_button.clicked.connect(
            self.withdraw_athlete
        )

        reactivate_button = QPushButton(
            "Reactivate Selected Athlete"
        )

        reactivate_button.clicked.connect(
            self.reactivate_athlete
        )

        clear_button = QPushButton(
            "Clear Selection"
        )
        clear_button.clicked.connect(
            self.clear_selection
        )

        refresh_button = QPushButton(
            "Refresh Athletes"
        )
        refresh_button.clicked.connect(
            self.load_athletes
        )

        # -------------------------
        # ATHLETE LIST
        # -------------------------
        self.athlete_list = QListWidget()

        self.athlete_list.itemClicked.connect(
            self.load_selected_athlete
        )

        # -------------------------
        # LAYOUT
        # -------------------------
        layout.addWidget(title)

        layout.addWidget(QLabel("Athlete Name"))
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Gender"))
        layout.addWidget(self.gender_combo)

        layout.addWidget(QLabel("Age Group"))
        layout.addWidget(self.age_combo)

        layout.addWidget(QLabel("Team / House"))
        layout.addWidget(self.team_combo)

        layout.addWidget(add_button)
        layout.addWidget(update_button)
        layout.addWidget(withdraw_button)
        layout.addWidget(reactivate_button)
        layout.addWidget(delete_button)
        layout.addWidget(clear_button)

        layout.addWidget(
            QLabel("Existing Athletes")
        )

        layout.addWidget(self.athlete_list)
        layout.addWidget(refresh_button)

        self.setLayout(layout)

        self.load_teams()
        self.load_athletes()


    # =========================
    # LOAD TEAMS
    # =========================
    def load_teams(self):

        self.team_combo.clear()

        meeting_id = get_active_meeting()

        if not meeting_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        SELECT id, name
        FROM teams
        WHERE meeting_id = ?
        ORDER BY name
        """, (meeting_id,))

        rows = cur.fetchall()

        conn.close()

        for team_id, name in rows:

            self.team_combo.addItem(
                name,
                team_id
            )


    # =========================
    # ADD ATHLETE
    # =========================
    def save_athlete(self):

        meeting_id = get_active_meeting()

        if not meeting_id:

            QMessageBox.warning(
                self,
                "No Active Meeting",
                "Select an active meeting first."
            )

            return

        name = self.name_input.text().strip()

        if not name:

            QMessageBox.warning(
                self,
                "Missing Name",
                "Enter the athlete's name."
            )

            return

        team_id = self.team_combo.currentData()

        if team_id is None:

            QMessageBox.warning(
                self,
                "No Team",
                "Select a team or house first."
            )

            return

        gender = self.gender_combo.currentText()
        age_group = self.age_combo.currentText()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO athletes
        (
            meeting_id,
            full_name,
            gender,
            age_group,
            team_id
        )
        VALUES (?, ?, ?, ?, ?)
        """, (
            meeting_id,
            name,
            gender,
            age_group,
            team_id
        ))

        conn.commit()
        conn.close()

        self.clear_selection()
        self.load_athletes()

        QMessageBox.information(
            self,
            "Athlete Added",
            "Athlete added successfully."
        )


    # =========================
    # LOAD ATHLETES
    # =========================
    def load_athletes(self):

        self.athlete_list.clear()

        meeting_id = get_active_meeting()

        if not meeting_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        SELECT
            a.id,
            a.full_name,
            a.gender,
            a.age_group,
            a.team_id,
            t.name,
            a.status
        FROM athletes a

        LEFT JOIN teams t
            ON a.team_id = t.id

        WHERE a.meeting_id = ?

        ORDER BY
            a.status,
            a.full_name
        """, (meeting_id,))

        rows = cur.fetchall()

        conn.close()

        for (
            athlete_id,
            name,
            gender,
            age_group,
            team_id,
            team_name,
            status
        ) in rows:

            if not team_name:
                team_name = "No Team"

            item = QListWidgetItem(
                f"{name} | {gender} | "
                f"{age_group} | {team_name} | "
                f"{status}"
            )

            item.setData(
                Qt.UserRole,
                athlete_id
            )

            self.athlete_list.addItem(
                item
            )

    # =========================
    # LOAD SELECTED ATHLETE
    # =========================
    def load_selected_athlete(
        self,
        item
    ):

        athlete_id = item.data(
            Qt.UserRole
        )

        if not athlete_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        SELECT
            full_name,
            gender,
            age_group,
            team_id
        FROM athletes
        WHERE id = ?
        """, (athlete_id,))

        athlete = cur.fetchone()

        conn.close()

        if not athlete:
            return

        name = athlete[0]
        gender = athlete[1]
        age_group = athlete[2]
        team_id = athlete[3]

        self.selected_athlete_id = (
            athlete_id
        )

        self.name_input.setText(
            name
        )

        gender_index = (
            self.gender_combo.findText(
                gender
            )
        )

        if gender_index >= 0:
            self.gender_combo.setCurrentIndex(
                gender_index
            )

        age_index = (
            self.age_combo.findText(
                age_group
            )
        )

        if age_index >= 0:
            self.age_combo.setCurrentIndex(
                age_index
            )

        team_index = (
            self.team_combo.findData(
                team_id
            )
        )

        if team_index >= 0:
            self.team_combo.setCurrentIndex(
                team_index
            )


    # =========================
    # UPDATE ATHLETE
    # =========================
    def update_athlete(self):

        if not self.selected_athlete_id:

            QMessageBox.warning(
                self,
                "No Athlete Selected",
                "Select an athlete from the list first."
            )

            return

        name = self.name_input.text().strip()

        if not name:

            QMessageBox.warning(
                self,
                "Missing Name",
                "Enter the athlete's name."
            )

            return

        gender = self.gender_combo.currentText()
        age_group = self.age_combo.currentText()
        team_id = self.team_combo.currentData()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Get previous athlete details
        cur.execute("""
        SELECT
            gender,
            age_group,
            team_id
        FROM athletes
        WHERE id = ?
        """, (
            self.selected_athlete_id,
        ))

        previous = cur.fetchone()

        if not previous:

            conn.close()
            return

        old_gender = previous[0]
        old_age_group = previous[1]

        cur.execute("""
        UPDATE athletes
        SET
            full_name = ?,
            gender = ?,
            age_group = ?,
            team_id = ?
        WHERE id = ?
        """, (
            name,
            gender,
            age_group,
            team_id,
            self.selected_athlete_id
        ))

        # If only their team changes,
        # existing awarded points must move
        # to the new team.
        cur.execute("""
        UPDATE awarded_points
        SET team_id = ?
        WHERE athlete_id = ?
        """, (
            team_id,
            self.selected_athlete_id
        ))

        # If gender or age group changes,
        # existing event entries may now
        # be invalid.
        if (
            gender != old_gender
            or age_group != old_age_group
        ):

            athlete_id = (
                self.selected_athlete_id
            )

            cur.execute("""
            DELETE FROM awarded_points
            WHERE athlete_id = ?
            """, (athlete_id,))

            cur.execute("""
            DELETE FROM final_results
            WHERE athlete_id = ?
            """, (athlete_id,))

            cur.execute("""
            DELETE FROM finals
            WHERE athlete_id = ?
            """, (athlete_id,))

            cur.execute("""
            DELETE FROM results
            WHERE athlete_id = ?
            """, (athlete_id,))

            cur.execute("""
            DELETE FROM heat_entries
            WHERE athlete_id = ?
            """, (athlete_id,))

            cur.execute("""
            DELETE FROM event_entries
            WHERE athlete_id = ?
            """, (athlete_id,))

        conn.commit()
        conn.close()

        QMessageBox.information(
            self,
            "Athlete Updated",
            "Athlete updated successfully."
        )

        self.clear_selection()
        self.load_athletes()

    # =========================
    # WITHDRAW ATHLETE
    # =========================
    def withdraw_athlete(self):

        if not self.selected_athlete_id:

            QMessageBox.warning(
                self,
                "No Athlete Selected",
                "Select an athlete from the list first."
            )

            return

        name = self.name_input.text().strip()

        answer = QMessageBox.question(
            self,
            "Withdraw Athlete",
            (
                f"Mark {name} as withdrawn?\n\n"
                "Their existing entries, results "
                "and points will be preserved."
            ),
            QMessageBox.Yes
            | QMessageBox.No
        )

        if answer != QMessageBox.Yes:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        UPDATE athletes
        SET status = 'Withdrawn'
        WHERE id = ?
        """, (
            self.selected_athlete_id,
        ))

        conn.commit()
        conn.close()

        QMessageBox.information(
            self,
            "Athlete Withdrawn",
            f"{name} has been marked as withdrawn."
        )

        self.clear_selection()
        self.load_athletes()

    # =========================
    # REACTIVATE ATHLETE
    # =========================
    def reactivate_athlete(self):

        if not self.selected_athlete_id:

            QMessageBox.warning(
                self,
                "No Athlete Selected",
                "Select an athlete from the list first."
            )

            return

        name = self.name_input.text().strip()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        UPDATE athletes
        SET status = 'Active'
        WHERE id = ?
        """, (
            self.selected_athlete_id,
        ))

        conn.commit()
        conn.close()

        QMessageBox.information(
            self,
            "Athlete Reactivated",
            f"{name} is active again."
        )

        self.clear_selection()
        self.load_athletes()

    # =========================
    # DELETE ATHLETE
    # =========================
    def delete_athlete(self):

        if not self.selected_athlete_id:

            QMessageBox.warning(
                self,
                "No Athlete Selected",
                "Select an athlete from the list first."
            )

            return

        name = self.name_input.text().strip()

        answer = QMessageBox.question(
            self,
            "Delete Athlete",
            (
                f"Are you sure you want to delete "
                f"{name}?\n\n"
                "Their event entries, heat entries, "
                "results, finals and awarded points "
                "will also be removed."
            ),
            QMessageBox.Yes
            | QMessageBox.No
        )

        if answer != QMessageBox.Yes:
            return

        athlete_id = (
            self.selected_athlete_id
        )

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Remove all related athletics data
        cur.execute("""
        DELETE FROM awarded_points
        WHERE athlete_id = ?
        """, (athlete_id,))

        cur.execute("""
        DELETE FROM final_results
        WHERE athlete_id = ?
        """, (athlete_id,))

        cur.execute("""
        DELETE FROM finals
        WHERE athlete_id = ?
        """, (athlete_id,))

        cur.execute("""
        DELETE FROM results
        WHERE athlete_id = ?
        """, (athlete_id,))

        cur.execute("""
        DELETE FROM heat_entries
        WHERE athlete_id = ?
        """, (athlete_id,))

        cur.execute("""
        DELETE FROM event_entries
        WHERE athlete_id = ?
        """, (athlete_id,))

        # Finally delete athlete
        cur.execute("""
        DELETE FROM athletes
        WHERE id = ?
        """, (athlete_id,))

        conn.commit()
        conn.close()

        QMessageBox.information(
            self,
            "Athlete Deleted",
            "Athlete deleted successfully."
        )

        self.clear_selection()
        self.load_athletes()


    # =========================
    # CLEAR SELECTION
    # =========================
    def clear_selection(self):

        self.selected_athlete_id = None

        self.athlete_list.clearSelection()

        self.name_input.clear()

        if self.gender_combo.count() > 0:
            self.gender_combo.setCurrentIndex(0)

        if self.age_combo.count() > 0:
            self.age_combo.setCurrentIndex(0)

        if self.team_combo.count() > 0:
            self.team_combo.setCurrentIndex(0)

# =========================
# EVENT SCREEN
# =========================
class EventScreen(QWidget):

    def __init__(self):
        super().__init__()

        self.selected_event_id = None

        layout = QVBoxLayout()

        title = QLabel("Events")
        title.setAlignment(Qt.AlignCenter)

        self.event_name = QLineEdit()
        self.event_name.setPlaceholderText("Event Name")

        self.gender_combo = QComboBox()
        self.gender_combo.addItems([
            "Male",
            "Female"
        ])

        self.age_combo = QComboBox()
        self.age_combo.addItems([
            "U7", "U8", "U9", "U10",
            "U11", "U12", "U13", "U14",
            "U15", "U16", "U17", "Open"
        ])

        self.event_type = QComboBox()
        self.event_type.addItems([
            "Track",
            "Field"
        ])

        # -------------------------
        # BUTTONS
        # -------------------------
        add_button = QPushButton(
            "Add Event"
        )
        add_button.clicked.connect(
            self.save_event
        )

        update_button = QPushButton(
            "Update Selected Event"
        )
        update_button.clicked.connect(
            self.update_event
        )

        delete_button = QPushButton(
            "Delete Selected Event"
        )
        delete_button.clicked.connect(
            self.delete_event
        )

        clear_button = QPushButton(
            "Clear Selection"
        )
        clear_button.clicked.connect(
            self.clear_selection
        )

        refresh_button = QPushButton(
            "Refresh Events"
        )
        refresh_button.clicked.connect(
            self.load_events
        )

        # -------------------------
        # EVENT LIST
        # -------------------------
        self.event_list = QListWidget()

        self.event_list.itemClicked.connect(
            self.load_selected_event
        )

        # -------------------------
        # LAYOUT
        # -------------------------
        layout.addWidget(title)

        layout.addWidget(
            QLabel("Event Name")
        )
        layout.addWidget(self.event_name)

        layout.addWidget(
            QLabel("Gender")
        )
        layout.addWidget(self.gender_combo)

        layout.addWidget(
            QLabel("Age Group")
        )
        layout.addWidget(self.age_combo)

        layout.addWidget(
            QLabel("Event Type")
        )
        layout.addWidget(self.event_type)

        layout.addWidget(add_button)
        layout.addWidget(update_button)
        layout.addWidget(delete_button)
        layout.addWidget(clear_button)

        layout.addWidget(
            QLabel("Existing Events")
        )

        layout.addWidget(self.event_list)
        layout.addWidget(refresh_button)

        self.setLayout(layout)

        self.load_events()


    # =========================
    # ADD EVENT
    # =========================
    def save_event(self):

        meeting_id = get_active_meeting()

        if not meeting_id:

            QMessageBox.warning(
                self,
                "No Active Meeting",
                "Select an active meeting first."
            )

            return

        name = self.event_name.text().strip()

        if not name:

            QMessageBox.warning(
                self,
                "Missing Event Name",
                "Enter an event name."
            )

            return

        event_type = (
            self.event_type.currentText()
        )

        gender = (
            self.gender_combo.currentText()
        )

        age_group = (
            self.age_combo.currentText()
        )

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Prevent duplicate events
        cur.execute("""
        SELECT id
        FROM events
        WHERE meeting_id = ?
        AND LOWER(event_name) = LOWER(?)
        AND gender = ?
        AND age_group = ?
        """, (
            meeting_id,
            name,
            gender,
            age_group
        ))

        if cur.fetchone():

            conn.close()

            QMessageBox.warning(
                self,
                "Duplicate Event",
                (
                    "This event already exists "
                    "for this gender and age group."
                )
            )

            return

        cur.execute("""
        INSERT INTO events
        (
            meeting_id,
            event_name,
            event_type,
            gender,
            age_group
        )
        VALUES (?, ?, ?, ?, ?)
        """, (
            meeting_id,
            name,
            event_type,
            gender,
            age_group
        ))

        conn.commit()
        conn.close()

        QMessageBox.information(
            self,
            "Event Added",
            "Event added successfully."
        )

        self.clear_selection()
        self.load_events()


    # =========================
    # LOAD EVENTS
    # =========================
    def load_events(self):

        self.event_list.clear()

        meeting_id = get_active_meeting()

        if not meeting_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        SELECT
            id,
            event_name,
            gender,
            age_group,
            event_type
        FROM events
        WHERE meeting_id = ?
        ORDER BY
            event_name,
            gender,
            age_group
        """, (meeting_id,))

        rows = cur.fetchall()

        conn.close()

        for (
            event_id,
            name,
            gender,
            age_group,
            event_type
        ) in rows:

            item = QListWidgetItem(
                f"{name} "
                f"({gender} {age_group}) "
                f"- {event_type}"
            )

            item.setData(
                Qt.UserRole,
                event_id
            )

            self.event_list.addItem(
                item
            )


    # =========================
    # LOAD SELECTED EVENT
    # =========================
    def load_selected_event(
        self,
        item
    ):

        event_id = item.data(
            Qt.UserRole
        )

        if not event_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        SELECT
            event_name,
            event_type,
            gender,
            age_group
        FROM events
        WHERE id = ?
        """, (event_id,))

        event = cur.fetchone()

        conn.close()

        if not event:
            return

        name = event[0]
        event_type = event[1]
        gender = event[2]
        age_group = event[3]

        self.selected_event_id = (
            event_id
        )

        self.event_name.setText(
            name
        )

        gender_index = (
            self.gender_combo.findText(
                gender
            )
        )

        if gender_index >= 0:

            self.gender_combo.setCurrentIndex(
                gender_index
            )

        age_index = (
            self.age_combo.findText(
                age_group
            )
        )

        if age_index >= 0:

            self.age_combo.setCurrentIndex(
                age_index
            )

        type_index = (
            self.event_type.findText(
                event_type
            )
        )

        if type_index >= 0:

            self.event_type.setCurrentIndex(
                type_index
            )


    # =========================
    # UPDATE EVENT
    # =========================
    def update_event(self):

        if not self.selected_event_id:

            QMessageBox.warning(
                self,
                "No Event Selected",
                "Select an event from the list first."
            )

            return

        meeting_id = get_active_meeting()

        if not meeting_id:
            return

        name = self.event_name.text().strip()

        if not name:

            QMessageBox.warning(
                self,
                "Missing Event Name",
                "Enter an event name."
            )

            return

        event_type = (
            self.event_type.currentText()
        )

        gender = (
            self.gender_combo.currentText()
        )

        age_group = (
            self.age_combo.currentText()
        )

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Get current event details
        cur.execute("""
        SELECT
            event_name,
            event_type,
            gender,
            age_group
        FROM events
        WHERE id = ?
        """, (
            self.selected_event_id,
        ))

        previous = cur.fetchone()

        if not previous:

            conn.close()
            return

        old_name = previous[0]
        old_event_type = previous[1]
        old_gender = previous[2]
        old_age_group = previous[3]

        # Check for duplicate event
        cur.execute("""
        SELECT id
        FROM events
        WHERE meeting_id = ?
        AND LOWER(event_name) = LOWER(?)
        AND gender = ?
        AND age_group = ?
        AND id != ?
        """, (
            meeting_id,
            name,
            gender,
            age_group,
            self.selected_event_id
        ))

        if cur.fetchone():

            conn.close()

            QMessageBox.warning(
                self,
                "Duplicate Event",
                (
                    "Another event already exists "
                    "with this name, gender "
                    "and age group."
                )
            )

            return

        # Changing only the event name is safe.
        #
        # Changing gender, age group or type
        # can invalidate existing competition data.
        structure_changed = (
            event_type != old_event_type
            or gender != old_gender
            or age_group != old_age_group
        )

        if structure_changed:

            answer = QMessageBox.question(
                self,
                "Event Structure Changed",
                (
                    "You changed the event's gender, "
                    "age group or event type.\n\n"
                    "Existing entries, heats, results, "
                    "finals and points for this event "
                    "must be cleared.\n\n"
                    "Continue with this change?"
                ),
                QMessageBox.Yes
                | QMessageBox.No
            )

            if answer != QMessageBox.Yes:

                conn.close()
                return

            event_id = (
                self.selected_event_id
            )

            # Remove points
            cur.execute("""
            DELETE FROM awarded_points
            WHERE event_id = ?
            """, (event_id,))

            # Remove final results
            cur.execute("""
            DELETE FROM final_results
            WHERE event_id = ?
            """, (event_id,))

            # Remove finalists
            cur.execute("""
            DELETE FROM finals
            WHERE event_id = ?
            """, (event_id,))

            # Remove heat results
            cur.execute("""
            DELETE FROM results
            WHERE heat_id IN (
                SELECT id
                FROM heats
                WHERE event_id = ?
            )
            """, (event_id,))

            # Remove heat entries
            cur.execute("""
            DELETE FROM heat_entries
            WHERE heat_id IN (
                SELECT id
                FROM heats
                WHERE event_id = ?
            )
            """, (event_id,))

            # Remove heats
            cur.execute("""
            DELETE FROM heats
            WHERE event_id = ?
            """, (event_id,))

            # Remove event entries
            cur.execute("""
            DELETE FROM event_entries
            WHERE event_id = ?
            """, (event_id,))

        cur.execute("""
        UPDATE events
        SET
            event_name = ?,
            event_type = ?,
            gender = ?,
            age_group = ?
        WHERE id = ?
        """, (
            name,
            event_type,
            gender,
            age_group,
            self.selected_event_id
        ))

        conn.commit()
        conn.close()

        QMessageBox.information(
            self,
            "Event Updated",
            "Event updated successfully."
        )

        self.clear_selection()
        self.load_events()


    # =========================
    # DELETE EVENT
    # =========================
    def delete_event(self):

        if not self.selected_event_id:

            QMessageBox.warning(
                self,
                "No Event Selected",
                "Select an event from the list first."
            )

            return

        name = self.event_name.text().strip()

        gender = (
            self.gender_combo.currentText()
        )

        age_group = (
            self.age_combo.currentText()
        )

        answer = QMessageBox.question(
            self,
            "Delete Event",
            (
                f"Are you sure you want to delete:\n\n"
                f"{name} ({gender} {age_group})?\n\n"
                "All entries, heats, results, finals "
                "and points for this event will also "
                "be permanently deleted."
            ),
            QMessageBox.Yes
            | QMessageBox.No
        )

        if answer != QMessageBox.Yes:
            return

        event_id = (
            self.selected_event_id
        )

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Remove awarded points
        cur.execute("""
        DELETE FROM awarded_points
        WHERE event_id = ?
        """, (event_id,))

        # Remove final results
        cur.execute("""
        DELETE FROM final_results
        WHERE event_id = ?
        """, (event_id,))

        # Remove finalists
        cur.execute("""
        DELETE FROM finals
        WHERE event_id = ?
        """, (event_id,))

        # Results depend on heat IDs
        cur.execute("""
        DELETE FROM results
        WHERE heat_id IN (
            SELECT id
            FROM heats
            WHERE event_id = ?
        )
        """, (event_id,))

        # Heat entries depend on heat IDs
        cur.execute("""
        DELETE FROM heat_entries
        WHERE heat_id IN (
            SELECT id
            FROM heats
            WHERE event_id = ?
        )
        """, (event_id,))

        # Remove heats
        cur.execute("""
        DELETE FROM heats
        WHERE event_id = ?
        """, (event_id,))

        # Remove event entries
        cur.execute("""
        DELETE FROM event_entries
        WHERE event_id = ?
        """, (event_id,))

        # Finally remove event itself
        cur.execute("""
        DELETE FROM events
        WHERE id = ?
        """, (event_id,))

        conn.commit()
        conn.close()

        QMessageBox.information(
            self,
            "Event Deleted",
            "Event deleted successfully."
        )

        self.clear_selection()
        self.load_events()


    # =========================
    # CLEAR SELECTION
    # =========================
    def clear_selection(self):

        self.selected_event_id = None

        self.event_list.clearSelection()

        self.event_name.clear()

        if self.gender_combo.count() > 0:
            self.gender_combo.setCurrentIndex(0)

        if self.age_combo.count() > 0:
            self.age_combo.setCurrentIndex(0)

        if self.event_type.count() > 0:
            self.event_type.setCurrentIndex(0)

# =========================
# EVENT ENTRY SCREEN
# =========================
class EventEntryScreen(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        title = QLabel("Event Entries")
        title.setAlignment(Qt.AlignCenter)

        self.event_combo = QComboBox()
        self.athlete_combo = QComboBox()

        add_button = QPushButton("Add Athlete to Event")
        add_button.clicked.connect(self.add_entry)

        remove_button = QPushButton(
            "Remove Selected Entry"
        )
        remove_button.clicked.connect(
            self.remove_entry
        )

        self.entry_list = QListWidget()

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_entries)

        generate_heats_button = QPushButton("Generate Heats")
        generate_heats_button.clicked.connect(
            self.generate_heats
        )

        reload_button = QPushButton("Reload Data")
        reload_button.clicked.connect(
            self.refresh_screen
        )

        layout.addWidget(title)
        layout.addWidget(QLabel("Select Event"))
        layout.addWidget(self.event_combo)

        layout.addWidget(QLabel("Select Athlete"))
        layout.addWidget(self.athlete_combo)

        layout.addWidget(add_button)
        layout.addWidget(remove_button)
        layout.addWidget(self.entry_list)
        layout.addWidget(refresh_button)
        layout.addWidget(reload_button)
        layout.addWidget(generate_heats_button)

        self.setLayout(layout)

        self.load_events()
        self.load_athletes()
        self.load_entries()

        self.filter_athletes_by_event()

        self.event_combo.currentIndexChanged.connect(
            self.filter_athletes_by_event
        )

    def load_athletes(self):

        self.filter_athletes_by_event()

    def add_entry(self):

        meeting_id = get_active_meeting()

        if not meeting_id:
            return

        event_id = self.event_combo.currentData()
        athlete_id = self.athlete_combo.currentData()

        if not event_id or not athlete_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Event details
        cur.execute("""
        SELECT gender, age_group
        FROM events
        WHERE id = ?
        """, (event_id,))

        event_gender, event_age = cur.fetchone()

        # Athlete details
        cur.execute("""
        SELECT gender, age_group
        FROM athletes
        WHERE id = ?
        """, (athlete_id,))

        ath_gender, ath_age = cur.fetchone()

        # Validation
        if event_gender != ath_gender or event_age != ath_age:

            QMessageBox.warning(
                self,
                "Invalid Entry",
                "Athlete does not match this event."
            )

            conn.close()
            return

        cur.execute("""
        SELECT id
        FROM event_entries
        WHERE meeting_id = ?
        AND event_id = ?
        AND athlete_id = ?
        """, (
            meeting_id,
            event_id,
            athlete_id
        ))

        if cur.fetchone():

            QMessageBox.warning(
                self,
                "Duplicate Entry",
                "This athlete is already entered in this event."
            )

            conn.close()
            return

        # Add entry
        cur.execute("""
        INSERT INTO event_entries
        (meeting_id, event_id, athlete_id)
        VALUES (?, ?, ?)
        """, (
            meeting_id,
            event_id,
            athlete_id
        ))

        conn.commit()
        conn.close()

        self.load_entries()

    def load_entries(self):

        self.entry_list.clear()

        meeting_id = get_active_meeting()

        if not meeting_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        SELECT
            e.event_name,
            e.gender,
            e.age_group,
            a.full_name,
            ee.event_id,
            ee.athlete_id
        FROM event_entries ee

        JOIN events e
            ON ee.event_id = e.id

        JOIN athletes a
            ON ee.athlete_id = a.id

        WHERE ee.meeting_id = ?

        ORDER BY
            e.event_name,
            e.gender,
            e.age_group,
            a.full_name
        """, (meeting_id,))

        rows = cur.fetchall()

        conn.close()

        current_event = ""

        for (
            event,
            gender,
            age_group,
            athlete,
            event_id,
            athlete_id
        ) in rows:

            heading = (
                f"{event} "
                f"({gender} {age_group})"
            )

            if heading != current_event:

                self.entry_list.addItem("")

                heading_item = QListWidgetItem(
                    heading
                )

                self.entry_list.addItem(
                    heading_item
                )

                current_event = heading

            athlete_item = QListWidgetItem(
                f"    {athlete}"
            )

            athlete_item.setData(
                Qt.UserRole,
                (
                    event_id,
                    athlete_id
                )
            )

            self.entry_list.addItem(
                athlete_item
            )

    # =========================
    # REMOVE EVENT ENTRY
    # =========================
    def remove_entry(self):

        item = self.entry_list.currentItem()

        if not item:

            QMessageBox.warning(
                self,
                "No Entry Selected",
                (
                    "Select an athlete underneath "
                    "an event first."
                )
            )

            return

        entry_data = item.data(
            Qt.UserRole
        )

        # Headings and blank lines
        # do not contain entry data.
        if not entry_data:

            QMessageBox.warning(
                self,
                "Invalid Selection",
                (
                    "Select an athlete entry, "
                    "not an event heading or heat."
                )
            )

            return

        try:
            event_id, athlete_id = entry_data

        except (TypeError, ValueError):

            QMessageBox.warning(
                self,
                "Invalid Selection",
                (
                    "Select an athlete entry "
                    "from the event list."
                )
            )

            return

        meeting_id = get_active_meeting()

        if not meeting_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # -------------------------
        # GET NAMES
        # -------------------------
        cur.execute("""
        SELECT
            a.full_name,
            e.event_name,
            e.gender,
            e.age_group
        FROM athletes a,
             events e
        WHERE a.id = ?
        AND e.id = ?
        """, (
            athlete_id,
            event_id
        ))

        details = cur.fetchone()

        if not details:

            conn.close()
            return

        athlete_name = details[0]
        event_name = details[1]
        gender = details[2]
        age_group = details[3]

        # -------------------------
        # CHECK LINKED DATA
        # -------------------------
        cur.execute("""
        SELECT COUNT(*)
        FROM heat_entries he

        JOIN heats h
            ON he.heat_id = h.id

        WHERE h.event_id = ?
        AND he.athlete_id = ?
        """, (
            event_id,
            athlete_id
        ))

        heat_entry_count = (
            cur.fetchone()[0]
        )

        cur.execute("""
        SELECT COUNT(*)
        FROM results r

        JOIN heats h
            ON r.heat_id = h.id

        WHERE h.event_id = ?
        AND r.athlete_id = ?
        """, (
            event_id,
            athlete_id
        ))

        result_count = (
            cur.fetchone()[0]
        )

        cur.execute("""
        SELECT COUNT(*)
        FROM finals
        WHERE event_id = ?
        AND athlete_id = ?
        """, (
            event_id,
            athlete_id
        ))

        finalist_count = (
            cur.fetchone()[0]
        )

        cur.execute("""
        SELECT COUNT(*)
        FROM final_results
        WHERE event_id = ?
        AND athlete_id = ?
        """, (
            event_id,
            athlete_id
        ))

        final_result_count = (
            cur.fetchone()[0]
        )

        has_competition_data = (
            heat_entry_count > 0
            or result_count > 0
            or finalist_count > 0
            or final_result_count > 0
        )

        # -------------------------
        # CONFIRM REMOVAL
        # -------------------------
        if has_competition_data:

            message = (
                f"{athlete_name} already has "
                f"generated competition data for:\n\n"
                f"{event_name} "
                f"({gender} {age_group})\n\n"
                "Removing this entry will also "
                "remove this athlete's heat entry, "
                "heat result, finalist record, "
                "final result and points for this "
                "event.\n\n"
                "Other athletes will not be deleted.\n\n"
                "Continue?"
            )

        else:

            message = (
                f"Remove {athlete_name} from:\n\n"
                f"{event_name} "
                f"({gender} {age_group})?"
            )

        answer = QMessageBox.question(
            self,
            "Remove Event Entry",
            message,
            QMessageBox.Yes
            | QMessageBox.No
        )

        if answer != QMessageBox.Yes:

            conn.close()
            return

        # -------------------------
        # REMEMBER AFFECTED HEATS
        # -------------------------
        cur.execute("""
        SELECT he.heat_id
        FROM heat_entries he

        JOIN heats h
            ON he.heat_id = h.id

        WHERE h.event_id = ?
        AND he.athlete_id = ?
        """, (
            event_id,
            athlete_id
        ))

        affected_heats = [
            row[0]
            for row in cur.fetchall()
        ]

        # -------------------------
        # DELETE ATHLETE DATA
        # -------------------------

        # Points
        cur.execute("""
        DELETE FROM awarded_points
        WHERE event_id = ?
        AND athlete_id = ?
        """, (
            event_id,
            athlete_id
        ))

        # Final result
        cur.execute("""
        DELETE FROM final_results
        WHERE event_id = ?
        AND athlete_id = ?
        """, (
            event_id,
            athlete_id
        ))

        # Finalist
        cur.execute("""
        DELETE FROM finals
        WHERE event_id = ?
        AND athlete_id = ?
        """, (
            event_id,
            athlete_id
        ))

        # Heat result
        cur.execute("""
        DELETE FROM results
        WHERE athlete_id = ?
        AND heat_id IN (
            SELECT id
            FROM heats
            WHERE event_id = ?
        )
        """, (
            athlete_id,
            event_id
        ))

        # Heat entry
        cur.execute("""
        DELETE FROM heat_entries
        WHERE athlete_id = ?
        AND heat_id IN (
            SELECT id
            FROM heats
            WHERE event_id = ?
        )
        """, (
            athlete_id,
            event_id
        ))

        # Event entry
        cur.execute("""
        DELETE FROM event_entries
        WHERE meeting_id = ?
        AND event_id = ?
        AND athlete_id = ?
        """, (
            meeting_id,
            event_id,
            athlete_id
        ))

        # -------------------------
        # RECALCULATE HEAT POSITIONS
        # -------------------------
        for heat_id in affected_heats:

            cur.execute("""
            UPDATE results
            SET position = NULL
            WHERE heat_id = ?
            """, (heat_id,))

            cur.execute("""
            SELECT e.event_type
            FROM heats h

            JOIN events e
                ON h.event_id = e.id

            WHERE h.id = ?
            """, (heat_id,))

            event_type_row = (
                cur.fetchone()
            )

            if not event_type_row:
                continue

            event_type = (
                event_type_row[0]
            )

            cur.execute("""
            SELECT
                athlete_id,
                performance
            FROM results
            WHERE heat_id = ?
            AND performance != ''
            """, (heat_id,))

            heat_results = []

            for (
                remaining_athlete_id,
                performance
            ) in cur.fetchall():

                try:

                    value = float(
                        performance
                    )

                    heat_results.append(
                        (
                            remaining_athlete_id,
                            value
                        )
                    )

                except (
                    ValueError,
                    TypeError
                ):
                    continue

            if event_type == "Track":

                heat_results.sort(
                    key=lambda x: x[1]
                )

            else:

                heat_results.sort(
                    key=lambda x: x[1],
                    reverse=True
                )

            position = 1

            for (
                remaining_athlete_id,
                value
            ) in heat_results:

                cur.execute("""
                UPDATE results
                SET position = ?
                WHERE heat_id = ?
                AND athlete_id = ?
                """, (
                    position,
                    heat_id,
                    remaining_athlete_id
                ))

                position += 1

        # -------------------------
        # RE-SEED REMAINING FINALISTS
        # -------------------------
        cur.execute("""
        SELECT athlete_id
        FROM finals
        WHERE event_id = ?
        ORDER BY seed_position
        """, (event_id,))

        remaining_finalists = [
            row[0]
            for row in cur.fetchall()
        ]

        seed = 1

        for finalist_id in remaining_finalists:

            cur.execute("""
            UPDATE finals
            SET seed_position = ?
            WHERE event_id = ?
            AND athlete_id = ?
            """, (
                seed,
                event_id,
                finalist_id
            ))

            seed += 1

        # -------------------------
        # RECALCULATE FINAL POSITIONS
        # -------------------------
        cur.execute("""
        UPDATE final_results
        SET position = NULL
        WHERE event_id = ?
        """, (event_id,))

        cur.execute("""
        SELECT event_type
        FROM events
        WHERE id = ?
        """, (event_id,))

        event_type_row = (
            cur.fetchone()
        )

        if event_type_row:

            event_type = (
                event_type_row[0]
            )

            cur.execute("""
            SELECT
                athlete_id,
                performance
            FROM final_results
            WHERE event_id = ?
            AND performance != ''
            """, (event_id,))

            final_results = []

            for (
                remaining_athlete_id,
                performance
            ) in cur.fetchall():

                try:

                    value = float(
                        performance
                    )

                    final_results.append(
                        (
                            remaining_athlete_id,
                            value
                        )
                    )

                except (
                    ValueError,
                    TypeError
                ):
                    continue

            if event_type == "Track":

                final_results.sort(
                    key=lambda x: x[1]
                )

            else:

                final_results.sort(
                    key=lambda x: x[1],
                    reverse=True
                )

            position = 1

            for (
                remaining_athlete_id,
                value
            ) in final_results:

                cur.execute("""
                UPDATE final_results
                SET position = ?
                WHERE event_id = ?
                AND athlete_id = ?
                """, (
                    position,
                    event_id,
                    remaining_athlete_id
                ))

                position += 1

        # -------------------------
        # REBUILD POINTS
        # -------------------------
        cur.execute("""
        DELETE FROM awarded_points
        WHERE event_id = ?
        """, (event_id,))

        cur.execute("""
        SELECT
            fr.athlete_id,
            fr.position,
            a.team_id
        FROM final_results fr

        JOIN athletes a
            ON fr.athlete_id = a.id

        WHERE fr.event_id = ?
        AND fr.position IS NOT NULL
        """, (event_id,))

        remaining_results = (
            cur.fetchall()
        )

        for (
            remaining_athlete_id,
            position,
            team_id
        ) in remaining_results:

            cur.execute("""
            SELECT points
            FROM points_config
            WHERE meeting_id = ?
            AND position = ?
            """, (
                meeting_id,
                position
            ))

            points_row = (
                cur.fetchone()
            )

            if not points_row:
                continue

            points = points_row[0]

            cur.execute("""
            INSERT INTO awarded_points
            (
                meeting_id,
                event_id,
                athlete_id,
                team_id,
                position,
                points
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                meeting_id,
                event_id,
                remaining_athlete_id,
                team_id,
                position,
                points
            ))

        conn.commit()
        conn.close()

        QMessageBox.information(
            self,
            "Entry Removed",
            (
                f"{athlete_name} has been "
                f"removed from {event_name}."
            )
        )

        self.refresh_screen()
                                    
    def generate_heats(self):

        meeting_id = get_active_meeting()

        if not meeting_id:
            QMessageBox.warning(
                self,
                "No Active Meeting",
                "Select an active meeting first."
            )
            return

        event_id = self.event_combo.currentData()

        if not event_id:
            QMessageBox.warning(
                self,
                "No Event Selected",
                "Select an event first."
            )
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Get all athletes entered in this event
        cur.execute("""
            SELECT athlete_id
            FROM event_entries
            WHERE meeting_id = ?
            AND event_id = ?
            ORDER BY athlete_id
        """, (
            meeting_id,
            event_id
        ))

        athletes = [row[0] for row in cur.fetchall()]

        if not athletes:
            QMessageBox.warning(
                self,
                "No Entries",
                "No athletes have been entered for this event."
            )
            conn.close()
            return

        # Delete existing heats for this event
        # First delete the heat entries
        cur.execute("""
            DELETE FROM heat_entries
            WHERE heat_id IN (
                SELECT id
                FROM heats
                WHERE meeting_id = ?
                AND event_id = ?
            )
        """, (
            meeting_id,
            event_id
        ))

        # Then delete the heats
        cur.execute("""
            DELETE FROM heats
            WHERE meeting_id = ?
            AND event_id = ?
        """, (
            meeting_id,
            event_id
        ))

        # Maximum 8 athletes per heat
        MAX_PER_HEAT = 8

        # Preferred lane order
        lane_order = [4, 5, 3, 6, 2, 7, 1, 8]

        heat_number = 1
        index = 0

        while index < len(athletes):

            # Create a new heat
            cur.execute("""
                INSERT INTO heats
                (
                    meeting_id,
                    event_id,
                    heat_number
                )
                VALUES (?, ?, ?)
            """, (
                meeting_id,
                event_id,
                heat_number
            ))

            heat_id = cur.lastrowid

            # Fill this heat
            lane_index = 0

            while (
                lane_index < MAX_PER_HEAT
                and index < len(athletes)
            ):

                athlete_id = athletes[index]

                lane = lane_order[lane_index]

                cur.execute("""
                    INSERT INTO heat_entries
                    (
                        heat_id,
                        athlete_id,
                        lane_number
                    )
                    VALUES (?, ?, ?)
                """, (
                    heat_id,
                    athlete_id,
                    lane
                ))

                index += 1
                lane_index += 1

            heat_number += 1

        conn.commit()
        conn.close()

        QMessageBox.information(
            self,
            "Heats Generated",
            "Heats have been successfully created."
        )

        self.refresh_screen()

    def refresh_screen(self):
        self.load_events()
        self.load_athletes()

        self.entry_list.clear()

        self.load_entries()
        self.load_heats()
        

    def filter_athletes_by_event(self):

        self.athlete_combo.clear()

        meeting_id = get_active_meeting()
        event_id = self.event_combo.currentData()

        if not meeting_id or not event_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Get the selected event's
        # gender and age group
        cur.execute("""
        SELECT
            gender,
            age_group
        FROM events
        WHERE id = ?
        AND meeting_id = ?
        """, (
            event_id,
            meeting_id
        ))

        event = cur.fetchone()

        if not event:

            conn.close()
            return

        gender = event[0]
        age_group = event[1]

        # Only show ACTIVE athletes
        # matching BOTH gender and age group
        cur.execute("""
        SELECT
            id,
            full_name
        FROM athletes
        WHERE meeting_id = ?
        AND gender = ?
        AND age_group = ?
        AND status = 'Active'
        ORDER BY full_name
        """, (
            meeting_id,
            gender,
            age_group
        ))

        athletes = cur.fetchall()

        conn.close()

        for athlete_id, name in athletes:

            self.athlete_combo.addItem(
                name,
                athlete_id
            )

    def load_events(self):

        self.event_combo.clear()

        meeting_id = get_active_meeting()

        if not meeting_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        SELECT
            id,
            event_name,
            gender,
            age_group
        FROM events
        WHERE meeting_id = ?
        ORDER BY event_name
        """, (meeting_id,))

        rows = cur.fetchall()

        conn.close()

        for event_id, name, gender, age_group in rows:
            self.event_combo.addItem(
                f"{name} ({gender} {age_group})",
                event_id
            )        

    def load_heats(self):

        meeting_id = get_active_meeting()

        if not meeting_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Get all heats for this meeting
        cur.execute("""
        SELECT
            h.id,
            h.heat_number,
            e.event_name,
            e.gender,
            e.age_group
        FROM heats h
        JOIN events e
            ON h.event_id = e.id
        WHERE h.meeting_id = ?
        ORDER BY
            e.event_name,
            e.gender,
            e.age_group,
            h.heat_number
        """, (meeting_id,))

        heats = cur.fetchall()

        for heat_id, heat_no, event_name, gender, age_group in heats:

            self.entry_list.addItem(
                f"{event_name} ({gender} {age_group}) - Heat {heat_no}"
            )

            cur.execute("""
            SELECT
                a.full_name,
                he.lane_number
            FROM heat_entries he
            JOIN athletes a
                ON he.athlete_id = a.id
            WHERE he.heat_id = ?
            ORDER BY he.lane_number
            """, (heat_id,))

            athletes = cur.fetchall()

            for name, lane in athletes:
                self.entry_list.addItem(
                    f"    Lane {lane}: {name}"
                )

            self.entry_list.addItem("")

        conn.close()


# =========================
# RESULTS SCREEN
# =========================
class ResultsScreen(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        title = QLabel("Results")
        title.setAlignment(Qt.AlignCenter)

        self.heat_combo = QComboBox()

        refresh_button = QPushButton("Load Heat")
        refresh_button.clicked.connect(
            self.load_heat
        )

        save_button = QPushButton("Save Results")
        save_button.clicked.connect(
            self.save_results
        )

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(
            ["Athlete", "Performance", "Position"]
        )

        layout.addWidget(title)
        layout.addWidget(self.heat_combo)
        layout.addWidget(refresh_button)
        layout.addWidget(self.table)
        layout.addWidget(save_button)

        self.setLayout(layout)

        self.load_heats()

        generate_finals_button = QPushButton("Generate Finalists")
        generate_finals_button.clicked.connect(
            self.generate_finalists
        )                                           

        layout.addWidget(generate_finals_button)

    def load_heats(self):

        self.heat_combo.clear()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        meeting_id = get_active_meeting()

        if not meeting_id:
            conn.close()
            return

        cur.execute("""
        SELECT
            h.id,
            e.event_name,
            e.gender,
            e.age_group,
            h.heat_number
        FROM heats h
        JOIN events e
            ON h.event_id = e.id
        WHERE h.meeting_id = ?
        ORDER BY
            e.event_name,
            e.gender,
            e.age_group,
            h.heat_number
        """, (meeting_id,))

        rows = cur.fetchall()

        conn.close()

        for heat_id, event_name, gender, age_group, heat_no in rows:

            self.heat_combo.addItem(
                f"{event_name} ({gender} {age_group}) - Heat {heat_no}",
                heat_id
            )

    def load_heat(self):

        self.table.setRowCount(0)

        heat_id = self.heat_combo.currentData()

        if not heat_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        SELECT a.id,
               a.full_name,
               he.lane_number
        FROM heat_entries he
        JOIN athletes a
            ON he.athlete_id = a.id
        WHERE he.heat_id = ?
        ORDER BY he.lane_number
        """, (heat_id,))

        athletes = cur.fetchall()

        cur.execute("""
        SELECT athlete_id,
            performance,
            position
        FROM results
        WHERE heat_id = ?
        """, (heat_id,))

        results = {
            r[0]: (r[1], r[2])
            for r in cur.fetchall()
        }

        conn.close()

        self.table.setRowCount(
            len(athletes)
        )

        for row, athlete in enumerate(athletes):

            athlete_id = athlete[0]
            athlete_name = athlete[1]

            item = QTableWidgetItem(
                athlete_name
            )

            item.setData(
                Qt.UserRole,
                athlete_id
            )

            self.table.setItem(
                row,
                0,
                item
            )

            perf, pos = results.get(athlete_id, ("", ""))

            self.table.setItem(row, 1, QTableWidgetItem(str(perf)))
            self.table.setItem(row, 2, QTableWidgetItem(str(pos)))


    def save_results(self):

        heat_id = self.heat_combo.currentData()

        if not heat_id:
            QMessageBox.warning(
                self,
                "No Heat Selected",
                "Please select a heat first."
            )
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        for row in range(self.table.rowCount()):

            athlete_item = self.table.item(row, 0)

            if not athlete_item:
                continue

            athlete_id = athlete_item.data(Qt.UserRole)

            performance_item = self.table.item(row, 1)

            performance = ""

            if performance_item:
                performance = performance_item.text().strip()

            cur.execute("""
                INSERT INTO results
                (
                    heat_id,
                    athlete_id,
                    performance
                )
                VALUES (?, ?, ?)
                ON CONFLICT(heat_id, athlete_id)
                DO UPDATE SET
                    performance = excluded.performance
            """, (
                heat_id,
                athlete_id,
                performance
            ))

        # Save all results first
        conn.commit()
        conn.close()

        # Now calculate positions
        self.calculate_positions(heat_id)

        # Reload the heat so the positions appear on screen
        self.load_heat()

        QMessageBox.information(
            self,
            "Saved",
            "Results saved successfully."
        )


    def generate_finalists(self):

        heat_id = self.heat_combo.currentData()

        if not heat_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Find event
        cur.execute("""
            SELECT event_id
            FROM heats
            WHERE id = ?
        """, (heat_id,))

        row = cur.fetchone()

        if not row:
            conn.close()
            return

        event_id = row[0]

        # Determine Track or Field
        cur.execute("""
            SELECT event_type
            FROM events
            WHERE id = ?
        """, (event_id,))

        event_type = cur.fetchone()[0]

        # Load all results for event
        cur.execute("""
            SELECT
                r.athlete_id,
                r.performance
            FROM results r
            JOIN heats h
                ON r.heat_id = h.id
            WHERE h.event_id = ?
        """, (event_id,))

        rows = cur.fetchall()

        athletes = []

        for athlete_id, performance in rows:

            try:
                value = float(performance)
                athletes.append(
                    (athlete_id, value)
                )
            except:
                pass

        if not athletes:
            conn.close()
            return

        # Track = lower better
        if event_type == "Track":
            athletes.sort(key=lambda x: x[1])

        # Field = higher better
        else:
            athletes.sort(
                key=lambda x: x[1],
                reverse=True
            )

        top8 = athletes[:8]

        cur.execute("""
            DELETE FROM finals
            WHERE event_id = ?
        """, (event_id,))

        seed = 1

        for athlete_id, _ in top8:

            cur.execute("""
                INSERT INTO finals
                (
                    event_id,
                    athlete_id,
                    seed_position
                )
                VALUES (?, ?, ?)
            """, (
                event_id,
                athlete_id,
                seed
            ))

            seed += 1

        conn.commit()
        conn.close()

        QMessageBox.information(
        self,
        "Finalists Generated",
        f"{len(top8)} finalists created."
        )

    def calculate_positions(self, heat_id):

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Find event type
        cur.execute("""
            SELECT e.event_type
            FROM heats h
            JOIN events e
                ON h.event_id = e.id
            WHERE h.id = ?
        """, (heat_id,))

        row = cur.fetchone()

        if not row:
            conn.close()
            return

        event_type = row[0]

        # Load performances
        cur.execute("""
            SELECT athlete_id, performance
            FROM results
            WHERE heat_id = ?
        """, (heat_id,))

        rows = cur.fetchall()

        athletes = []

        for athlete_id, performance in rows:

            try:
                value = float(performance)

                athletes.append(
                    (athlete_id, value)
                )

            except:
                pass

        # Track events:
        # Lowest time wins
        if event_type == "Track":

            athletes.sort(
                key=lambda x: x[1]
            )

        # Field events:
        # Highest distance wins
        else:

            athletes.sort(
                key=lambda x: x[1],
                reverse=True
            )

        # Assign positions
        position = 1

        for athlete_id, value in athletes:

            cur.execute("""
                UPDATE results
                SET position = ?
                WHERE heat_id = ?
                AND athlete_id = ?
            """, (
                position,
                heat_id,
                athlete_id
            ))

            position += 1

        conn.commit()
        conn.close()

# =========================
# FINALS SCREEN
# =========================
class FinalsScreen(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        title = QLabel("Final Results")
        title.setAlignment(Qt.AlignCenter)

        self.event_combo = QComboBox()

        load_button = QPushButton("Load Final")
        load_button.clicked.connect(
            self.load_finals
        )

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Lane",
            "Athlete",
            "Performance",
            "Position"
        ])

        save_button = QPushButton("Save Final Results")
        save_button.clicked.connect(
            self.save_final_results
        )

        layout.addWidget(title)
        layout.addWidget(QLabel("Select Event"))
        layout.addWidget(self.event_combo)
        layout.addWidget(load_button)
        layout.addWidget(self.table)
        layout.addWidget(save_button)

        self.setLayout(layout)

        self.load_events()

        self.event_combo.currentIndexChanged.connect(
            self.load_finals
        )

    def load_events(self):

        self.event_combo.clear()

        meeting_id = get_active_meeting()

        if not meeting_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        SELECT
            id,
            event_name,
            gender,
            age_group
        FROM events
        WHERE meeting_id = ?
        ORDER BY
            event_name,
            gender,
            age_group
        """, (meeting_id,))

        rows = cur.fetchall()

        conn.close()

        for event_id, name, gender, age_group in rows:

            self.event_combo.addItem(
                f"{name} ({gender} {age_group})",
                event_id
            )

    def load_finals(self):

        self.table.setRowCount(0)

        event_id = self.event_combo.currentData()

        if not event_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Finalists
        cur.execute("""
        SELECT
            f.athlete_id,
            a.full_name,
            f.seed_position
        FROM finals f
        JOIN athletes a
            ON f.athlete_id = a.id
        WHERE f.event_id = ?
        ORDER BY f.seed_position
        """, (event_id,))

        finalists = cur.fetchall()

        if not finalists:
            conn.close()

            QMessageBox.information(
                self,
                "No Finalists",
                "No finalists have been generated for this event yet."
            )
            return

        # Existing final results
        cur.execute("""
        SELECT
            athlete_id,
            performance,
            position
        FROM final_results
        WHERE event_id = ?
        """, (event_id,))

        saved_results = {
            row[0]: (row[1], row[2])
            for row in cur.fetchall()
        }

        conn.close()

        # Championship lane order
        lane_order = [4, 5, 3, 6, 2, 7, 1, 8]

        self.table.setRowCount(
            len(finalists)
        )

        for row, finalist in enumerate(finalists):

            athlete_id = finalist[0]
            athlete_name = finalist[1]
            seed = finalist[2]

            if 1 <= seed <= len(lane_order):
                lane = lane_order[seed - 1]
            else:
                lane = ""

            # Lane
            self.table.setItem(
                row,
                0,
                QTableWidgetItem(str(lane))
            )

            # Athlete
            athlete_item = QTableWidgetItem(
                athlete_name
            )

            athlete_item.setData(
                Qt.UserRole,
                athlete_id
            )

            self.table.setItem(
                row,
                1,
                athlete_item
            )

            # Previously saved result
            performance, position = saved_results.get(
                athlete_id,
                ("", "")
            )

            self.table.setItem(
                row,
                2,
                QTableWidgetItem(
                    str(performance)
                )
            )

            self.table.setItem(
                row,
                3,
                QTableWidgetItem(
                    str(position)
                )
            )

    def save_final_results(self):

        event_id = self.event_combo.currentData()

        if not event_id:
            QMessageBox.warning(
                self,
                "No Event Selected",
                "Please select a final event first."
            )
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        for row in range(
            self.table.rowCount()
        ):

            athlete_item = self.table.item(
                row,
                1
            )

            if not athlete_item:
                continue

            athlete_id = athlete_item.data(
                Qt.UserRole
            )

            lane_item = self.table.item(
                row,
                0
            )

            performance_item = self.table.item(
                row,
                2
            )

            lane = 0

            if lane_item:
                try:
                    lane = int(
                        lane_item.text()
                    )
                except ValueError:
                    lane = 0

            performance = ""

            if performance_item:
                performance = (
                    performance_item.text().strip()
                )

            cur.execute("""
            INSERT INTO final_results
            (
                event_id,
                athlete_id,
                lane_number,
                performance
            )
            VALUES (?, ?, ?, ?)

            ON CONFLICT(event_id, athlete_id)
            DO UPDATE SET
                lane_number = excluded.lane_number,
                performance = excluded.performance
            """, (
                event_id,
                athlete_id,
                lane,
                performance
            ))

        conn.commit()
        conn.close()

        self.calculate_final_positions(
            event_id
        )

        self.award_final_points(
            event_id
        )

        self.load_finals()

        QMessageBox.information(
            self,
            "Final Results Saved",
            "Final results saved successfully."
        )

    def calculate_final_positions(
        self,
        event_id
    ):

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Determine event type
        cur.execute("""
        SELECT event_type
        FROM events
        WHERE id = ?
        """, (event_id,))

        row = cur.fetchone()

        if not row:
            conn.close()
            return

        event_type = row[0]

        # Load valid final performances
        cur.execute("""
        SELECT
            athlete_id,
            performance
        FROM final_results
        WHERE event_id = ?
        AND performance != ''
        """, (event_id,))

        rows = cur.fetchall()

        athletes = []

        for athlete_id, performance in rows:

            try:
                value = float(
                    performance
                )

                athletes.append(
                    (
                        athlete_id,
                        value
                    )
                )

            except (
                ValueError,
                TypeError
            ):
                continue

        # Track: fastest time wins
        if event_type == "Track":

            athletes.sort(
                key=lambda x: x[1]
            )

        # Field: longest distance wins
        else:

            athletes.sort(
                key=lambda x: x[1],
                reverse=True
            )

        # Assign final positions
        position = 1

        for athlete_id, value in athletes:

            cur.execute("""
            UPDATE final_results
            SET position = ?
            WHERE event_id = ?
            AND athlete_id = ?
            """, (
                position,
                event_id,
                athlete_id
            ))

            position += 1

        conn.commit()
        conn.close()

    def award_final_points(
        self,
        event_id
    ):

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Find the meeting this event belongs to
        cur.execute("""
        SELECT meeting_id
        FROM events
        WHERE id = ?
        """, (event_id,))

        row = cur.fetchone()

        if not row:
            conn.close()
            return

        meeting_id = row[0]

        # Remove old points for this event.
        # This prevents duplicate or outdated points
        # if final results are edited later.
        cur.execute("""
        DELETE FROM awarded_points
        WHERE event_id = ?
        """, (event_id,))

        # Load final results together with
        # the athlete's team
        cur.execute("""
        SELECT
            fr.athlete_id,
            fr.position,
            a.team_id
        FROM final_results fr
        JOIN athletes a
            ON fr.athlete_id = a.id
        WHERE fr.event_id = ?
        AND fr.position IS NOT NULL
        """, (event_id,))

        results = cur.fetchall()

        for athlete_id, position, team_id in results:

            # Find how many points this position earns
            cur.execute("""
            SELECT points
            FROM points_config
            WHERE meeting_id = ?
            AND position = ?
            """, (
                meeting_id,
                position
            ))

            points_row = cur.fetchone()

            # No points configured for this position
            if not points_row:
                continue

            points = points_row[0]

            cur.execute("""
            INSERT INTO awarded_points
            (
                meeting_id,
                event_id,
                athlete_id,
                team_id,
                position,
                points
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                meeting_id,
                event_id,
                athlete_id,
                team_id,
                position,
                points
            ))

        conn.commit()
        conn.close()

# =========================
# POINTS SETUP SCREEN
# =========================
class PointsSetupScreen(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        title = QLabel("Points Setup")
        title.setAlignment(Qt.AlignCenter)

        info = QLabel(
            "Set the number of points awarded for each finishing position.\n"
            "These values are saved separately for each athletics meeting."
        )
        info.setAlignment(Qt.AlignCenter)

        self.table = QTableWidget()
        self.table.setRowCount(8)
        self.table.setColumnCount(2)

        self.table.setHorizontalHeaderLabels([
            "Position",
            "Points"
        ])

        # Suggested default scoring system
        default_points = [
            10,
            8,
            6,
            5,
            4,
            3,
            2,
            1
        ]

        for row in range(8):

            position = row + 1

            position_item = QTableWidgetItem(
                str(position)
            )

            # Do not allow position number to be edited
            position_item.setFlags(
                position_item.flags()
                & ~Qt.ItemIsEditable
            )

            self.table.setItem(
                row,
                0,
                position_item
            )

            self.table.setItem(
                row,
                1,
                QTableWidgetItem(
                    str(default_points[row])
                )
            )

        save_button = QPushButton(
            "Save Points System"
        )

        save_button.clicked.connect(
            self.save_points
        )

        reload_button = QPushButton(
            "Reload Points"
        )

        reload_button.clicked.connect(
            self.load_points
        )

        layout.addWidget(title)
        layout.addWidget(info)
        layout.addWidget(self.table)
        layout.addWidget(save_button)
        layout.addWidget(reload_button)
        layout.addStretch()

        self.setLayout(layout)

        self.load_points()


    def load_points(self):

        meeting_id = get_active_meeting()

        if not meeting_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        SELECT
            position,
            points
        FROM points_config
        WHERE meeting_id = ?
        """, (meeting_id,))

        saved_points = {
            position: points
            for position, points
            in cur.fetchall()
        }

        conn.close()

        for row in range(8):

            position = row + 1

            if position in saved_points:

                points = saved_points[position]

                # Show whole numbers nicely
                if float(points).is_integer():
                    points = int(points)

                self.table.setItem(
                    row,
                    1,
                    QTableWidgetItem(
                        str(points)
                    )
                )


    def save_points(self):

        meeting_id = get_active_meeting()

        if not meeting_id:

            QMessageBox.warning(
                self,
                "No Active Meeting",
                "Select an active meeting first."
            )

            return

        points_to_save = []

        for row in range(
            self.table.rowCount()
        ):

            position = row + 1

            points_item = self.table.item(
                row,
                1
            )

            if not points_item:

                QMessageBox.warning(
                    self,
                    "Missing Points",
                    f"Enter points for position {position}."
                )

                return

            text = points_item.text().strip()

            try:

                points = float(text)

            except ValueError:

                QMessageBox.warning(
                    self,
                    "Invalid Points",
                    f"Position {position} does not contain a valid number."
                )

                return

            if points < 0:

                QMessageBox.warning(
                    self,
                    "Invalid Points",
                    "Points cannot be negative."
                )

                return

            points_to_save.append(
                (position, points)
            )

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        for position, points in points_to_save:

            cur.execute("""
            INSERT INTO points_config
            (
                meeting_id,
                position,
                points
            )
            VALUES (?, ?, ?)

            ON CONFLICT(meeting_id, position)
            DO UPDATE SET
                points = excluded.points
            """, (
                meeting_id,
                position,
                points
            ))

        conn.commit()
        conn.close()

        QMessageBox.information(
            self,
            "Points Saved",
            "Points system saved successfully."
        )

# =========================
# TEAM STANDINGS SCREEN
# =========================
class TeamStandingsScreen(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        title = QLabel("Team Standings")
        title.setAlignment(Qt.AlignCenter)

        self.meeting_label = QLabel(
            "Points totals for the active meeting"
        )
        self.meeting_label.setAlignment(Qt.AlignCenter)

        self.table = QTableWidget()

        self.table.setColumnCount(3)

        self.table.setHorizontalHeaderLabels([
            "Position",
            "Team / House",
            "Points"
        ])

        refresh_button = QPushButton(
            "Refresh Standings"
        )

        refresh_button.clicked.connect(
            self.load_standings
        )

        layout.addWidget(title)
        layout.addWidget(self.meeting_label)
        layout.addWidget(self.table)
        layout.addWidget(refresh_button)
        layout.addStretch()

        self.setLayout(layout)


    def load_standings(self):

        self.table.setRowCount(0)

        meeting_id = get_active_meeting()

        if not meeting_id:

            self.meeting_label.setText(
                "No active meeting selected."
            )

            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Get meeting name
        cur.execute("""
        SELECT name
        FROM meetings
        WHERE id = ?
        """, (meeting_id,))

        meeting_row = cur.fetchone()

        if meeting_row:
            self.meeting_label.setText(
                f"Standings: {meeting_row[0]}"
            )

        # Load teams that actually have athletes
        # participating in this meeting.
        #
        # Total points are calculated from
        # awarded_points for this meeting only.
        cur.execute("""
        SELECT
            t.id,
            t.name,

            COALESCE(
                (
                    SELECT SUM(ap.points)
                    FROM awarded_points ap
                    WHERE ap.meeting_id = ?
                    AND ap.team_id = t.id
                ),
                0
            ) AS total_points

        FROM teams t

        WHERE EXISTS (
            SELECT 1
            FROM athletes a
            WHERE a.meeting_id = ?
            AND a.team_id = t.id
        )

        ORDER BY
            total_points DESC,
            t.name ASC
        """, (
            meeting_id,
            meeting_id
        ))

        standings = cur.fetchall()

        conn.close()

        self.table.setRowCount(
            len(standings)
        )

        previous_points = None
        previous_position = 0

        for row_index, standing in enumerate(
            standings
        ):

            team_id = standing[0]
            team_name = standing[1]
            points = standing[2]

            # Competition-style ranking:
            # 1, 2, 2, 4 if teams are tied.
            if previous_points is None:
                position = 1

            elif points == previous_points:
                position = previous_position

            else:
                position = row_index + 1

            previous_points = points
            previous_position = position

            # Make whole-number totals look cleaner
            if float(points).is_integer():
                points_display = str(int(points))
            else:
                points_display = str(points)

            self.table.setItem(
                row_index,
                0,
                QTableWidgetItem(
                    str(position)
                )
            )

            self.table.setItem(
                row_index,
                1,
                QTableWidgetItem(
                    team_name
                )
            )

            self.table.setItem(
                row_index,
                2,
                QTableWidgetItem(
                    points_display
                )
            )

# =========================
# USER MODE SCREEN
# =========================
class UserModeScreen(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        title = QLabel("User Mode")

        title.setAlignment(Qt.AlignCenter)

        admin_button = QPushButton("Administrator")
        operator_button = QPushButton("Meet Operator")

        admin_button.clicked.connect(
            lambda: self.set_mode("Administrator")
        )

        operator_button.clicked.connect(
            lambda: self.set_mode("Meet Operator")
        )

        self.current_mode = QLabel()

        layout.addWidget(title)
        layout.addWidget(self.current_mode)
        layout.addWidget(admin_button)
        layout.addWidget(operator_button)

        self.setLayout(layout)

        self.refresh()

    def set_mode(self, mode):

        set_user_mode(mode)

        self.refresh()

    def refresh(self):

        self.current_mode.setText(
            f"Current Mode: {get_user_mode()}"
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
        load_button.clicked.connect(
            lambda: self.stack.setCurrentIndex(2)
        )

        teams_button = QPushButton("Teams")
        teams_button.clicked.connect(
            self.open_teams
        )

        mode_button = QPushButton("User Mode")
        mode_button.clicked.connect(
            lambda: self.stack.setCurrentIndex(4)
        )

        athletes_button = QPushButton("Athletes")
        athletes_button.clicked.connect(
            self.open_athletes
        )

        events_button = QPushButton("Events")
        events_button.clicked.connect(
            self.open_events
        )

        event_entry_button = QPushButton("Event Entries")
        event_entry_button.clicked.connect(
            self.open_event_entries
        )

        results_button = QPushButton("Results")
        results_button.clicked.connect(
        self.open_results
        )

        finals_button = QPushButton("Finals")
        finals_button.clicked.connect(
            lambda: self.stack.setCurrentIndex(9)
        )

        points_button = QPushButton("Points Setup")
        points_button.clicked.connect(
            self.open_points
        )

        standings_button = QPushButton(
            "Team Standings"
        )

        standings_button.clicked.connect(
            self.open_standings
        )

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(create_button)
        layout.addWidget(load_button)
        layout.addWidget(teams_button)
        layout.addWidget(mode_button)
        layout.addWidget(athletes_button)
        layout.addWidget(events_button)
        layout.addWidget(event_entry_button)
        layout.addWidget(results_button)
        layout.addWidget(finals_button)
        layout.addWidget(points_button)
        layout.addWidget(standings_button)
        layout.addStretch()

        self.setLayout(layout)

    def open_events(self):

        event_screen = self.stack.widget(6)

        event_screen.load_events()

        self.stack.setCurrentIndex(6)

    def open_event_entries(self):
        self.stack.widget(7).refresh_screen()
        self.stack.setCurrentIndex(7)

    def open_results(self):

        self.stack.widget(8).load_heats()

        self.stack.setCurrentIndex(8)

    def open_points(self):

        self.stack.widget(10).load_points()

        self.stack.setCurrentIndex(10)

    def open_teams(self):

        team_screen = self.stack.widget(3)

        team_screen.load_teams()

        self.stack.setCurrentIndex(3)

    def open_athletes(self):

        athlete_screen = self.stack.widget(5)

        athlete_screen.load_teams()
        athlete_screen.load_athletes()

        self.stack.setCurrentIndex(5)

    def open_standings(self):

        self.stack.widget(11).load_standings()

        self.stack.setCurrentIndex(11)


# =========================
# MAIN WINDOWpy main.py
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
        self.user_mode = UserModeScreen()
        self.athletes = AthleteScreen()
        self.events = EventScreen()
        self.event_entry = EventEntryScreen()
        self.results = ResultsScreen()
        self.finals = FinalsScreen()
        self.points_setup = PointsSetupScreen()
        self.team_standings = TeamStandingsScreen()

        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.create_meeting)
        self.stack.addWidget(self.load_meeting)
        self.stack.addWidget(self.teams)
        self.stack.addWidget(self.user_mode)
        self.stack.addWidget(self.athletes)
        self.stack.addWidget(self.events)
        self.stack.addWidget(self.event_entry)
        self.stack.addWidget(self.results)
        self.stack.addWidget(self.finals)
        self.stack.addWidget(self.points_setup)
        self.stack.addWidget(self.team_standings)

        container = QWidget()
        athletes_button = QPushButton("Athletes")
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

    def refresh_screen(self):

        self.load_events()

        self.filter_athletes_by_event()

        self.entry_list.clear()

        self.load_entries()
        self.load_heats()

    def open_finals(self):

        self.finals.load_events()
        self.finals.load_finals()

        self.stack.setCurrentWidget(
            self.finals
        )

# =========================
# PROGRAM START
# =========================
if __name__ == "__main__":

    init_db()

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
    