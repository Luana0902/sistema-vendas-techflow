from PyQt6 import QtWidgets, uic

from src.cadastro import TelaCadastro
from src.dashboard import TelaDashboard


class TelaLogin(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        uic.loadUi("views/login.ui", self)

   
        self.btn_entrar.clicked.connect(self.verificar_login)
        self.btnCriarconta.clicked.connect(self.criar_conta)
        
    def criar_conta(self):

        self.cadastro = TelaCadastro()
        self.cadastro.show()

        self.close()

    def verificar_login(self):

        self.dashboard = TelaDashboard()
        self.dashboard.label_usuario.setText("Leticia")
        self.dashboard.show()

        self.close()
    def criar_conta(self):

        self.cadastro = TelaCadastro()
        self.cadastro.show()

        self.close()

    def logar(self):

        # depois será feita a validação no banco

        self.dashboard = TelaDashboard()
        self.dashboard.show()

        self.close()