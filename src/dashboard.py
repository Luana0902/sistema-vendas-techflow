from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import (
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
)
import sys

# Importa o gerenciador do arquivo cliente.py
from src.cliente import GerenciadorClientes 
from src.produto import GerenciadorProdutos
from src.venda import GerenciadorVendas

class TelaDashboard(QtWidgets.QWidget): 

    def __init__(self):
        super().__init__()
       
        uic.loadUi(
            "views/dashboard.ui",
            self
        )
        self.gerenciador_vendas = GerenciadorVendas(self)

        #self.btnProdutos.clicked.connect(self.abrir_produtos)
        # Configuração inicial do menu lateral animado
        self.largura_menu_aberto = 200
        self.largura_menu_fechado = 0

        self.menu_lateral.setMinimumWidth(self.largura_menu_aberto)
        self.menu_lateral.setMaximumWidth(self.largura_menu_aberto)

        self.menu_aberto = True

        # Associa o botão do menu hambúrguer à animação
        self.drop_button.clicked.connect(self.alternar_menu)

        # Define a página inicial ativa (index 1 é a página de Clientes no StackedWidget)
        self.conteudo_principal.setCurrentIndex(0)

        self.button_home.clicked.connect(lambda: self.conteudo_principal.setCurrentIndex(0))
        self.cadastro_cliente.clicked.connect(lambda: self.conteudo_principal.setCurrentIndex(1))
        self.cadastro_produtos.clicked.connect(lambda: self.conteudo_principal.setCurrentIndex(2))    
        self.registro_vendas.clicked.connect(lambda: self.conteudo_principal.setCurrentIndex(3))
    
    
        # --- ATIVA A LÓGICA DE CONTROLE DO CLIENTE ---
        # Passamos 'self' (esta classe) para que o cliente.py consiga ler os componentes da tela
        self.gerenciador_clientes = GerenciadorClientes(self)
        self.gerenciador_produtos = GerenciadorProdutos(self)
        self.gerenciador_vendas = GerenciadorVendas(self)
    def alternar_menu(self):
        """Executa a animação de abrir e fechar o menu esquerdo."""
        anim_min = QPropertyAnimation(self.menu_lateral, b"minimumWidth")
        anim_max = QPropertyAnimation(self.menu_lateral, b"maximumWidth")

        for anim in (anim_min, anim_max):
            anim.setDuration(300)
            anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        if self.menu_aberto:
            anim_min.setStartValue(self.largura_menu_aberto)
            anim_min.setEndValue(self.largura_menu_fechado)
            anim_max.setStartValue(self.largura_menu_aberto)
            anim_max.setEndValue(self.largura_menu_fechado)
        else:
            anim_min.setStartValue(self.largura_menu_fechado)
            anim_min.setEndValue(self.largura_menu_aberto)
            anim_max.setStartValue(self.largura_menu_fechado)
            anim_max.setEndValue(self.largura_menu_aberto)

        self.menu_aberto = not self.menu_aberto

        self.animacao = QParallelAnimationGroup()
        self.animacao.addAnimation(anim_min)
        self.animacao.addAnimation(anim_max)
        self.animacao.start()




if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    janela = TelaDashboard()
    janela.show()
    sys.exit(app.exec())

    