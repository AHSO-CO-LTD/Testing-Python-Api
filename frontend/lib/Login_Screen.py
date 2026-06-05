import os
import sys

from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QLineEdit
from PyQt5.QtCore import QTimer, QProcess, QTime, QDate

from Global import signal, OskEventFilter, CheckPasswordMessage
from Database import DatabaseConnection, BaseModel, User, CurrentSession
db = DatabaseConnection()
BaseModel.use_db(db)

class LoginScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.current_drive()
        loadUi("form_UI/screenLogin.ui", self)
        self.set_event()
        self.set_state()
    
    def set_event(self):
        # signal=================================================================
        signal.show_error_message_login.connect(self.on_show_error_message)

        # UI=====================================================================
        self.button_login.clicked.connect(self.on_login)
        self.button_show_password.clicked.connect(self.toggle_password_visibility)

    def set_state(self):
        self.start_clock()
        self.toggle_password_visibility()
        self.install_event_fillter()

    # signal=====================================================================
    def on_show_error_message(self, error_message):
        try:
            QMessageBox.critical(self, "Error", error_message )
            # msg_box = QMessageBox()
            # msg_box.setIcon(QMessageBox.Icon.Critical)
            # msg_box.setWindowTitle("Error")
            # msg_box.setText(error_message)
            # msg_box.exec_()
        except Exception as e:
            signal.show_error_message_login.emit(str(e))
            
    # UI=========================================================================
    def on_login(self, checked=False):
        try:
            username = self.lineedit_username.text().strip()
            password = self.lineedit_password.text().strip()

            if not username or not password:
                QMessageBox.warning(self, "Warning", "Please enter UserName and Password!")
                return
            else:
                user = User.get_columns_by(
                    ["UserID", "UserName", "PasswordHash", "Role", "Active", "Attempt"],
                    {"UserName": username}
                )
                if not user or len(user) == 0:
                    QMessageBox.warning(self, "Warning", "UserName does not exist! Please try again.")
                    return
                else:
                    user_info = user[0]
                    #print(user_info["Active"])
                    
                    if user_info["Active"] != "Active":
                        QMessageBox.warning(self, "Warning", "UserName is inactive or locked! Please contact Administrator to activate.")
                        return
                    elif user_info["PasswordHash"] != password:
                        attempt = user_info["Attempt"] + 1
                        
                        if user_info["Role"] != "Administrator" and attempt == 3:
                            # LoginAudit.insert({"UserID":user_info["UserID"], "UserName":user_info["UserName"], "EventType":"Loggedin fail after 3 attempts"})
                            User.update(column="UserName", value=user_info["UserName"], 
                                        updates={"Active":"Inactive"})
                            QMessageBox.warning(self, "Warning", "UserName locked after 3 failed attempts!")
                            return
                        else:
                            User.update(column="UserName", value=user_info["UserName"], 
                                        updates={"Attempt":attempt})
                            if CheckPasswordMessage(password) is not True:
                                message = CheckPasswordMessage(password)
                            else:
                                message = "Password is incorrect!"
                            if user_info["Role"] != "Administrator":
                                QMessageBox.warning(self, "Warning", f"{message} You have {3 - attempt} attempts left.")
                            else:
                                QMessageBox.warning(self, "Warning", f"{message} Please try again.")
                            return
                    else:
                        attempt = user_info["Attempt"] + 1
                        # LoginAudit.insert({"UserID":user_info["UserID"], "UserName":user_info["UserName"], "EventType":f"Loggedin after {attempt} attempts"})
                        User.update(column="UserName", value=user_info["UserName"], 
                                        updates={"Attempt":0})
                        # self.login_user = user_info

                        CurrentSession.insert_or_update({
                            "ID": 1,
                            "UserName": user_info["UserName"]
                        } )

                        signal.switch_screen.emit(1) # MainScreen(1)
                        #QMessageBox.information(self,"Success", "Success!")
        except Exception as e:
            signal.show_error_message_login.emit(str(e))

    def toggle_password_visibility(self, checked=False):
        mode = self.lineedit_password.echoMode()
        self.lineedit_password.setEchoMode(
            QLineEdit.Normal if mode == QLineEdit.Password else QLineEdit.Password
        )

    # Function=======================================================================
    def start_clock(self):
        try:
            # Tạo QTimer để cập nhật mỗi giây
            self.timer_clock = QTimer(self)
            self.timer_clock.timeout.connect(self.update_clock)
            self.timer_clock.start(1000)

            # Hiển thị lần đầu
            self.update_clock()
        except Exception as e:
            signal.show_error_message_main.emit(str(e))

    def update_clock(self):
        now = QDate.currentDate().toString("dd/MM/yyyy") + "  " + QTime.currentTime().toString("HH:mm:ss")
        self.label_clock.setText(now)

    def install_event_fillter(self):
        try:
            widget_list = [self.lineedit_password,
                           self.lineedit_username,
                           ]
            osk = OskEventFilter(self)
            for w in widget_list:
                if w is not None: # comboBox.lineEdit() có thể None nếu không editable
                    w.installEventFilter(osk)
        except Exception as e:
            signal.show_error_message_main.emit(str(e))

    def current_drive(self):
        #Thu muc chua file python hien tai
        if getattr(sys, 'frozen', False):
            #Neu chay tu file exe
            # sys.executable = D:\MyApp\main.exe
            base_dir = os.path.dirname(sys.executable)
        else:
            #Neu chay tu file python
            # sys.modules[__name__].__file__ = D:\MyApp\lib\Main_Screen.py
            module_dir = os.path.dirname(sys.modules[__name__].__file__)
            # Đi lên 1 cấp để tới MyApp
            base_dir = os.path.abspath(os.path.join(module_dir, ".."))

        # Lấy ổ đĩa (C:\, D:\, E:\ ...)
        self.drive = os.path.splitdrive(base_dir)[0]

        # ui_path = os.path.join(base_dir, "form_UI", "screenLogin.ui")
        # # Kiểm tra tồn tại để tránh lỗi
        # if not os.path.exists(ui_path):
        #     signal.show_error_message_main.emit("UI file not found!")
        #     return
        # loadUi(ui_path, self)