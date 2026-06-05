from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSpinBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QSplitter, QScrollArea, QSizePolicy, QLineEdit)
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt, pyqtSignal

from Global import signal, OskEventFilter, CheckPasswordMessage
from Database import DatabaseConnection, BaseModel, User
db = DatabaseConnection()
BaseModel.use_db(db)

class Authentication(QMainWindow):
    closed = pyqtSignal()
    error_signal = pyqtSignal(str)
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        
        self.current_user = user
        loadUi("form_UI/Authentication.ui", self)
        self.setWindowTitle("Authentication — 21CFR Part 11")
        self.Btn_Add_User.clicked.connect(self.On_AddUser)

        #load data len list khi mo
        self.user_name = User.get_column("UserName") #LoadUser()
        self.listWidget_User.addItems(self.user_name)

        self.listWidget_User.itemClicked.connect(self.On_LoadUserInfo)

        self.Btn_Delete_User.clicked.connect(self.On_DeleteUserInfo)

        self.Btn_Save.clicked.connect(self.On_Save)

        # Biến để theo dõi trạng thái hiển thị
        self.password_visible = False
        self.password_visible_1 = False
        # Đặt chế độ ẩn ký tự cho lineEdit nhập mật khẩu
        self.Le_Password_Cre.setEchoMode(QLineEdit.Password)
        self.LE_Password.setEchoMode(QLineEdit.Password)
        # Gắn sự kiện cho nút hiện/ẩn
        self.Btn_Show_Pass.clicked.connect(self.toggle_password_visibility)
        self.Btn_Show_Pass_1.clicked.connect(self.toggle_password_visibility_1)

        #Function khac
        self.install_event_fillter()
        #show error
        self.error_signal.connect(self.show_error_message)

    def toggle_password_visibility(self):
        if self.password_visible:
            self.Le_Password_Cre.setEchoMode(QLineEdit.Password)
        else:
            self.Le_Password_Cre.setEchoMode(QLineEdit.Normal)
        self.password_visible = not self.password_visible

    def toggle_password_visibility_1(self):
        if self.password_visible_1:
            self.LE_Password.setEchoMode(QLineEdit.Password)
        else:
            self.LE_Password.setEchoMode(QLineEdit.Normal)
        self.password_visible_1 = not self.password_visible_1

    def On_Save(self):
        try:
            if not self.listWidget_User.currentItem():
                QMessageBox.warning(self, "Fail", "Please select a user!")
                return
            user_name = self.listWidget_User.currentItem().text()
            full_name = self.Le_Full_Name_Cre.text().strip()
            password_hash = self.Le_Password_Cre.text().strip()
            department = self.Le_Department_Cre.text().strip()
            no_id = self.Le_No_Id_Cre.text().strip()
            role_group = self.comboBox_Group_Cre.currentText()
            status = self.comboBox_Status_Cre.currentText()
            #Quy định password
            if CheckPasswordMessage(password_hash) is not True:
                QMessageBox.warning(self, "Fail", CheckPasswordMessage(password_hash))
                return
            #SaveUserInfo(user_name, full_name, password_hash, department, no_id, role_group)
            User.update(column="UserName", value=user_name, 
                        updates={"FullName":full_name,"PasswordHash":password_hash,"Department":department,"No_id":no_id,"Role":role_group,"Active":status})
            
            # LoginAudit.insert({"UserID":self.current_user["UserID"], "UserName":self.current_user["UserName"], "EventType":f"Change User {user_name} Crediantials"})
            # AuditTrial.insert({"UserName":self.current_user["UserName"], "Action":"Change User Crediantials"})
            QMessageBox.information(self, "Success", "Success!")
        except Exception as e:
            self.error_signal.emit(str(e))

    def On_DeleteUserInfo(self):
        try:
            if not self.listWidget_User.currentItem():
                QMessageBox.warning(self, "Fail", "Please select a user!")
                return
            user_name = self.listWidget_User.currentItem().text()
            # LoginAudit.insert({"UserID":self.current_user["UserID"], "UserName":self.current_user["UserName"], "EventType":f"Delete User {user_name}"})
            #xoa tren database
            #DeleteUserInfo(self.listWidget_User.currentItem().text())
            User.delete(column="UserName", value=self.listWidget_User.currentItem().text())
            row = self.listWidget_User.currentRow()
            #xoa tren listWidget
            if row >= 0: 
                self.listWidget_User.takeItem(row)
            
            # AuditTrial.insert({"UserName":self.current_user["UserName"], "Action":"Delete User"})
            QMessageBox.information(self, "Success", "Success!")
        except Exception as e:
            self.error_signal.emit(str(e))

    def On_LoadUserInfo(self):
        try:
            #hien thi tren lineedit
            #data = LoadUserInfo(self.listWidget_User.currentItem().text())
            data = User.get_by(column="UserName", value=self.listWidget_User.currentItem().text())
            info = data[0]
            if info:
                self.Le_Full_Name_Cre.setText(info["FullName"])
                self.Le_Department_Cre.setText(info["Department"])
                self.Le_No_Id_Cre.setText(str(info["No_id"]))
                self.comboBox_Group_Cre.setCurrentText(info["Role"])
                self.Le_Password_Cre.setText(info["PasswordHash"])
                self.comboBox_Status_Cre.setCurrentText(info["Active"])
            #print(data)
        except Exception as e:
            self.error_signal.emit(str(e))

    def On_AddUser(self):
        try:
            #Them user
            #kiem tra user ton tai chua
            user_name = self.LE_User_Name.text().strip()
            matches = self.listWidget_User.findItems(user_name, Qt.MatchFixedString)
            if matches:
                QMessageBox.warning(self, "Fail", "User Name already exist! Please try again.")
                return

            full_name = self.LE_Full_Name.text().strip()
            password_hash = self.LE_Password.text().strip()
            department = self.LE_Department.text().strip()
            no_id = self.LE_No_Id.text().strip()
            role_group = self.comboBox_Role_Group.currentText()

            #ko duoc de trong
            if not(user_name and full_name and password_hash and department and no_id):
                QMessageBox.warning(self, "Fail", "Enter User Information!")
                return
            #Quy định password
            if CheckPasswordMessage(password_hash) is not True:
                QMessageBox.warning(self, "Fail", CheckPasswordMessage(password_hash))
                return
            #AddUser(user_name, full_name, password_hash, department, no_id, role_group)        
            User.insert({"UserName":user_name, "FullName":full_name, "PasswordHash":password_hash, "Department":department, "No_id":no_id, "Role":role_group})
            
            #cap nhat sang listwidget
            self.listWidget_User.clear()
            #Load lai user sau khi them moi
            self.user_name = User.get_column("UserName") #LoadUser()
            self.listWidget_User.addItems(self.user_name)

            # LoginAudit.insert({"UserID":self.current_user["UserID"], "UserName":self.current_user["UserName"], "EventType":f"Add New User {user_name}"})
            # AuditTrial.insert({"UserName":self.current_user["UserName"], "Action":"Add New User"})
            QMessageBox.information(self, "Success", "Success!")
        except Exception as e:
            self.error_signal.emit(str(e))

    #Function khac=====================================================================================================================================================
    #Cài bộ lọc sự kiện installEventFilter cho widget
    def install_event_fillter(self):
        try:
            widget_list = [self.Le_Full_Name_Cre,
                           self.Le_Department_Cre,
                           self.Le_No_Id_Cre,
                           self.Le_Password_Cre,
                           self.LE_User_Name,
                           self.LE_Full_Name,
                           self.LE_Password,
                           self.LE_Department,
                           self.LE_No_Id]
            osk = OskEventFilter(self)
            for w in widget_list:
                if w is not None: # comboBox.lineEdit() có thể None nếu không editable
                    w.installEventFilter(osk)
        except Exception as e:
            self.error_signal.emit(str(e))
    
    def closeEvent(self, event):
        try:
            self.closed.emit()
            event.accept()
        except Exception as e:
            self.error_signal.emit(str(e))

    def show_error_message(self, error_message):
        # Hiển thị hộp thoại lỗi với nội dung từ error_message
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(f"An error occurred: {error_message}")
        msg_box.exec()

def OpenAuthentication(parent=None, user=None):
    f = Authentication(user=user)
    f.setWindowFlags(f.windowFlags() | Qt.WindowStaysOnTopHint)
    f.show()
    return f