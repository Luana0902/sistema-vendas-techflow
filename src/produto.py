from decimal import Decimal, InvalidOperation

from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QMessageBox, QAbstractItemView

from utils.cnn import conectar


class GerenciadorProdutos:
    def __init__(self, tela):
        self.tela = tela

        # Cria o modelo da tabela de produtos
        self.modelo = QStandardItemModel()

        self.modelo.setHorizontalHeaderLabels(
            [
                "Código",
                "Nome",
                "Descrição",
                "Categoria",
                "Preço",
                "Estoque",
            ]
        )

        # Coloca o modelo na tabela da interface
        self.tela.tabela_produtos.setModel(self.modelo)

        # Configura a tabela para selecionar a linha inteira
        self.tela.tabela_produtos.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.tela.tabela_produtos.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        # Conecta os botões às funções
        self.tela.btn_salvar_2.clicked.connect(
            self.salvar_produto
        )

        self.tela.btn_limpar_2.clicked.connect(
            self.limpar_campos
        )

        self.tela.btn_excluir_2.clicked.connect(
            self.excluir_produto
        )

        # Ao dar dois cliques em um produto,
        # carrega seus dados nos campos
        self.tela.tabela_produtos.doubleClicked.connect(
            self.carregar_campos_ao_duplo_clique
        )

        # Carrega os produtos quando abrir a tela
        self.carregar_dados_na_tabela()

    def carregar_dados_na_tabela(self):
        """
        Busca todos os produtos no banco de dados
        e mostra na tabela.
        """

        # Limpa os registros que já estavam na tabela
        self.modelo.removeRows(
            0,
            self.modelo.rowCount()
        )

        conexao = None
        cursor = None

        try:
            conexao = conectar()
            cursor = conexao.cursor()

            sql = """
                SELECT
                    id_codigo,
                    nome,
                    descricao,
                    categoria,
                    preco,
                    estoque
                FROM produtos
                ORDER BY id_codigo
            """

            cursor.execute(sql)

            produtos = cursor.fetchall()

            for produto in produtos:

                preco = ""

                if produto[4] is not None:
                    preco = f"{Decimal(str(produto[4])):.2f}"

                linha = [
                    QStandardItem(
                        str(produto[0] or "")
                    ),
                    QStandardItem(
                        str(produto[1] or "")
                    ),
                    QStandardItem(
                        str(produto[2] or "")
                    ),
                    QStandardItem(
                        str(produto[3] or "")
                    ),
                    QStandardItem(preco),
                    QStandardItem(
                        str(
                            produto[5]
                            if produto[5] is not None
                            else ""
                        )
                    ),
                ]

                self.modelo.appendRow(linha)

            # Ajusta o tamanho das colunas
            self.tela.tabela_produtos.resizeColumnsToContents()

        except Exception as erro:
            QMessageBox.critical(
                self.tela,
                "Erro",
                f"Erro ao carregar os produtos:\n{erro}",
            )

        finally:
            if cursor is not None:
                cursor.close()

            if conexao is not None:
                conexao.close()

    def salvar_produto(self):
        """
        Cadastra um produto novo ou altera
        um produto já cadastrado.
        """

        codigo_texto = (
            self.tela.txt_codigo.text().strip()
        )

        nome = (
            self.tela.txt_nome.text().strip()
        )

        descricao = (
            self.tela.txt_descricao.text().strip()
        )

        categoria = (
            self.tela.cmb_categoria.currentText().strip()
        )

        preco_texto = (
            self.tela.txt_preco.text()
            .strip()
            .replace("R$", "")
            .strip()
        )

        estoque_texto = (
            self.tela.txt_estoque.text().strip()
        )

        # Validação do nome
        if not nome:
            QMessageBox.warning(
                self.tela,
                "Aviso",
                "Preencha o nome do produto.",
            )
            return

        # Validação da descrição
        if not descricao:
            QMessageBox.warning(
                self.tela,
                "Aviso",
                "Preencha a descrição do produto.",
            )
            return

        # Validação da categoria
        if not categoria:
            QMessageBox.warning(
                self.tela,
                "Aviso",
                "Selecione a categoria do produto.",
            )
            return

        # Validação do preço
        if not preco_texto:
            QMessageBox.warning(
                self.tela,
                "Aviso",
                "Preencha o preço do produto.",
            )
            return

        # Validação do estoque
        if not estoque_texto:
            QMessageBox.warning(
                self.tela,
                "Aviso",
                "Preencha o estoque do produto.",
            )
            return

        try:
            # Aceita preço com vírgula ou ponto
            preco = Decimal(
                preco_texto.replace(",", ".")
            )

            if preco < 0:
                raise InvalidOperation

        except (InvalidOperation, ValueError):
            QMessageBox.warning(
                self.tela,
                "Aviso",
                "Digite um preço válido.\n"
                "Exemplo: 199,90",
            )
            return

        try:
            estoque = int(estoque_texto)

            if estoque < 0:
                raise ValueError

        except ValueError:
            QMessageBox.warning(
                self.tela,
                "Aviso",
                "Digite um estoque válido usando "
                "um número inteiro maior ou igual a zero.",
            )
            return

        conexao = None
        cursor = None

        try:
            conexao = conectar()
            cursor = conexao.cursor()

            # Se existe código, altera o produto
            if codigo_texto:

                sql = """
                    UPDATE produtos
                    SET
                        nome = %s,
                        descricao = %s,
                        categoria = %s,
                        preco = %s,
                        estoque = %s
                    WHERE id_codigo = %s
                """

                cursor.execute(
                    sql,
                    (
                        nome,
                        descricao,
                        categoria,
                        preco,
                        estoque,
                        int(codigo_texto),
                    ),
                )

                if cursor.rowcount == 0:
                    mensagem = (
                        "Nenhuma alteração foi realizada."
                    )
                else:
                    mensagem = (
                        "Produto atualizado com sucesso!"
                    )

            # Se não existe código, cadastra produto novo
            else:

                sql = """
                    INSERT INTO produtos
                    (
                        nome,
                        descricao,
                        categoria,
                        preco,
                        estoque
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """

                cursor.execute(
                    sql,
                    (
                        nome,
                        descricao,
                        categoria,
                        preco,
                        estoque,
                    ),
                )

                mensagem = (
                    "Produto cadastrado com sucesso!"
                )

            conexao.commit()

            QMessageBox.information(
                self.tela,
                "Sucesso",
                mensagem,
            )

            self.limpar_campos()
            self.carregar_dados_na_tabela()

        except ValueError:
            QMessageBox.warning(
                self.tela,
                "Aviso",
                "O código do produto é inválido.",
            )

        except Exception as erro:

            if conexao is not None:
                conexao.rollback()

            QMessageBox.critical(
                self.tela,
                "Erro",
                f"Não foi possível salvar o produto:\n{erro}",
            )

        finally:
            if cursor is not None:
                cursor.close()

            if conexao is not None:
                conexao.close()

    def carregar_campos_ao_duplo_clique(self, index):
        """
        Carrega os dados do produto nos campos
        quando o usuário dá dois cliques na tabela.
        """

        linha = index.row()

        def texto_da_coluna(coluna):
            item = self.modelo.item(
                linha,
                coluna
            )

            if item:
                return item.text()

            return ""

        codigo = texto_da_coluna(0)
        nome = texto_da_coluna(1)
        descricao = texto_da_coluna(2)
        categoria = texto_da_coluna(3)
        preco = texto_da_coluna(4)
        estoque = texto_da_coluna(5)

        self.tela.txt_codigo.setText(codigo)
        self.tela.txt_nome.setText(nome)
        self.tela.txt_descricao.setText(descricao)

        # Procura a categoria no ComboBox
        indice_categoria = (
            self.tela.cmb_categoria.findText(categoria)
        )

        if indice_categoria >= 0:
            self.tela.cmb_categoria.setCurrentIndex(
                indice_categoria
            )
        else:
            self.tela.cmb_categoria.setCurrentText(
                categoria
            )

        # Mostra o preço com vírgula
        self.tela.txt_preco.setText(
            preco.replace(".", ",")
        )

        self.tela.txt_estoque.setText(estoque)

    def excluir_produto(self):
        """
        Exclui o produto selecionado da tabela.
        """

        codigo_texto = (
            self.tela.txt_codigo.text().strip()
        )

        # Se os campos estiverem vazios,
        # procura uma linha selecionada na tabela
        if not codigo_texto:

            linhas_selecionadas = (
                self.tela
                .tabela_produtos
                .selectionModel()
                .selectedRows()
            )

            if not linhas_selecionadas:
                QMessageBox.warning(
                    self.tela,
                    "Aviso",
                    "Selecione um produto na tabela.",
                )
                return

            linha = linhas_selecionadas[0].row()

            item_id = self.modelo.item(
                linha,
                0
            )

            if item_id is None:
                QMessageBox.warning(
                    self.tela,
                    "Aviso",
                    "Não foi possível identificar o produto.",
                )
                return

            codigo_texto = item_id.text()

        try:
            id_produto = int(codigo_texto)

        except ValueError:
            QMessageBox.warning(
                self.tela,
                "Aviso",
                "O código do produto é inválido.",
            )
            return

        # Pergunta antes de excluir
        resposta = QMessageBox.question(
            self.tela,
            "Confirmar exclusão",
            (
                "Deseja realmente excluir o produto "
                f"de código {id_produto}?"
            ),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No,
        )

        if resposta != QMessageBox.StandardButton.Yes:
            return

        conexao = None
        cursor = None

        try:
            conexao = conectar()
            cursor = conexao.cursor()

            sql = """
                DELETE FROM produtos
                WHERE id_codigo = %s
            """

            cursor.execute(
                sql,
                (id_produto,),
            )

            conexao.commit()

            if cursor.rowcount == 0:
                QMessageBox.warning(
                    self.tela,
                    "Aviso",
                    "Produto não encontrado no banco.",
                )

            else:
                QMessageBox.information(
                    self.tela,
                    "Sucesso",
                    "Produto excluído com sucesso!",
                )

            self.limpar_campos()
            self.carregar_dados_na_tabela()

        except Exception as erro:

            if conexao is not None:
                conexao.rollback()

            QMessageBox.critical(
                self.tela,
                "Erro",
                f"Não foi possível excluir o produto:\n{erro}",
            )

        finally:
            if cursor is not None:
                cursor.close()

            if conexao is not None:
                conexao.close()

    def limpar_campos(self):
        """
        Limpa os campos do cadastro de produtos.
        """

        self.tela.txt_codigo.clear()
        self.tela.txt_nome.clear()
        self.tela.txt_descricao.clear()
        self.tela.txt_preco.clear()
        self.tela.txt_estoque.clear()

        self.tela.cmb_categoria.setCurrentIndex(0)

        self.tela.tabela_produtos.clearSelection()

        self.tela.txt_nome.setFocus()