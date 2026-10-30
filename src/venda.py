from decimal import Decimal, InvalidOperation

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QAbstractItemView, QTableWidgetItem

from utils.cnn import conectar


class GerenciadorVendas:
    """Controla o CRUD de vendas da página de vendas do dashboard."""

    def __init__(self, tela):
        self.tela = tela
        self.id_venda_em_edicao = None

        self.configurar_tabela()
        self.configurar_quantidade()

        self.tela.btn_registrar_venda.clicked.connect(self.salvar_venda)
        self.tela.btn_limpar_5.clicked.connect(self.limpar_campos)
        self.tela.btn_cancelar.clicked.connect(self.excluir_venda)
        self.tela.combo_produto.currentIndexChanged.connect(self.atualizar_valor_total)
        self.tela.spin_quantidade.currentTextChanged.connect(self.atualizar_valor_total)
        self.tela.tableWidget.itemDoubleClicked.connect(self.carregar_venda_para_edicao)

        self.carregar_clientes()
        self.carregar_produtos()
        self.carregar_vendas()

    def configurar_tabela(self):
        tabela = self.tela.tableWidget
        tabela.setColumnCount(6)
        tabela.setHorizontalHeaderLabels([
            "Data/Hora", "Cliente", "Produto", "Quantidade",
            "Valor Unitário", "Valor Total"
        ])
        tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabela.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def configurar_quantidade(self):
        # Na interface, spin_quantidade é um QComboBox editável.
        self.tela.spin_quantidade.clear()
        self.tela.spin_quantidade.addItems([str(numero) for numero in range(1, 101)])
        self.tela.spin_quantidade.setCurrentText("1")

    def carregar_clientes(self):
        conexao = None
        cursor = None
        try:
            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute("SELECT id_clientes, nome FROM clientes ORDER BY nome")
            clientes = cursor.fetchall()

            self.tela.combo_cliente.blockSignals(True)
            self.tela.combo_cliente.clear()
            self.tela.combo_cliente.addItem("Selecione um cliente...", None)
            for id_cliente, nome in clientes:
                self.tela.combo_cliente.addItem(str(nome), int(id_cliente))
            self.tela.combo_cliente.setCurrentIndex(0)
            self.tela.combo_cliente.blockSignals(False)
        except Exception as erro:
            QMessageBox.critical(self.tela, "Erro", f"Erro ao carregar clientes:\n{erro}")
        finally:
            if cursor is not None:
                cursor.close()
            if conexao is not None:
                conexao.close()

    def carregar_produtos(self):
        conexao = None
        cursor = None
        try:
            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute(
                "SELECT id_codigo, nome, preco, estoque "
                "FROM produtos ORDER BY nome"
            )
            produtos = cursor.fetchall()

            self.tela.combo_produto.blockSignals(True)
            self.tela.combo_produto.clear()
            self.tela.combo_produto.addItem("Selecione um produto...", None)
            for id_produto, nome, preco, estoque in produtos:
                dados = {
                    "id": int(id_produto),
                    "preco": Decimal(str(preco or 0)),
                    "estoque": int(estoque or 0),
                }
                texto = f"{nome} (Estoque: {dados['estoque']})"
                self.tela.combo_produto.addItem(texto, dados)
            self.tela.combo_produto.setCurrentIndex(0)
            self.tela.combo_produto.blockSignals(False)
            self.atualizar_valor_total()
        except Exception as erro:
            QMessageBox.critical(self.tela, "Erro", f"Erro ao carregar produtos:\n{erro}")
        finally:
            if cursor is not None:
                cursor.close()
            if conexao is not None:
                conexao.close()

    def obter_quantidade(self):
        texto = self.tela.spin_quantidade.currentText().strip()
        try:
            quantidade = int(texto)
            if quantidade <= 0:
                raise ValueError
            return quantidade
        except ValueError:
            return None

    def atualizar_valor_total(self):
        dados_produto = self.tela.combo_produto.currentData()
        quantidade = self.obter_quantidade()
        if not dados_produto or quantidade is None:
            total = Decimal("0.00")
        else:
            total = dados_produto["preco"] * quantidade
        self.tela.lbl_valor_total.setText(self.formatar_moeda(total))

    @staticmethod
    def formatar_moeda(valor):
        valor = Decimal(str(valor or 0))
        texto = f"{valor:,.2f}"
        texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {texto}"

    def salvar_venda(self):
        id_cliente = self.tela.combo_cliente.currentData()
        dados_produto = self.tela.combo_produto.currentData()
        quantidade = self.obter_quantidade()

        if id_cliente is None:
            QMessageBox.warning(self.tela, "Aviso", "Selecione um cliente.")
            return
        if not dados_produto:
            QMessageBox.warning(self.tela, "Aviso", "Selecione um produto.")
            return
        if quantidade is None:
            QMessageBox.warning(self.tela, "Aviso", "Digite uma quantidade inteira maior que zero.")
            return

        id_produto = dados_produto["id"]
        valor_unitario = dados_produto["preco"]
        valor_total = valor_unitario * quantidade

        conexao = None
        cursor = None
        try:
            conexao = conectar()
            cursor = conexao.cursor()

            # Bloqueia o produto durante a operação e confere o estoque real.
            cursor.execute(
                "SELECT preco, estoque FROM produtos WHERE id_codigo = %s FOR UPDATE",
                (id_produto,),
            )
            produto_banco = cursor.fetchone()
            if produto_banco is None:
                raise ValueError("Produto não encontrado no banco.")

            valor_unitario = Decimal(str(produto_banco[0] or 0))
            estoque_atual = int(produto_banco[1] or 0)
            valor_total = valor_unitario * quantidade

            if self.id_venda_em_edicao is None:
                if quantidade > estoque_atual:
                    raise ValueError(f"Estoque insuficiente. Disponível: {estoque_atual}.")

                cursor.execute(
                    """
                    INSERT INTO vendas
                        (id_cliente, id_produto, quantidade, valor_unitario, valor_total)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (id_cliente, id_produto, quantidade, valor_unitario, valor_total),
                )
                cursor.execute(
                    "UPDATE produtos SET estoque = estoque - %s WHERE id_codigo = %s",
                    (quantidade, id_produto),
                )
                mensagem = "Venda registrada com sucesso!"
            else:
                cursor.execute(
                    "SELECT id_produto, quantidade FROM vendas "
                    "WHERE id_venda = %s FOR UPDATE",
                    (self.id_venda_em_edicao,),
                )
                venda_antiga = cursor.fetchone()
                if venda_antiga is None:
                    raise ValueError("Venda não encontrada no banco.")

                produto_antigo = int(venda_antiga[0])
                quantidade_antiga = int(venda_antiga[1])

                # Devolve ao estoque a quantidade da venda antiga.
                cursor.execute(
                    "UPDATE produtos SET estoque = estoque + %s WHERE id_codigo = %s",
                    (quantidade_antiga, produto_antigo),
                )

                # Busca novamente o estoque, pois pode ser o mesmo produto.
                cursor.execute(
                    "SELECT estoque FROM produtos WHERE id_codigo = %s FOR UPDATE",
                    (id_produto,),
                )
                estoque_disponivel = int(cursor.fetchone()[0] or 0)
                if quantidade > estoque_disponivel:
                    raise ValueError(f"Estoque insuficiente. Disponível: {estoque_disponivel}.")

                cursor.execute(
                    """
                    UPDATE vendas
                    SET id_cliente = %s, id_produto = %s, quantidade = %s,
                        valor_unitario = %s, valor_total = %s
                    WHERE id_venda = %s
                    """,
                    (
                        id_cliente, id_produto, quantidade, valor_unitario,
                        valor_total, self.id_venda_em_edicao,
                    ),
                )
                cursor.execute(
                    "UPDATE produtos SET estoque = estoque - %s WHERE id_codigo = %s",
                    (quantidade, id_produto),
                )
                mensagem = "Venda atualizada com sucesso!"

            conexao.commit()
            QMessageBox.information(self.tela, "Sucesso", mensagem)
            self.limpar_campos()
            self.carregar_produtos()
            self.carregar_vendas()
        except (ValueError, InvalidOperation) as erro:
            if conexao is not None:
                conexao.rollback()
            QMessageBox.warning(self.tela, "Aviso", str(erro))
        except Exception as erro:
            if conexao is not None:
                conexao.rollback()
            QMessageBox.critical(self.tela, "Erro", f"Não foi possível salvar a venda:\n{erro}")
        finally:
            if cursor is not None:
                cursor.close()
            if conexao is not None:
                conexao.close()

    def carregar_vendas(self):
        conexao = None
        cursor = None
        try:
            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute(
                """
                SELECT v.id_venda, v.data_venda, c.nome, p.nome,
                       v.quantidade, v.valor_unitario, v.valor_total,
                       v.id_cliente, v.id_produto
                FROM vendas v
                INNER JOIN clientes c ON c.id_clientes = v.id_cliente
                INNER JOIN produtos p ON p.id_codigo = v.id_produto
                ORDER BY v.id_venda DESC
                """
            )
            vendas = cursor.fetchall()

            tabela = self.tela.tableWidget
            tabela.setRowCount(0)
            total_vendas = Decimal("0.00")
            total_itens = 0

            for venda in vendas:
                linha = tabela.rowCount()
                tabela.insertRow(linha)
                data = venda[1].strftime("%d/%m/%Y %H:%M") if hasattr(venda[1], "strftime") else str(venda[1])
                valores = [
                    data,
                    str(venda[2]),
                    str(venda[3]),
                    str(venda[4]),
                    self.formatar_moeda(venda[5]),
                    self.formatar_moeda(venda[6]),
                ]
                for coluna, valor in enumerate(valores):
                    item = QTableWidgetItem(valor)
                    if coluna == 0:
                        item.setData(Qt.ItemDataRole.UserRole, int(venda[0]))
                        item.setData(Qt.ItemDataRole.UserRole + 1, int(venda[7]))
                        item.setData(Qt.ItemDataRole.UserRole + 2, int(venda[8]))
                    tabela.setItem(linha, coluna, item)
                total_itens += int(venda[4])
                total_vendas += Decimal(str(venda[6] or 0))

            tabela.resizeColumnsToContents()
            self.tela.lbl_total_vendas.setText(
                f"📊 Total de Vendas: {self.formatar_moeda(total_vendas)}"
            )
            # A interface enviada não possui lbl_total_itens na página visível.
            if hasattr(self.tela, "lbl_total_itens"):
                self.tela.lbl_total_itens.setText(
                    f"🛒 Total de Itens Vendidos: {total_itens}"
                )
        except Exception as erro:
            QMessageBox.critical(self.tela, "Erro", f"Erro ao carregar vendas:\n{erro}")
        finally:
            if cursor is not None:
                cursor.close()
            if conexao is not None:
                conexao.close()

    def carregar_venda_para_edicao(self, item):
        linha = item.row()
        item_data = self.tela.tableWidget.item(linha, 0)
        if item_data is None:
            return

        self.id_venda_em_edicao = item_data.data(Qt.ItemDataRole.UserRole)
        id_cliente = item_data.data(Qt.ItemDataRole.UserRole + 1)
        id_produto = item_data.data(Qt.ItemDataRole.UserRole + 2)
        quantidade = self.tela.tableWidget.item(linha, 3).text()

        indice_cliente = self.tela.combo_cliente.findData(id_cliente)
        if indice_cliente >= 0:
            self.tela.combo_cliente.setCurrentIndex(indice_cliente)

        indice_produto = -1
        for indice in range(self.tela.combo_produto.count()):
            dados = self.tela.combo_produto.itemData(indice)
            if dados and dados.get("id") == id_produto:
                indice_produto = indice
                break
        if indice_produto >= 0:
            self.tela.combo_produto.setCurrentIndex(indice_produto)

        self.tela.spin_quantidade.setCurrentText(quantidade)
        self.tela.btn_registrar_venda.setText("💾 Atualizar Venda")
        self.atualizar_valor_total()

    def excluir_venda(self):
        linhas = self.tela.tableWidget.selectionModel().selectedRows()
        if not linhas:
            QMessageBox.warning(
                self.tela, "Aviso",
                "Selecione uma venda no histórico para cancelar/excluir."
            )
            return

        linha = linhas[0].row()
        item_data = self.tela.tableWidget.item(linha, 0)
        id_venda = item_data.data(Qt.ItemDataRole.UserRole) if item_data else None
        if id_venda is None:
            QMessageBox.warning(self.tela, "Aviso", "Não foi possível identificar a venda.")
            return

        resposta = QMessageBox.question(
            self.tela,
            "Confirmar cancelamento",
            f"Deseja cancelar/excluir a venda de código {id_venda}?\n"
            "A quantidade será devolvida ao estoque.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resposta != QMessageBox.StandardButton.Yes:
            return

        conexao = None
        cursor = None
        try:
            conexao = conectar()
            cursor = conexao.cursor()
            cursor.execute(
                "SELECT id_produto, quantidade FROM vendas "
                "WHERE id_venda = %s FOR UPDATE",
                (id_venda,),
            )
            venda = cursor.fetchone()
            if venda is None:
                raise ValueError("Venda não encontrada no banco.")

            cursor.execute(
                "UPDATE produtos SET estoque = estoque + %s WHERE id_codigo = %s",
                (int(venda[1]), int(venda[0])),
            )
            cursor.execute("DELETE FROM vendas WHERE id_venda = %s", (id_venda,))
            conexao.commit()

            QMessageBox.information(self.tela, "Sucesso", "Venda cancelada com sucesso!")
            self.limpar_campos()
            self.carregar_produtos()
            self.carregar_vendas()
        except ValueError as erro:
            if conexao is not None:
                conexao.rollback()
            QMessageBox.warning(self.tela, "Aviso", str(erro))
        except Exception as erro:
            if conexao is not None:
                conexao.rollback()
            QMessageBox.critical(self.tela, "Erro", f"Não foi possível excluir a venda:\n{erro}")
        finally:
            if cursor is not None:
                cursor.close()
            if conexao is not None:
                conexao.close()

    def limpar_campos(self):
        self.id_venda_em_edicao = None
        self.tela.combo_cliente.setCurrentIndex(0)
        self.tela.combo_produto.setCurrentIndex(0)
        self.tela.spin_quantidade.setCurrentText("1")
        self.tela.tableWidget.clearSelection()
        self.tela.btn_registrar_venda.setText("🛒 Registrar Venda")
        self.atualizar_valor_total()
