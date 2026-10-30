import sys
import json
from pathlib import Path
from PyQt6 import QtWidgets, uic
# Importa a tela do dashboard que criamos
from src.dashboard import TelaDashboard
#import pymysql
import bcrypt


from utils.cnn import conectar


class TelaLogin(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        
        uic.loadUi("views/login.ui", self)
        
        self.btn_entrar.clicked.connect(self.verificar_login)

    def verificar_login(self):
        usuario_digitado = self.txt_usuario.text()
        senha_digitada = self.txt_senha.text()

        usuario_digitado = self.txt_usuario.text()
        senha_digitada = self.txt_senha.text()

        try:
            conexao = conectar()
            cursor = conexao.cursor()

            cursor.execute(
                """
                SELECT nome, senha
                FROM usuarios
                WHERE login = %s
                """,
                (usuario_digitado,)
            )

            resultado = cursor.fetchone()

            cursor.close()
            conexao.close()

            if resultado:

                nome_usuario = resultado[0]
                senha_hash = resultado[1]

                if bcrypt.checkpw(
                    senha_digitada.encode("utf-8"),
                    senha_hash.encode("utf-8")
                ):

                    self.nova_tela = TelaDashboard()
                    self.nova_tela.show()
                    self.close()

                else:

                    QtWidgets.QMessageBox.warning(
                        self,
                        "Erro",
                        "Usuario ou senha incorretos."
                    )

            else:

                QtWidgets.QMessageBox.warning(
                    self,
                    "Erro",
                    "Usuario não encontrado."
                )

        except Exception as erro:

            QtWidgets.QMessageBox.critical(
                self,
                "Erro",
                str(erro)
            )
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    janela = TelaLogin()
    janela.show()
    sys.exit(app.exec())