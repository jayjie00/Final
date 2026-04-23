import sys
import os
from PyQt6.QtCore import QTimer, QDateTime, Qt
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QStackedWidget, QFrame, QGridLayout, QScrollArea, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QLineEdit, QMessageBox, QComboBox, QSizePolicy)
from PyQt6.QtGui import QFont, QPixmap, QColor
from PyQt6.QtCore import Qt, QTimer, QDateTime, QDate  # QDate here
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui import QPainter, QPdfWriter, QPageLayout, QPageSize

# Ensure the database folder is accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_manager import get_all_items

# Updated Imports
try:
    from database.db_manager import get_all_items, add_request, get_available_asset_id
except ImportError:
    print("Error: database/db_manager.py not found. Please ensure your folder structure is correct.")
    
class RISFormWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: white; color: black;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(5) 

        # 1. Header Section
        header = QLabel("COLEGIO DE MONTALBAN\nPROPERTY & SUPPLY OFFICE\nREQUISITION AND ISSUANCE SLIP")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header)
        layout.addSpacing(15)

        # 2. Top Info Fields
        top_grid = QGridLayout()
        lbl_s = "font-weight: bold; font-size: 11px; color: black;"
        in_s = "border: none; border-bottom: 1px solid black; color: black; background: transparent;"
        
        self.ris_div = QLineEdit("CDM")
        self.ris_resp_center = QLineEdit()
        
        today_str = QDate.currentDate().toString("MM/dd/yyyy")
        self.ris_date = QLineEdit(today_str)
        self.ris_date.setReadOnly(True)
        self.ris_date.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.ris_date.setStyleSheet(in_s + "color: black; font-weight: bold;")

        self.ris_office = QLineEdit(); self.ris_code = QLineEdit(); self.ris_no = QLineEdit()

        top_grid.addWidget(QLabel("DIVISION:", styleSheet=lbl_s), 0, 0)
        top_grid.addWidget(self.ris_div, 0, 1)
        top_grid.addWidget(QLabel("RESPONSIBLE CENTER:", styleSheet=lbl_s), 0, 2)
        top_grid.addWidget(self.ris_resp_center, 0, 3)
        top_grid.addWidget(QLabel("DATE:", styleSheet=lbl_s), 0, 4)
        top_grid.addWidget(self.ris_date, 0, 5)

        top_grid.addWidget(QLabel("OFFICE:", styleSheet=lbl_s), 1, 0)
        top_grid.addWidget(self.ris_office, 1, 1)
        top_grid.addWidget(QLabel("CODE/CL # :", styleSheet=lbl_s), 1, 2)
        top_grid.addWidget(self.ris_code, 1, 3)
        top_grid.addWidget(QLabel("RIS NO:", styleSheet=lbl_s), 1, 4)
        top_grid.addWidget(self.ris_no, 1, 5)

        for w in [self.ris_div, self.ris_resp_center, self.ris_office, self.ris_code, self.ris_no]:
            w.setStyleSheet(in_s)
        layout.addLayout(top_grid)

        # 3. Items Table
        self.ris_table = QTableWidget(12, 6)
        self.ris_table.setHorizontalHeaderLabels(["STOCK NO", "UNIT", "DESCRIPTION", "QTY (REQ)", "QTY (ISS)", "REMARKS"])
        self.ris_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ris_table.verticalHeader().setVisible(False)
        self.ris_table.setStyleSheet("""
            QTableWidget { gridline-color: black; border: 1.5px solid black; background-color: white; color: black; }
            QHeaderView::section { background-color: white; color: black; border: 1px solid black; font-weight: bold; font-size: 10px; }
        """)
        self.ris_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self.ris_table)

        # 4. Purpose Line
        p_lay = QHBoxLayout()
        self.purpose_in = QLineEdit(); self.purpose_in.setStyleSheet(in_s)
        p_lay.addWidget(QLabel("PURPOSE:", styleSheet=lbl_s))
        p_lay.addWidget(self.purpose_in)
        layout.addLayout(p_lay)
        layout.addSpacing(15)

        # 5. THE FOUR SIGNATURE COLUMNS (Grid Style)
        sig_container = QGridLayout()
        sig_container.setSpacing(10)
        
        # Define styles
        header_s = "font-weight: bold; font-size: 11px; color: black; border-bottom: 1px solid black; padding-bottom: 5px;"
        label_s = "font-weight: bold; font-size: 10px; color: #555;"
        input_s = "border: none; border-bottom: 1px solid black; color: black; background: transparent; font-size: 11px;"

        # Column Headers
        headers = ["Requested By:", "Approved By:", "Issued By:", "Received By:"]
        for col, text in enumerate(headers):
            h_lbl = QLabel(text)
            h_lbl.setStyleSheet(header_s)
            h_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sig_container.addWidget(h_lbl, 0, col)

        # Printed Name Row
        sig_container.addWidget(QLabel("Printed Name:", styleSheet=label_s), 1, 0)
        self.ris_req_name = QLineEdit(); self.ris_req_name.setStyleSheet(input_s)
        sig_container.addWidget(self.ris_req_name, 2, 0)

        self.ris_app_name = QLineEdit(); self.ris_app_name.setStyleSheet(input_s)
        sig_container.addWidget(self.ris_app_name, 2, 1)

        self.ris_iss_name = QLineEdit(); self.ris_iss_name.setStyleSheet(input_s)
        sig_container.addWidget(self.ris_iss_name, 2, 2)

        self.ris_rec_name = QLineEdit(); self.ris_rec_name.setStyleSheet(input_s)
        sig_container.addWidget(self.ris_rec_name, 2, 3)

        # Signature Row (Lines Only)
        sig_container.addWidget(QLabel("Signature:", styleSheet=label_s), 3, 0)
        for i in range(4):
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setStyleSheet("color: black;")
            sig_container.addWidget(line, 4, i)

        # Date Row
        sig_container.addWidget(QLabel("Date:", styleSheet=label_s), 5, 0)
        self.ris_req_date = QLineEdit(); self.ris_req_date.setStyleSheet(input_s)
        sig_container.addWidget(self.ris_req_date, 6, 0)

        self.ris_app_date = QLineEdit(); self.ris_app_date.setStyleSheet(input_s)
        sig_container.addWidget(self.ris_app_date, 6, 1)

        self.ris_iss_date = QLineEdit(); self.ris_iss_date.setStyleSheet(input_s)
        sig_container.addWidget(self.ris_iss_date, 6, 2)

        self.ris_rec_date = QLineEdit(); self.ris_rec_date.setStyleSheet(input_s)
        sig_container.addWidget(self.ris_rec_date, 6, 3)

        layout.addLayout(sig_container)
        layout.addSpacing(10)

        # 6. Bottom Office Stamp
        office_label = QLabel("___________________________\nPROPERTY & SUPPLY OFFICE")
        office_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        office_label.setStyleSheet("font-weight: bold; font-size: 10px;")
        layout.addWidget(office_label)

        layout.addStretch(1)
        
class BorrowersFormWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: white; color: black;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)

        # --- HEADER ---
        header = QLabel("COLEGIO DE MONTALBAN\nPROPERTY AND SUPPLY OFFICE\n\nBORROWER'S FORM")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(header)
        layout.addSpacing(20)

        # --- TABLE SETUP ---
        self.table = QTableWidget(10, 6)
        self.table.setHorizontalHeaderLabels([
            "QTY.", "ITEM DESCRIPTION", "PURPOSE", 
            "DATE/TIME\nBORROWED", "DATE/TIME\nRETURNED", "REMARKS"
        ])
        
        # 1. Enable Wrapping and Auto-Height
        self.table.setWordWrap(True) 
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)

        # 2. COLUMN WIDTH LOGIC
        header = self.table.horizontalHeader()
        
        # Set fixed/interactive widths for the smaller info columns
        self.table.setColumnWidth(0, 45)  # QTY (Very small)
        self.table.setColumnWidth(1, 160) # Item Description
        self.table.setColumnWidth(3, 150) # Date Borrowed
        self.table.setColumnWidth(4, 150) # Date Returned
        self.table.setColumnWidth(5, 100) # Remarks (Shrunk down)

        # 3. MAKE PURPOSE THE DOMINANT COLUMN
        # This tells the Purpose column to take up ALL remaining space
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        self.table.setStyleSheet("""
            QTableWidget { gridline-color: black; border: 1.5px solid black; background-color: white; color: black; }
            QHeaderView::section { background-color: white; color: black; border: 1px solid black; font-weight: bold; }
        """)
        layout.addWidget(self.table)


        # --- FOOTER SECTION (Names, Signatures, Note) ---
        footer_container = QVBoxLayout()
        footer_container.setSpacing(15)

        lbl_style = "font-weight: bold; font-size: 13px; color: black;"
        in_style = "background: transparent; border: none; border-bottom: 1.5px solid black; color: black; padding: 2px;"

        # Row 1: Borrower Name and Room No
        row1 = QHBoxLayout()
        self.borrower_name = QLineEdit()
        self.room_no = QLineEdit()
        
        row1.addWidget(QLabel("NAME OF BORROWER:", styleSheet=lbl_style))
        row1.addWidget(self.borrower_name, 3)
        self.borrower_name.setStyleSheet(in_style)
        
        row1.addSpacing(30)
        
        row1.addWidget(QLabel("ROOM NO:", styleSheet=lbl_style))
        row1.addWidget(self.room_no, 1)
        self.room_no.setStyleSheet(in_style)
        footer_container.addLayout(row1)

        # Row 2: Borrower Signature Line (Directly below Borrower Name)
        row2 = QHBoxLayout()
        self.borrower_sig = QLineEdit()
        row2.addWidget(QLabel("SIGNATURE:", styleSheet=lbl_style))
        row2.addWidget(self.borrower_sig, 1)
        self.borrower_sig.setStyleSheet(in_style)
        row2.addStretch(1) # Keeps the line from stretching to the right edge
        footer_container.addLayout(row2)

        # Row 3: Instructor Name
        row3 = QHBoxLayout()
        self.instructor_name = QLineEdit()
        row3.addWidget(QLabel("NAME OF INSTRUCTOR:", styleSheet=lbl_style))
        row3.addWidget(self.instructor_name, 1)
        self.instructor_name.setStyleSheet(in_style)
        row3.addStretch(1)
        footer_container.addLayout(row3)

        # Row 4: Instructor Signature Line (Directly below Instructor Name)
        row4 = QHBoxLayout()
        self.instructor_sig = QLineEdit()
        row4.addWidget(QLabel("SIGNATURE:", styleSheet=lbl_style))
        row4.addWidget(self.instructor_sig, 1)
        self.instructor_sig.setStyleSheet(in_style)
        row4.addStretch(1)
        footer_container.addLayout(row4)

        # Add the "PROPERTY & SUPPLY OFFICE" right-aligned text
        layout.addLayout(footer_container)
        layout.addSpacing(20)

        office_tag = QLabel("___________________________\nPROPERTY & SUPPLY OFFICE")
        office_tag.setAlignment(Qt.AlignmentFlag.AlignRight)
        office_tag.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(office_tag)

        # The Bottom Note
        note = QLabel("\nNOTE: The instructor shall receive the items and need to sign the borrower's form. "
                      "Releasing and returning items within school days ONLY from 8:00 am to 5:00 pm.")
        note.setStyleSheet("font-size: 11px; font-style: italic; color: black;")
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addStretch()
class StudentKiosk(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CDM Kiosk")
        self.showMaximized()
        self.setStyleSheet("background-color: white; color: black;")
        
        self.cart = {} 
        self.cart_brands = {} 
        self.current_cat = "Supplies"
        self.print_buttons = [] 

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.pages = QStackedWidget()
        self.pages.addWidget(self.create_welcome_screen())      # Index 0
        self.pages.addWidget(self.create_category_screen())     # Index 1
        self.pages.addWidget(self.create_selection_screen())    # Index 2
        self.pages.addWidget(self.create_ris_form_page())       # Index 3
        self.pages.addWidget(self.create_waiting_screen())      # Index 4
        self.pages.addWidget(self.create_printing_sub_screen()) # Index 5
        self.pages.addWidget(self.create_borrow_form_page()) # Index 6

        self.main_layout.addWidget(self.pages)

    # --- SHARED UI COMPONENTS ---
    def create_top_bar(self, title_text, back_to_index):
        bar = QFrame()
        bar.setFixedHeight(100)
        bar.setStyleSheet("background-color: #1B4D2E;")
        layout = QHBoxLayout(bar)
        
        back_btn = QPushButton("BACK")
        back_btn.setFixedSize(120, 50)
        back_btn.setStyleSheet("color: white; border: 1px solid white; font-weight: bold; border-radius: 10px;")
        
        if title_text == "REQUISITION & ISSUANCE SLIP":
            back_btn.clicked.connect(self.handle_back_from_ris)
        else:
            back_btn.clicked.connect(lambda: self.pages.setCurrentIndex(back_to_index))
            
        title = QLabel(title_text)
        title.setFont(QFont("Arial", 26, QFont.Weight.Bold))
        title.setStyleSheet("color: white; border: none; background: transparent;")
        
        layout.addWidget(back_btn)
        layout.addStretch()
        layout.addWidget(title)
        layout.addStretch()
        layout.addSpacing(150)
        return bar

    def handle_back_from_ris(self):
        # Allow user to go back to selection screen to modify their cart
        self.pages.setCurrentIndex(2)

    # --- PAGE 0: WELCOME SCREEN ---
    def create_welcome_screen(self):
        page = QFrame()
        page.setStyleSheet("background-color: #1B4D2E;") 
        
        main_lay = QVBoxLayout(page)
        main_lay.setContentsMargins(60, 60, 60, 60)

        # BReal-time Clock
        top_hbox = QHBoxLayout()
        brand_vbox = QVBoxLayout()
        
        office_title = QLabel("COLEGIO DE MONTALBAN")
        office_title.setStyleSheet("color: white; font-size: 32px; font-weight: bold; background: transparent;")
        subtitle = QLabel("Official Kiosk of the Property and Supply Office")
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 20px; background: transparent;")
        
        brand_vbox.addWidget(office_title)
        brand_vbox.addWidget(subtitle)
        
        self.clock_label = QLabel()
        self.clock_label.setStyleSheet("color: white; font-size: 26px; font-weight: bold; background: transparent;")
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()

        top_hbox.addLayout(brand_vbox)
        top_hbox.addStretch()
        top_hbox.addWidget(self.clock_label)
        main_lay.addLayout(top_hbox)

        # Large Center Action
        main_lay.addStretch(1)
        btn = QPushButton("TOUCH TO START")
        btn.setFixedSize(550, 250)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #E0E4D9; color: #1B4D2E; border-radius: 40px; 
                font-size: 48px; font-weight: bold; border: none;
            }
            QPushButton:hover { background-color: white; }
        """)
        btn.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        main_lay.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        main_lay.addStretch(1)

        # Minimalist Help Button (Popup)
        help_btn = QPushButton("HELP / HOW TO USE")
        help_btn.setFixedSize(250, 50)
        help_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1); 
                color: white; border-radius: 25px; 
                font-size: 14px; font-weight: bold; border: 1px solid rgba(255, 255, 255, 0.3);
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.2); }
        """)
        help_btn.clicked.connect(self.show_help_popup)
        main_lay.addWidget(help_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return page

    def update_clock(self):
        self.clock_label.setText(QDateTime.currentDateTime().toString("MMMM dd, yyyy \n hh:mm:ss AP"))

    def show_help_popup(self):
        help_text = (
            "<b>PROCESS TO GET REQUEST:</b><br><br>"
            "1. <b>SELECT CATEGORY:</b> Choose the type of item needed (Equipment, Printing, etc.)<br>"
            "2. <b>SELECT ITEMS:</b> Add multiple items to your cart.<br>"
            "3. <b>FILL RIS FORM:</b> Provide your student details and purpose.<br>"
            "4. <b>PRINT & COLLECT:</b> Collect your printed slip and proceed to the PSO counter."
        )
        msg = QMessageBox(self)
        msg.setWindowTitle("Kiosk Guide")
        msg.setText(help_text)
        msg.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1B4D2E; font-size: 16px; }
            QPushButton { 
                background-color: #1B4D2E; color: white; 
                padding: 8px 20px; border-radius: 5px; font-weight: bold; 
            }
        """)
        msg.exec()

    # --- PAGE 1: CATEGORY SELECTION (Side-by-Side & Centered Middle) ---
    def create_category_screen(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # 1. Top Bar
        lay.addWidget(self.create_top_bar("CDM PROPERTY AND SUPPLY KIOSK", 0))
        
        # 2. TOP STRETCH (The "Spring" pushing from the top)
        lay.addStretch(1)

        # 3. Main Horizontal Container for the Columns
        columns_container = QWidget()
        h_lay = QHBoxLayout(columns_container)
        h_lay.setContentsMargins(50, 0, 50, 0) # No extra top/bottom margin needed
        h_lay.setSpacing(80) # Space between the two sections
        h_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- LEFT COLUMN: BORROW ---
        borrow_col = QVBoxLayout()
        borrow_col.setSpacing(30)
        
        borrow_title = QLabel("BORROW")
        borrow_title.setFont(QFont("Arial", 38, QFont.Weight.Bold))
        borrow_title.setStyleSheet("color: #1B4D2E;")
        borrow_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        borrow_col.addWidget(borrow_title)
        
        borrow_items_lay = QHBoxLayout()
        borrow_items_lay.addWidget(self.make_category_item("Equipment\nBorrowing", "Equipment"))
        borrow_items_lay.addWidget(self.make_category_item("Sound System\nSetup", "Sound"))
        
        borrow_col.addLayout(borrow_items_lay)
        h_lay.addLayout(borrow_col)

        # --- VERTICAL SEPARATOR LINE ---
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #DDD; min-height: 400px;") # Fixed height for the line
        h_lay.addWidget(line)

        # --- RIGHT COLUMN: REQUEST ---
        request_col = QVBoxLayout()
        request_col.setSpacing(30)
        
        request_title = QLabel("REQUEST")
        request_title.setFont(QFont("Arial", 38, QFont.Weight.Bold))
        request_title.setStyleSheet("color: #1B4D2E;")
        request_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        request_col.addWidget(request_title)
        
        request_items_lay = QHBoxLayout()
        request_items_lay.addWidget(self.make_category_item("Office/School\nSupplies", "Supplies"))
        request_items_lay.addWidget(self.make_category_item("Mass\nPrinting", "Printing"))
        
        request_col.addLayout(request_items_lay)
        h_lay.addLayout(request_col)

        # Add the container to the main layout
        lay.addWidget(columns_container)

        # 4. BOTTOM STRETCH (The "Spring" pushing from the bottom)
        lay.addStretch(1) 
        
        return page

    # Ensure your helper method uses PointingHandCursor for the kiosk feel
    def make_category_item(self, display, code):
        cont = QWidget()
        v = QVBoxLayout(cont)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn = QPushButton()
        btn.setFixedSize(240, 240) # Large visible circles
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #4B8B3B; 
                border-radius: 120px; 
                border: 8px solid #E0E4D9;
            }
            QPushButton:hover {
                background-color: #5BA34A;
                border: 8px solid white;
            }
        """)
        btn.clicked.connect(lambda ch, c=code: self.show_filtered(c))
        
        lbl = QLabel(display)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: black; font-weight: bold; font-size: 22px;")
        
        v.addWidget(btn)
        v.addWidget(lbl)
        return cont
    

    # --- PAGE 2: ITEM SELECTION & CART ---
    def create_selection_screen(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.create_top_bar("SELECT ITEMS", 1))
        
        main_content = QHBoxLayout()
        
        # Sidebar Cart
        self.cart_area = QFrame()
        self.cart_area.setFixedWidth(380)
        self.cart_area.setStyleSheet("background-color: #F4F6F1; border-right: 2px solid #DDD;")
        cart_lay = QVBoxLayout(self.cart_area)
        
        header = QHBoxLayout()
        t = QLabel("SELECTED ITEMS")
        t.setStyleSheet("color: black; font-weight: bold; font-size: 18px;")
        reset_btn = QPushButton("RESET")
        reset_btn.setStyleSheet("color: #A32A2A; font-weight: bold; border: none;")
        reset_btn.clicked.connect(self.reset_cart)
        
        header.addWidget(t)
        header.addStretch()
        header.addWidget(reset_btn)
        cart_lay.addLayout(header)
        
        self.cart_list = QVBoxLayout()
        self.cart_list.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_c = QScrollArea()
        sc_w = QWidget()
        sc_w.setLayout(self.cart_list)
        scroll_c.setWidget(sc_w)
        scroll_c.setWidgetResizable(True)
        scroll_c.setStyleSheet("background: transparent; border: none;")
        cart_lay.addWidget(scroll_c)
        
        checkout_btn = QPushButton("PROCEED TO CHECKOUT")
        checkout_btn.setStyleSheet("""
            QPushButton {
                background-color: #1B4D2E; color: white; 
                padding: 20px; font-weight: bold; border-radius: 10px;
            }
        """)
        checkout_btn.clicked.connect(self.proceed_to_ris_review)
        cart_lay.addWidget(checkout_btn)
        
        # Item Grid
        scroll_g = QScrollArea()
        scroll_g.setWidgetResizable(True)
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        scroll_g.setWidget(self.grid_widget)
        
        main_content.addWidget(self.cart_area)
        main_content.addWidget(scroll_g)
        lay.addLayout(main_content)
        return page

    def add_to_cart_grouped(self, item):
        name, brand = item[1], item[2]
        available_qty = item[3]
        current_qty = self.cart.get(name, 0)

        if current_qty >= available_qty:
            QMessageBox.warning(self, "Stock Limit", f"Cannot add more than {available_qty} {name}(s).")
            return

        self.cart[name] = current_qty + 1
        self.cart_brands[name] = brand
        self.update_cart_display()
        self.refresh_grid()

    def remove_from_cart(self, name):
        if name in self.cart:
            if self.cart[name] > 1:
                self.cart[name] -= 1
            else:
                del self.cart[name]
                if name in self.cart_brands: del self.cart_brands[name]
        self.update_cart_display()
        self.refresh_grid()

    def update_cart_display(self):
        """Refreshes BOTH sidebars (Selection screen and Printing screen)"""
        # List of all cart containers we need to update
        lists_to_update = []
        if hasattr(self, 'cart_list'): lists_to_update.append(self.cart_list)
        if hasattr(self, 'print_cart_list'): lists_to_update.append(self.print_cart_list)

        for cart_container in lists_to_update:
            # Clear current items
            for i in reversed(range(cart_container.count())): 
                w = cart_container.itemAt(i).widget()
                if w: w.setParent(None)
            
            # Add updated items
            for name, qty in self.cart.items():
                f = QFrame()
                f.setStyleSheet("background: white; border-bottom: 1px solid #EEE; border-radius: 5px;")
                l = QHBoxLayout(f)
                
                txt = QLabel(f"{name} x{qty}")
                txt.setStyleSheet("color: black; font-weight: bold; border: none;")
                
                rem = QPushButton("✕")
                rem.setFixedSize(35, 35)
                rem.setStyleSheet("color: red; border: none; font-weight: bold; font-size: 18px;")
                rem.clicked.connect(lambda ch, n=name: self.remove_from_cart(n))
                
                l.addWidget(txt)
                l.addStretch()
                l.addWidget(rem)
                cart_container.addWidget(f)
                
    def create_borrow_form_page(self):
        page = QWidget(); lay = QVBoxLayout(page); lay.setContentsMargins(0,0,0,0)
        lay.addWidget(self.create_top_bar("BORROWER'S FORM", 2))
        
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        self.borrow_form_widget = BorrowersFormWidget()
        scroll.setWidget(self.borrow_form_widget)
        
        submit_btn = QPushButton("SUBMIT BORROW REQUEST")
        submit_btn.setStyleSheet("background-color: #1B4D2E; color: white; padding: 15px; font-weight: bold;")
        submit_btn.clicked.connect(self.handle_final_submit) # Uses your existing submit logic
        
        lay.addWidget(scroll); lay.addWidget(submit_btn)
        return page

    # --- PAGE 5: MASS PRINTING (Unified Cart) ---
    # --- PAGE 5: MASS PRINTING (Fixed Reset & Centering) ---
    def create_printing_sub_screen(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.create_top_bar("MASS PRINTING SELECTION", 1))
        
        main_content = QHBoxLayout()

        # 1. SIDEBAR WITH RESET BUTTON
        self.print_cart_area = QFrame()
        self.print_cart_area.setFixedWidth(380)
        self.print_cart_area.setStyleSheet("background-color: #F4F6F1; border-right: 2px solid #DDD;")
        print_cart_lay = QVBoxLayout(self.print_cart_area)
        
        # Header with RESET
        h_layout = QHBoxLayout()
        cart_header = QLabel("SELECTED ITEMS")
        cart_header.setStyleSheet("color: black; font-weight: bold; font-size: 18px;")
        
        reset_btn = QPushButton("RESET")
        reset_btn.setStyleSheet("color: #A32A2A; font-weight: bold; border: none; background: transparent;")
        reset_btn.clicked.connect(self.reset_cart) # Connects to your existing reset_cart method
        
        h_layout.addWidget(cart_header)
        h_layout.addStretch()
        h_layout.addWidget(reset_btn)
        print_cart_lay.addLayout(h_layout)

        self.print_cart_list = QVBoxLayout()
        self.print_cart_list.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_c = QScrollArea()
        sc_w = QWidget(); sc_w.setLayout(self.print_cart_list)
        scroll_c.setWidget(sc_w); scroll_c.setWidgetResizable(True)
        scroll_c.setStyleSheet("background: transparent; border: none;")
        print_cart_lay.addWidget(scroll_c)
        
        checkout_btn = QPushButton("PROCEED TO CHECKOUT")
        checkout_btn.setStyleSheet("background-color: #1B4D2E; color: white; padding: 20px; font-weight: bold; border-radius: 10px;")
        checkout_btn.clicked.connect(self.proceed_to_ris_review)
        print_cart_lay.addWidget(checkout_btn)

        # 2. CENTERED CONTENT (Form + Buttons)
        # We wrap the right side in a QVBoxLayout with a stretch to center it vertically
        right_side_container = QWidget()
        right_side_lay = QVBoxLayout(right_side_container)
        
        # This is the horizontal layout holding your Form and Buttons
        form_content = QHBoxLayout()
        form_content.setSpacing(40)
        form_content.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center content horizontally

        # Left: Form Panel
        left = QFrame()
        left.setStyleSheet("background-color: #F4F6F1; border-radius: 20px; border: 1px solid #1B4D2E;")
        left.setFixedWidth(400)
        l_lay = QVBoxLayout(left)
        l_lay.setContentsMargins(25, 25, 25, 25)
        
        title = QLabel("PRINT DETAILS")
        title.setStyleSheet("color: black; font-weight: bold; font-size: 26px;")
        
        self.print_item_label = QLabel("Select Category ->")
        self.print_item_label.setStyleSheet("background-color: #E0E4D9; color: black; border-radius: 10px; padding: 15px; font-weight: bold;")
        
        # (Keep your existing QComboBox and QLineEdit setup here...)
        input_style = "background-color: white; color: black; padding: 12px; border: 1px solid #1B4D2E; border-radius: 8px;"
        self.paper_type_in = QComboBox(); self.paper_type_in.addItems(["Regular (70gsm)", "Premium (80gsm)", "Special Paper"]); self.paper_type_in.setStyleSheet(input_style)
        self.paper_size_in = QComboBox(); self.paper_size_in.addItems(["A4", "Long", "Short"]); self.paper_size_in.setStyleSheet(input_style)
        self.print_qty_in = QLineEdit(); self.print_qty_in.setPlaceholderText("Number of pages..."); self.print_qty_in.setStyleSheet(input_style)
        
        add_p = QPushButton("ADD TO CART")
        add_p.setStyleSheet("background-color: #1B4D2E; color: white; font-weight: bold; padding: 20px; border-radius: 30px;")
        add_p.clicked.connect(self.handle_print_proceed)
        
        l_lay.addWidget(title); l_lay.addWidget(self.print_item_label); l_lay.addWidget(QLabel("Paper Type"))
        l_lay.addWidget(self.paper_type_in); l_lay.addWidget(QLabel("Paper Size")); l_lay.addWidget(self.paper_size_in)
        l_lay.addWidget(QLabel("Quantity")); l_lay.addWidget(self.print_qty_in); l_lay.addStretch(); l_lay.addWidget(add_p)
        
        # Right: Category Buttons
        right_buttons_lay = QHBoxLayout()
        self.print_buttons = []
        cats = ["Instructional Materials", "Official Documents", "Examination Materials"]
        for n in cats:
            b = QPushButton(n.replace(" ", "\n"))
            b.setFixedSize(180, 200) # Slightly smaller to ensure they fit nicely
            b.setStyleSheet("background-color: #4B6344; color: white; font-weight: bold; border-radius: 15px;")
            b.clicked.connect(lambda ch, name=n, btn=b: (self.select_print_type(btn), self.print_item_label.setText(name)))
            self.print_buttons.append(b)
            right_buttons_lay.addWidget(b)
            
        form_content.addWidget(left)
        form_content.addLayout(right_buttons_lay)

        # Final assembly with vertical stretches to center the middle part
        right_side_lay.addStretch(1)
        right_side_lay.addLayout(form_content)
        right_side_lay.addStretch(1)

        main_content.addWidget(self.print_cart_area)
        main_content.addWidget(right_side_container, stretch=1)
        
        lay.addLayout(main_content)
        return page
    def save_form_to_pdf(self, form_widget, filename_prefix):
        # 1. Create the 'history_pdfs' folder if it doesn't exist
        project_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(project_dir, "history_pdfs")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 2. Setup the filename with a timestamp
        timestamp = QDateTime.currentDateTime().toString("yyyyMMdd_hhmmss")
        file_path = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.pdf")

        # 3. Initialize the PDF Writer
        pdf_writer = QPdfWriter(file_path)
        # Set to A5 or Letter depending on your paper size
        pdf_writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        pdf_writer.setPageOrientation(QPageLayout.Orientation.Portrait)
        
        # 4. Use QPainter to draw the widget onto the PDF
        painter = QPainter(pdf_writer)
        
        # CALCULATE SCALING (Important for High-Resolution PDF)
        # This prevents the PDF from looking tiny or blurry
        target_rect = painter.viewport()
        scale = pdf_writer.logicalDpiX() / 96.0 # Scale based on screen DPI
        painter.scale(scale, scale)

        # 5. RENDER THE FORM
        # This captures your 'BorrowersFormWidget' or 'RISFormWidget' exactly
        form_widget.render(painter)
        
        painter.end()
    
        print(f"PDF Saved: {file_path}")
        return file_path

    def select_print_type(self, clicked_button):
        for btn in self.print_buttons:
            btn.setStyleSheet("background-color: #4B6344; color: white; font-weight: bold; border-radius: 15px;")
        clicked_button.setStyleSheet("background-color: #1B4D2E; color: white; font-weight: bold; border: 4px solid #E0E4D9; border-radius: 15px;")

    def handle_print_proceed(self):
        t, q = self.print_item_label.text(), self.print_qty_in.text().strip()
        if t == "Select Category ->" or not q.isdigit():
            QMessageBox.warning(self, "Input Error", "Please select a category and quantity.")
            return
            
        key = f"PRINTING: {t} ({self.paper_size_in.currentText()})"
        self.cart[key] = self.cart.get(key, 0) + int(q)
        
        # We NO LONGER jump back to category automatically, 
        # so the user can see it in the sidebar and add more printing if needed.
        QMessageBox.information(self, "Success", f"Added {t} to your cart.")
        self.update_cart_display()

    # --- CHECKOUT LOGIC ---
    def proceed_to_ris_review(self):
        if not self.cart:
            QMessageBox.warning(self, "Empty Cart", "Please add items first.")
            return
        
        if self.current_cat in ["Equipment", "Sound"]:
            self.fill_borrowers_form()
            self.print_ris_btn.setText("PRINT BORROWER SLIP") # Update button text
            self.pages.setCurrentIndex(6)
        else:
            self.fill_ris_form()
            self.print_ris_btn.setText("PRINT RIS FORM NOW") # Update button text
            self.pages.setCurrentIndex(3)

    def fill_borrowers_form(self):
        table = self.borrow_form_widget.table
        table.setRowCount(0)
        now = QDateTime.currentDateTime().toString("MM/dd/yyyy hh:mm AP")
        for name, qty in self.cart.items():
            row = table.rowCount(); table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(str(qty)))
            table.setItem(row, 1, QTableWidgetItem(name))
            table.setItem(row, 3, QTableWidgetItem(now))
            for c in range(6): 
                if table.item(row, c): table.item(row, c).setForeground(QColor("black"))
                
    def fill_ris_form(self):
        table = self.ris_form_widget.ris_table 
        table.setRowCount(0)
        
        for name, qty in self.cart.items():
            row = table.rowCount()
            table.insertRow(row)
            
            # Smart Unit Selection
            unit = "pc"
            if "Printing" in name or "Paper" in name: 
                unit = "pages" 
            elif any(x in name for x in ["Printer", "Projector", "Speaker"]): 
                unit = "unit"
                
            table.setItem(row, 1, QTableWidgetItem(unit)) # Column 1: UNIT
            table.setItem(row, 2, QTableWidgetItem(name)) # Column 2: DESCRIPTION
            table.setItem(row, 3, QTableWidgetItem(str(qty))) # Column 3: QTY (REQ)
                
    def handle_borrow_submit(self):
        # 1. Get the data from the new fields
        borrower = self.borrow_form_widget.borrower_name.text().strip()
        instructor = self.borrow_form_widget.instructor_name.text().strip()
        room = self.borrow_form_widget.room_no.text().strip()
        
        # 2. UPDATED VALIDATION: Removed 'purpose' from this check
        if not borrower or not instructor or not room:
            QMessageBox.warning(self, "Required Fields", 
                                "Please fill in Borrower Name, Instructor, and Room No.")
            return

        # 3. Use the first row's purpose from the table for the database record
        # (Assuming the student typed it into the table earlier)
        table = self.borrow_form_widget.table
        table_purpose = table.item(0, 2).text() if table.item(0, 2) else "Borrowing"

        # 4. Submit to database
        final_purpose = f"Room: {room} | Inst: {instructor} | Purpose: {table_purpose}"
        add_request(borrower, self.cart, final_purpose)
        
        # 5. Move to waiting screen
        self.pages.setCurrentIndex(4) 
        QTimer.singleShot(3000, self.reset_to_start)
    def proceed_to_ris(self):
        # Check if any item in the cart belongs to Borrowing categories
        is_borrowing = any(cat in self.cart_brands.values() or "Equipment" in str(name) or "Sound" in str(name) 
                           for name in self.cart.keys())

        if is_borrowing:
            self.fill_borrowers_form()
            self.pages.setCurrentIndex(6) # Switch to Borrower's Form Page
        else:
            self.fill_standard_ris_form()
            self.pages.setCurrentIndex(3) # Switch to standard RIS Form Page

    def fill_borrowers_form(self):
        # CHANGE THIS LINE: 
        # Instead of self.borrow_table, we point to the table inside the form widget
        table = self.borrow_form_widget.table 
        
        table.setRowCount(0)
        now = QDateTime.currentDateTime().toString("MM/dd/yyyy hh:mm AP")
        
        for name, qty in self.cart.items():
            row = table.rowCount()
            table.insertRow(row)
            
            # Use 'table' here too
            table.setItem(row, 0, QTableWidgetItem(str(qty)))
            table.setItem(row, 1, QTableWidgetItem(name))
            table.setItem(row, 3, QTableWidgetItem(now))
            
            # Ensure text is black for visibility
            for c in range(6):
                if table.item(row, c):
                    table.item(row, c).setForeground(QColor("black"))
        
    #bagoforborrowing
    class BorrowersFormWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setStyleSheet("background-color: white; color: black;")
            layout = QVBoxLayout(self)
            layout.setContentsMargins(40, 40, 40, 40)

            # --- HEADER SECTION ---
            header_vbox = QVBoxLayout()
            header_vbox.setSpacing(2)
            
            title1 = QLabel("COLEGIO DE MONTALBAN")
            title2 = QLabel("PROPERTY AND SUPPLY OFFICE")
            title3 = QLabel("\nBORROWER'S FORM")
            
            for lbl in [title1, title2]:
                lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                header_vbox.addWidget(lbl)
                
            title3.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            title3.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_vbox.addWidget(title3)
            
            layout.addLayout(header_vbox)
            layout.addSpacing(20)

            # --- TABLE SECTION (Matches columns in photo) ---
            self.table = QTableWidget(10, 6) # 10 rows for plenty of space
            self.table.setHorizontalHeaderLabels([
                "QTY.", "ITEM\nDESCRIPTION", "PURPOSE", 
                "DATE/TIME\nBORROWED", "DATE/TIME\nRETURNED", "REMARKS"
            ])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.table.verticalHeader().setVisible(False) # Hide row numbers to look like a form
            self.table.setStyleSheet("""
                QTableWidget { gridline-color: black; border: 1.5px solid black; background-color: white; color: black; }
                QHeaderView::section { 
                    background-color: white; color: black; 
                    font-weight: bold; border: 1.5px solid black;
                    padding: 5px;
                }
            """)
            # Allow editing Purpose and Remarks
            self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.AnyKeyPressed)
            layout.addWidget(self.table)
            layout.addSpacing(30)

           # --- FOOTER DETAILS SECTION ---
            footer_container = QVBoxLayout()
            footer_container.setSpacing(15)

            # Row 1: Borrower Name and Room No
            row1 = QHBoxLayout()
            self.borrower_name = QLineEdit()
            self.room_no = QLineEdit()
            
            lbl_style = "font-weight: bold; font-size: 13px; color: black;"
            in_style = "background: transparent; border: none; border-bottom: 1.5px solid black; color: black; padding: 2px;"

            row1.addWidget(QLabel("NAME OF BORROWER:", styleSheet=lbl_style))
            row1.addWidget(self.borrower_name, 3) # The '3' makes this box longer
            self.borrower_name.setStyleSheet(in_style)
            
            row1.addSpacing(40) # Space between name and room
            
            row1.addWidget(QLabel("ROOM NO:", styleSheet=lbl_style))
            row1.addWidget(self.room_no, 1) # The '1' makes this box shorter
            self.room_no.setStyleSheet(in_style)
            footer_container.addLayout(row1)

            # Row 2: Borrower Signature
            row2 = QHBoxLayout()
            self.borrower_sig = QLineEdit()
            row2.addWidget(QLabel("SIGNATURE:", styleSheet=lbl_style))
            row2.addWidget(self.borrower_sig, 1)
            self.borrower_sig.setStyleSheet(in_style)
            row2.addStretch(1) # Pushes the signature line to the left half
            footer_container.addLayout(row2)

            # Row 3: Instructor Name
            row3 = QHBoxLayout()
            self.instructor_name = QLineEdit()
            row3.addWidget(QLabel("NAME OF INSTRUCTOR:", styleSheet=lbl_style))
            row3.addWidget(self.instructor_name, 1)
            self.instructor_name.setStyleSheet(in_style)
            row3.addStretch(1)
            footer_container.addLayout(row3)

            # Row 4: Instructor Signature
            row4 = QHBoxLayout()
            self.instructor_sig = QLineEdit()
            row4.addWidget(QLabel("SIGNATURE:", styleSheet=lbl_style))
            row4.addWidget(self.instructor_sig, 1)
            self.instructor_sig.setStyleSheet(in_style)
            row4.addStretch(1)
            footer_container.addLayout(row4)

            # Final Footer Labels
            footer_container.addSpacing(20)
            
            office_label = QLabel("___________________________\nPROPERTY & SUPPLY OFFICE")
            office_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            office_label.setStyleSheet("font-weight: bold; font-size: 13px; color: black;")
            footer_container.addWidget(office_label)

            note = QLabel("\nNOTE: The instructor shall receive the items and need to sign the borrower's form. "
                        "Releasing and returning items with in school days ONLY from 8:00 am to 5:00 pm.")
            note.setStyleSheet("font-size: 11px; font-style: italic; color: black;")
            note.setWordWrap(True)
            footer_container.addWidget(note)

            layout.addLayout(footer_container)
            layout.addStretch()

    # --- FORM & GRID REFRESH ---
    def create_ris_form_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0,0,0,0)
        lay.addWidget(self.create_top_bar("REQUISITION & ISSUANCE SLIP", 2))
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.ris_form_widget = RISFormWidget() # Using the new class
        scroll.setWidget(self.ris_form_widget)
        
        submit_btn = QPushButton("SUBMIT REQUEST  ➡")
        submit_btn.setStyleSheet("background-color: #1B4D2E; color: white; padding: 15px; font-weight: bold; border-radius: 25px;")
        submit_btn.clicked.connect(self.handle_final_submit)
        
        lay.addWidget(scroll); lay.addWidget(submit_btn)
        return page

    def refresh_grid(self):
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget: widget.setParent(None)
            
        all_items = get_all_items()
        grouped_items = {}
        for item in all_items:
            if item[5] != self.current_cat: continue
            key = f"{item[1]}|{item[2]}" 
            if key not in grouped_items: grouped_items[key] = list(item)
            else: grouped_items[key][3] += item[3]
            
        for idx, (key, item) in enumerate(grouped_items.items()):
            name, brand, total_qty, img_path = item[1], item[2], item[3], item[6]
            card = QFrame(); card.setFixedSize(220, 320); card.setStyleSheet("background: white; border: 2px solid #DDD; border-radius: 10px;")
            l = QVBoxLayout(card)
            
            img_lbl = QLabel(); img_lbl.setFixedSize(200, 140); img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if img_path and os.path.exists(img_path):
                img_lbl.setPixmap(QPixmap(img_path).scaled(200, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                img_lbl.setText("📦"); img_lbl.setStyleSheet("background-color: #EEE; color: #999; font-size: 40px;")
            
            n_lbl = QLabel(f"{name}\n({brand})"); n_lbl.setStyleSheet("color: black; font-weight: bold; font-size: 16px; border: none;")
            current_qty = self.cart.get(name, 0)
            remaining_qty = max(total_qty - current_qty, 0)
            s_lbl = QLabel(f"Available: {remaining_qty}"); s_lbl.setStyleSheet("color: #666; border: none;")
            
            add_btn = QPushButton("ADD")
            add_btn.setEnabled(remaining_qty > 0)
            add_btn.setStyleSheet("background-color: #4B8B3B; color: white; font-weight: bold; border-radius: 5px; padding: 10px;")
            add_btn.clicked.connect(lambda ch, i=item: self.add_to_cart_grouped(i))
            
            l.addWidget(img_lbl); l.addWidget(n_lbl); l.addWidget(s_lbl); l.addWidget(add_btn)
            self.grid_layout.addWidget(card, idx // 4, idx % 4)

    def handle_final_submit(self):
        try:
            # --- 1. VALIDATION FOR BORROWER'S FORM (Index 6) ---
            if self.pages.currentIndex() == 6:
                borrower = self.borrow_form_widget.borrower_name.text().strip()
                room = self.borrow_form_widget.room_no.text().strip()
                instructor = self.borrow_form_widget.instructor_name.text().strip()
                
                # Check Purpose in the table (Row 0, Column 2)
                purpose_item = self.borrow_form_widget.table.item(0, 2)
                purpose = purpose_item.text().strip() if purpose_item else ""

                if not borrower or not room or not instructor or not purpose:
                    QMessageBox.warning(self, "Missing Information", 
                        "Please fill in all fields including the Purpose in the table.")
                    return

                student_name = borrower
                final_purpose = f"Room: {room} | Inst: {instructor} | Purpose: {purpose}"

            # --- 2. VALIDATION FOR RIS SLIP (Index 3) ---
            else:
                purpose = self.ris_form_widget.purpose_in.text().strip()
                
                # UPDATED: Use the NEW QLineEdit names we created for the Grid
                requester_name = self.ris_form_widget.ris_req_name.text().strip()

                if not purpose or not requester_name:
                    QMessageBox.warning(self, "Missing Information", 
                        "Please provide the Purpose and the Requester's Name.")
                    return

                student_name = requester_name
                final_purpose = purpose

            # --- 3. DATABASE SUBMISSION ---
            # We wrap the database call in its own try/except to catch errors without exiting
            try:
                add_request(student_name, self.cart, final_purpose)
            except Exception as db_err:
                QMessageBox.critical(self, "Database Error", f"Failed to save to database: {str(db_err)}")
                return # Don't move to the success screen if DB fails

            # --- 4. SUCCESS TRANSITION ---
            self.pages.setCurrentIndex(4) 
            QTimer.singleShot(3000, self.reset_to_start)
            
        except Exception as e:
            # This 'catch-all' will tell you EXACTLY why the app is crashing
            print(f"CRITICAL ERROR IN SUBMIT: {str(e)}")
            QMessageBox.critical(self, "System Error", f"Something went wrong: {str(e)}")

    def create_waiting_screen(self):
        page = QFrame(); page.setStyleSheet("background-color: #1B4D2E;"); lay = QVBoxLayout(page)
        msg = QLabel("WAITING FOR VERIFICATION..."); msg.setStyleSheet("color: white; font-size: 40px; font-weight: bold;")
        sub = QLabel("Please wait while the PSO Admin reviews your request."); sub.setStyleSheet("color: #E0E4D9; font-size: 22px;")
        
        self.print_ris_btn = QPushButton("PRINT RIS FORM NOW")
        self.print_ris_btn.setFixedSize(400, 80); self.print_ris_btn.setStyleSheet("background-color: #E0E4D9; color: #1B4D2E; font-weight: bold; font-size: 20px; border-radius: 15px;")
        self.print_ris_btn.clicked.connect(self.process_ris_document)
        
        lay.addStretch(); lay.addWidget(msg, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(sub, alignment=Qt.AlignmentFlag.AlignCenter); lay.addSpacing(30)
        lay.addWidget(self.print_ris_btn, alignment=Qt.AlignmentFlag.AlignCenter); lay.addStretch()
        return page

    def print_current_ris(self):
        # 1. Setup the Printer
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        
        # Open the Print Dialog so the user can choose a printer
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            painter = QPainter(printer)
            
            # 2. Capture the RIS Form Page as an Image
            # We target the actual container inside the scroll area to get the full form
            ris_page_widget = self.pages.widget(3) # Index 3 is your RIS Form
            
            # This takes a 'screenshot' of the widget
            pixmap = ris_page_widget.grab()
            
            # 3. Scale the image to fit the paper
            rect = painter.viewport()
            size = pixmap.size()
            size.scale(rect.size(), Qt.AspectRatioMode.KeepAspectRatio)
            
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(pixmap.rect())
            
            # 4. Draw the image onto the paper
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            
            QMessageBox.information(self, "Printing", "RIS Form sent to printer.")
            self.print_ris_btn.setEnabled(False)
            self.print_ris_btn.setText("RIS PRINTED")

    def reset_to_start(self):
        # 1. Clear core data
        self.cart = {}
        self.cart_brands = {}
        
        # 2. Reset the RIS Form Widget fields
        if hasattr(self, 'ris_form_widget'):
            # Clear Top Info
            self.ris_form_widget.ris_resp_center.clear()
            self.ris_form_widget.ris_office.clear()
            self.ris_form_widget.ris_code.clear()
            self.ris_form_widget.ris_no.clear()
            self.ris_form_widget.purpose_in.clear()
            
            # Clear Table
            self.ris_form_widget.ris_table.setRowCount(0)

            # Clear ALL Signature Grid Fields (The ones from the Grid Layout)
            self.ris_form_widget.ris_req_name.clear()
            self.ris_form_widget.ris_app_name.clear()
            self.ris_form_widget.ris_iss_name.clear()
            self.ris_form_widget.ris_rec_name.clear()
            
            self.ris_form_widget.ris_req_date.clear()
            self.ris_form_widget.ris_app_date.clear()
            self.ris_form_widget.ris_iss_date.clear()
            self.ris_form_widget.ris_rec_date.clear()
            
            # Reset the Main Date to Today
            new_date = QDate.currentDate().toString("MM/dd/yyyy")
            self.ris_form_widget.ris_date.setText(new_date)

        # 3. Reset the Borrower Form fields if they exist
        if hasattr(self, 'borrow_form_widget'):
            self.borrow_form_widget.borrower_name.clear()
            self.borrow_form_widget.room_no.clear()
            self.borrow_form_widget.instructor_name.clear()
            self.borrow_form_widget.borrower_sig.clear()
            self.borrow_form_widget.instructor_sig.clear()
            self.borrow_form_widget.table.setRowCount(0)

        # 4. Final UI Refresh
        self.update_cart_display()
        self.pages.setCurrentIndex(0) # Back to Welcome Screen


    def reset_cart(self):
        # 1. Clear the basic data
        self.cart = {}
        self.cart_brands = {}
        self.update_cart_display()
        self.refresh_grid()
        
        # 2. Clear the Excel-style Signature Table (RIS side)
        # We check if the table exists first to prevent crashes
        if hasattr(self.ris_form_widget, 'sig_table'):
            for row in range(1, 4):
                for col in range(4):
                    item = self.ris_form_widget.sig_table.item(row, col)
                    if item: 
                        item.setText("")

        # 3. Clear the Borrowers Form fields too
        if hasattr(self, 'borrow_form_widget'):
            self.borrow_form_widget.borrower_name.clear()
            self.borrow_form_widget.room_no.clear()
            self.borrow_form_widget.instructor_name.clear()

    def show_filtered(self, category_code):
        self.current_cat = category_code
        if category_code == "Printing": self.pages.setCurrentIndex(5)
        else: self.refresh_grid(); self.pages.setCurrentIndex(2)
        
    def process_ris_document(self):
        try:
            # 1. SETUP THE DIRECTORY
            project_dir = os.path.dirname(os.path.abspath(__file__))
            output_dir = os.path.join(project_dir, "history_pdfs")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            timestamp = QDateTime.currentDateTime().toString("yyyyMMdd_hhmmss")
            
            # 2. DEFINE TARGET AND FILENAME
            if self.pages.currentIndex() == 6 or self.current_cat in ["Equipment", "Sound"]:
                target_widget = self.borrow_form_widget
                file_name = f"BorrowerSlip_{timestamp}.pdf"
                
                # Borrower Specific Height Fix
                target_widget.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                target_widget.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                total_h = target_widget.table.verticalHeader().length() + target_widget.table.horizontalHeader().height() + 4
                target_widget.table.setFixedHeight(total_h)
            else:
                target_widget = self.ris_form_widget
                file_name = f"RIS_Slip_{timestamp}.pdf"
                
                # --- NEW: RIS SLIDER FIX ---
                # Force the main items table to show all rows with no scrollbars
                ris_h = target_widget.ris_table.verticalHeader().length() + target_widget.ris_table.horizontalHeader().height() + 4
                target_widget.ris_table.setFixedHeight(ris_h)
                target_widget.ris_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                target_widget.ris_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

            file_path = os.path.join(output_dir, file_name)

            # 3. CLEAN THE TABLES (Anti-Black Box & Global Slider Fix)
            tables = target_widget.findChildren(QTableWidget)
            for table in tables:
                table.clearSelection()
                table.setCurrentItem(None)
                table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                # Global force-off for scrollbars
                table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

            # 4. PREPARE WIDGET FOR PRINTING
            target_widget.setFixedWidth(850)
            target_widget.adjustSize()

           # 5. START THE PRINTER (Changed from PDF Writer)
            # Use HighResolution for crisp text on paper
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            
            # --- AUTO-PRINT LOGIC ---
            # This skips the "Save As" dialog and sends it to the system's default printer
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            
            # If you want the user to choose the printer first, uncomment the next 3 lines:
            # from PyQt6.QtPrintSupport import QPrintDialog
            # dialog = QPrintDialog(printer, self)
            # if dialog.exec() != QPrintDialog.DialogCode.Accepted: return

            painter = QPainter(printer)
            
            # Calculate scaling for the printer's specific DPI
            # Printers usually have much higher DPI than screens (e.g., 600 vs 96)
            scale_factor = printer.logicalDpiX() / 96.0
            painter.scale(scale_factor, scale_factor)

            # Centering Math (850 is our target width for the form)
            page_rect = painter.viewport()
            x_centered = (page_rect.width() / scale_factor - 850) / 2
            painter.translate(x_centered, 40)

            # Draw the Outer Box
            painter.drawRect(0, 0, target_widget.width(), target_widget.height())

            # 6. RENDER
            target_widget.render(painter)
            painter.end()

            # 7. RESTORE UI (Resetting heights so they work on screen again)
            for table in tables:
                table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                # Give the tables back their original scrollable size for the kiosk screen
                if table == self.ris_form_widget.ris_table:
                    table.setMinimumHeight(300)
                    table.setMaximumHeight(2000)
            

            QMessageBox.information(self, "Success", f"Clean PDF Saved!\n{file_name}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    k = StudentKiosk()
    k.show()
    sys.exit(app.exec())