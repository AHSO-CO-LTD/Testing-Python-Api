from PyQt5 import QtWidgets

from Main_Screen import MainScreen
from Login_Screen import LoginScreen
from Global import signal

class StackedWidget(QtWidgets.QStackedWidget):
    def __init__(self):
        super().__init__()
        self.login_screen = LoginScreen()
        self.main_screen = MainScreen() 
        self.addWidget(self.login_screen)  # index 0
        self.addWidget(self.main_screen)  # index 1
        self.set_event()

    def set_event(self):
        signal.switch_screen.connect(self.switch_screen)

    def switch_screen(self, index):
        self.setCurrentIndex(index)