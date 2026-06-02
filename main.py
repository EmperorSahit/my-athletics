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
# ATHLETE SCREEN
# =========================
class AthleteScreen(QWidget):

    def __init__(self):
        super().__init__()

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

        save_button = QPushButton("Add Athlete")
        save_button.clicked.connect(self.save_athlete)

        self.athlete_list = QListWidget()

        refresh_button = QPushButton("Refresh Athletes")
        refresh_button.clicked.connect(self.load_athletes)

        layout.addWidget(title)
        layout.addWidget(self.name_input)
        layout.addWidget(self.gender_combo)
        layout.addWidget(self.age_combo)
        layout.addWidget(self.team_combo)
        layout.addWidget(save_button)
        layout.addWidget(self.athlete_list)
        layout.addWidget(refresh_button)

        self.setLayout(layout)

        self.load_teams()
        self.load_athletes()

    def load_teams(self):

        self.team_combo.clear()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        SELECT id, name
        FROM teams
        ORDER BY name
        """)

        rows = cur.fetchall()

        conn.close()

        for team_id, name in rows:
            self.team_combo.addItem(
                name,
                team_id
            )

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
            return

        gender = self.gender_combo.currentText()
        age_group = self.age_combo.currentText()

        team_id = self.team_combo.currentData()

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

        self.name_input.clear()

        self.load_athletes()

    def load_athletes(self):

        self.athlete_list.clear()

        meeting_id = get_active_meeting()

        if not meeting_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        SELECT full_name, gender, age_group
        FROM athletes
        WHERE meeting_id = ?
        ORDER BY full_name
        """, (meeting_id,))

        rows = cur.fetchall()

        conn.close()

        for name, gender, age_group in rows:
            self.athlete_list.addItem(
                f"{name} | {gender} | {age_group}"
            )

# =========================
# EVENT SCREEN
# =========================
class EventScreen(QWidget):

    def __init__(self):
        super().__init__()

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
            "U7","U8","U9","U10",
            "U11","U12","U13","U14",
            "U15","U16","U17","Open"
        ])

        self.event_type = QComboBox()
        self.event_type.addItems([
            "Track",
            "Field"
        ])

        save_button = QPushButton("Add Event")
        save_button.clicked.connect(self.save_event)

        self.event_list = QListWidget()

        refresh_button = QPushButton("Refresh Events")
        refresh_button.clicked.connect(self.load_events)

        layout.addWidget(title)
        layout.addWidget(self.event_name)

        layout.addWidget(self.gender_combo)
        layout.addWidget(self.age_combo)

        layout.addWidget(self.event_type)

        layout.addWidget(save_button)
        layout.addWidget(self.event_list)
        layout.addWidget(refresh_button)

        self.setLayout(layout)

        self.load_events()

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
            return

        event_type = self.event_type.currentText()
        gender = self.gender_combo.currentText()
        age_group = self.age_combo.currentText()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

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

        self.event_name.clear()
        self.load_events()
    
    def load_events(self):

        self.event_combo.clear()

        meeting_id = get_active_meeting()

        if not meeting_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        for event_id, name, gender, age_group in rows:
            self.event_combo.addItem(
                f"{name} ({gender} {age_group})",
                event_id
            )
        WHERE meeting_id = ?
        ORDER BY event_name
        """, (meeting_id,))

        rows = cur.fetchall()
        conn.close()

        for event_id, name, gender, age_group in rows:
            display = f"{name} ({gender} {age_group})"
            self.event_combo.addItem(display, event_id)            

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
        layout.addWidget(self.entry_list)
        layout.addWidget(refresh_button)
        layout.addWidget(reload_button)
        layout.addWidget(generate_heats_button)

        self.setLayout(layout)

        self.load_events()
        self.load_athletes()
        self.load_entries()
        self.event_combo.currentIndexChanged.connect(self.filter_athletes_by_event)

    def load_heats(self):

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        self.entry_list.clear()

        event_id = self.event_combo.currentData()
        meeting_id = get_active_meeting()

        if not event_id:
            return

        cur.execute("""
            SELECT a.id
            FROM event_entries ee
            JOIN athletes a ON ee.athlete_id = a.id
            WHERE ee.meeting_id = ?
            AND ee.event_id = ?
            ORDER BY a.full_name ASC
        """, (meeting_id, event_id))

        heats = cur.fetchall()

        for heat_id, heat_no in heats:

            cur.execute("""
                SELECT a.full_name, he.lane_number
                FROM heat_entries he
                JOIN athletes a ON he.athlete_id = a.id
                WHERE he.heat_id = ?
                ORDER BY he.lane_number
            """, (heat_id,))

            athletes = cur.fetchall()

            self.entry_list.addItem(f"Heat {heat_no}")

            for name, lane in athletes:
                self.entry_list.addItem(f"  Lane {lane}: {name}")

        conn.close()

    def load_events(self):

        self.event_list.clear()

        meeting_id = get_active_meeting()

        if not meeting_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        SELECT id, event_name
        FROM events
        WHERE meeting_id = ?
        """, (meeting_id,))

        rows = cur.fetchall()
        conn.close()

        for event_id, name in rows:
            self.event_combo.addItem(name, event_id)

    def load_athletes(self):

        self.athlete_combo.clear()

        meeting_id = get_active_meeting()

        if not meeting_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("""
        SELECT id, full_name
        FROM athletes
        WHERE meeting_id = ?
        """, (meeting_id,))

        rows = cur.fetchall()
        conn.close()

        for athlete_id, name in rows:
            self.athlete_combo.addItem(name, athlete_id)

    def add_entry(self):

        meeting_id = get_active_meeting()

        if not meeting_id:
            return

        event_id = self.event_combo.currentData()
        athlete_id = self.athlete_combo.currentData()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

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
        SELECT e.event_name, a.full_name
        FROM event_entries ee
        JOIN events e ON ee.event_id = e.id
        JOIN athletes a ON ee.athlete_id = a.id
        WHERE ee.meeting_id = ?
        """, (meeting_id,))

        rows = cur.fetchall()
        conn.close()

        for event, athlete in rows:
            self.entry_list.addItem(f"{event} → {athlete}")

    def generate_heats(self):

        meeting_id = get_active_meeting()

        if not meeting_id:
            QMessageBox.warning(
                self,
                "No Active Meeting",
                "Select an active meeting first."
            )
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Get selected event
        event_id = self.event_combo.currentData()

        if not event_id:
            QMessageBox.warning(
                self,
                "No Event Selected",
                "Select an event first."
            )
            return

        # Get all athletes in this event
        cur.execute("""
            SELECT athlete_id
            FROM event_entries
            WHERE meeting_id = ? AND event_id = ?
        """, (meeting_id, event_id))

        athletes = cur.fetchall()

        if not athletes:
            QMessageBox.warning(
                self,
                "No Entries",
                "No athletes entered for this event."
            )
            conn.close()
            return

        athletes = [a[0] for a in athletes]

        # First delete child rows
        cur.execute("""
            DELETE FROM heat_entries
            WHERE heat_id IN (
                SELECT id FROM heats
                WHERE meeting_id = ? AND event_id = ?
            )
        """, (meeting_id, event_id))

        # Then delete parent rows
        cur.execute("""
            DELETE FROM heats
            WHERE meeting_id = ? AND event_id = ?
        """, (meeting_id, event_id))

        # Heat settings
        MAX_PER_HEAT = 8

        heat_number = 1
        index = 0

        while index < len(athletes):

            # Create heat
            cur.execute("""
                INSERT INTO heats
                (meeting_id, event_id, heat_number)
                VALUES (?, ?, ?)
            """, (meeting_id, event_id, heat_number))

            heat_id = cur.lastrowid

            # Fill heat with up to 8 athletes
            lane = 1
            while lane <= MAX_PER_HEAT and index < len(athletes):

                if index >= len(athletes):
                    break

                athlete_id = athletes[index]

                cur.execute("""
                    INSERT INTO heat_entries
                    (heat_id, athlete_id, lane_number)
                    VALUES (?, ?, ?)
                """, (heat_id, athlete_id, lane))

                index += 1
                lane += 1

            heat_number += 1

        conn.commit()
        conn.close()

        QMessageBox.information(
            self,
            "Heats Generated",
            "Heats have been successfully created."
        )

        self.load_heats()

    def refresh_screen(self):
        self.load_events()
        self.load_athletes()
        self.load_entries()   

    def filter_athletes_by_event(self):

        self.athlete_combo.clear()

        meeting_id = get_active_meeting()
        event_id = self.event_combo.currentData()

        if not meeting_id or not event_id:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Get event rules (gender + age group)
        cur.execute("""
            SELECT gender, age_group
            FROM events
            WHERE id = ?
        """, (event_id,))

        event = cur.fetchone()

        if not event:
            conn.close()
            return

        gender, age_group = event

        # Filter athletes
        cur.execute("""
            SELECT id, full_name
            FROM athletes
            WHERE meeting_id = ?
            AND gender = ?
            AND age_group = ?
        """, (meeting_id, gender, age_group))

        rows = cur.fetchall()
        conn.close()

        for athlete_id, name in rows:
            self.athlete_combo.addItem(name, athlete_id)    

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

        generate_finals_button = QPushButton(
            "Generate Finalists"
        )
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
        SELECT h.id,
               e.event_name,
               h.heat_number
        FROM heats h
        JOIN events e
            ON h.event_id = e.id
        WHERE h.meeting_id = ?
        ORDER BY e.event_name,
                 h.heat_number
        """, (meeting_id,))

        rows = cur.fetchall()

        conn.close()

        for heat_id, event_name, heat_no in rows:

            self.heat_combo.addItem(
                f"{event_name} - Heat {heat_no}",
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
            SELECT athlete_id, performance, position
            FROM results
            WHERE heat_id = ?
        """, (heat_id,))

        results = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
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
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        for row in range(
            self.table.rowCount()
        ):

            athlete_item = self.table.item(
                row,
                0
            )

            performance_item = self.table.item(
                row,
                1
            )

            athlete_id = athlete_item.data(
                Qt.UserRole
            )

            performance = ""

            if performance_item:
                performance = (
                    performance_item.text()
                )

                cur.execute("""
                INSERT INTO results (heat_id, athlete_id, performance)
                VALUES (?, ?, ?)
                ON CONFLICT(heat_id, athlete_id)
                DO UPDATE SET performance = excluded.performance
                """, (
                    heat_id,
                    athlete_id,
                    performance
                ))

        conn.commit()
        conn.close()

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

        cur.execute("""
            SELECT athlete_id, performance
            FROM results
            WHERE heat_id = ?
        """, (heat_id,))

        rows = cur.fetchall()

        # Filter valid numeric performances
        cleaned = []

        for athlete_id, perf in rows:
            try:
                value = float(perf)
                cleaned.append((athlete_id, value))
            except:
                continue

        # Sort (lower = faster)
        cleaned.sort(key=lambda x: x[1])

        # Assign positions
        for i, (athlete_id, _) in enumerate(cleaned, start=1):
            cur.execute("""
                UPDATE results
                SET position = ?
                WHERE heat_id = ? AND athlete_id = ?
            """, (i, heat_id, athlete_id))

        conn.commit()
        conn.close()

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
            lambda: self.stack.setCurrentIndex(3)
        )

        mode_button = QPushButton("User Mode")
        mode_button.clicked.connect(
            lambda: self.stack.setCurrentIndex(4)
        )

        athletes_button = QPushButton("Athletes")
        athletes_button.clicked.connect(
            lambda: self.stack.setCurrentIndex(5)
        )

        events_button = QPushButton("Events")
        events_button.clicked.connect(
            lambda: self.stack.setCurrentIndex(6)
        )

        event_entry_button = QPushButton("Event Entries")
        event_entry_button.clicked.connect(
            self.open_event_entries
        )

        results_button = QPushButton("Results")
        results_button.clicked.connect(
            lambda: self.stack.setCurrentIndex(8)
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
        layout.addStretch()

        self.setLayout(layout)

    def open_event_entries(self):
        self.stack.widget(7).refresh_screen()
        self.stack.setCurrentIndex(7)


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

        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.create_meeting)
        self.stack.addWidget(self.load_meeting)
        self.stack.addWidget(self.teams)
        self.stack.addWidget(self.user_mode)
        self.stack.addWidget(self.athletes)
        self.stack.addWidget(self.events)
        self.stack.addWidget(self.event_entry)
        self.stack.addWidget(self.results)

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
        self.load_athletes()
        self.load_entries()

# =========================
# PROGRAM START
# =========================
if __name__ == "__main__":

    init_db()

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
    