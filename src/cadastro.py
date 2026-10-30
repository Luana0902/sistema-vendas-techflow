from PyQt6 import QtWidgets, uic
from src.dashboard import TelaDashboard
from utils.cnn import conectar
import bcrypt


class TelaCadastro(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        uic.loadUi(
            "views/cadastro.ui", 
            self
        )
        self.btnCadastrar.clicked.connect(
            self.cadastrar
        )  


    def cadastrar(self):

        nome = self.txtNome.text()
        login = self.txtLogin.text()
        senha = self.txtSenha.text()
        conf_senha = self.txtConfsenha.text()

        if senha != conf_senha:

            QtWidgets.QMessageBox.warning(
                self,
                "Erro",
                "As senhas não conferem."
            )

            return

        try:

            conexao = conectar()

            cursor = conexao.cursor()

            senha_hash = bcrypt.hashpw(
                senha.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')

            sql = """
                INSERT INTO usuarios
                (nome, login, senha)
                VALUES (%s, %s, %s)
            """

            valores = (
                nome,
                login,
                senha_hash
            )

            cursor.execute(sql, valores)

            conexao.commit()

            QtWidgets.QMessageBox.information(
                self,
                "Sucesso",
                "Usuário cadastrado!"
            )

            self.dashboard = TelaDashboard()
            self.dashboard.show()

            self.close()

        except Exception as erro:

            QtWidgets.QMessageBox.critical(
                self,
                "Erro",
                str(erro)
            )

    def cadastrar_usuario(self):

        nome = self.txtNome.text().strip()
        login = self.txtLogin.text().strip()
        senha = self.txtSenha.text()
        confsenha = self.txtConfsenha.text()

        if not nome or not login or not senha:

            QtWidgets.QMessageBox.warning(
                self,
                "Erro",
                "Preencha todos os campos."
            )
            return

        if senha != confsenha:

            QtWidgets.QMessageBox.warning(
                self,
                "Erro",
                "As senhas não conferem."
            )
            return

        try:

            conexao = conectar()
            cursor = conexao.cursor()

            cursor.execute(
                "SELECT id FROM usuarios WHERE login=%s",
                (login,)
            )

            if cursor.fetchone():

                QtWidgets.QMessageBox.warning(
                    self,
                    "Aviso",
                    "login já cadastrado."
                )

                return

            senha_hash = bcrypt.hashpw(
                senha.encode('utf-8'),
                bcrypt.gensalt()
            )

            sql = """
                INSERT INTO usuarios
                (
                    nome,
                    login,
                    senha
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
            """

            valores = (
                nome,
                login,
                senha_hash.decode('utf-8')
            )

            cursor.execute(sql, valores)
            conexao.commit()

            QtWidgets.QMessageBox.information(
                self,
                "Sucesso",
                "Cadastro realizado!"
            )

            self.limpar_campos()

        except Exception as erro:

            QtWidgets.QMessageBox.critical(
                self,
                "Erro",
                str(erro)
            )

        finally:

            if 'cursor' in locals():
                cursor.close()

            if 'conexao' in locals():
                conexao.close()

    def limpar_campos(self):

        self.txtNome.clear()
        self.txtLogin.clear()
        self.txtSenha.clear()
        self.txtConfsenha.clear()