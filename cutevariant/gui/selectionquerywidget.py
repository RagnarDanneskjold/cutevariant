from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *


from .plugin import QueryPluginWidget
from cutevariant.core import Query
from cutevariant.core import sql
from cutevariant.gui.ficon import FIcon


class SelectionQueryModel(QStandardItemModel):
    def __init__(self):
        super().__init__()
        self.setColumnCount(2)
        self._query = None

    @property
    def query(self):
        return self._query

    @query.setter
    def query(self, query: Query):
        self._query = query
        self.refresh()

    def refresh(self):
        self.clear()
        for record in sql.get_selections(self._query.conn):
            name_item = QStandardItem("{} ({})".format(record["name"],record["count"]))
            name_item.setIcon(FIcon(0xf4f1))
            name_item.setData(record["name"])
            self.appendRow([name_item])

    def save_current_query(self, name):
        self.query.create_selection(name)
        self.refresh()


class SelectionQueryWidget(QueryPluginWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(self.tr("Selections"))
        self.view = QTreeView()
        self.model = SelectionQueryModel()
        self.view.setModel(self.model)
        self.view.header().hide()

        layout = QVBoxLayout()

        layout.addWidget(self.view)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.view.selectionModel().currentRowChanged.connect(self.changed)

    @property
    def query(self):
        """ Method override from AbstractQueryWidget"""

        # if not self.view.selectionModel():
        #     return self.model.query

        #item = self.model.item(self.view.selectionModel().currentIndex().row())

        #print("item text", item.data())

        # _query = self.model.query
        # _query.selection = str(item.data())

        return self.model.query

    @query.setter
    def query(self, query: Query):
        """ Method override from AbstractQueryWidget"""
        self.model.query = query

    def save_current_query(self):

        name, success = QInputDialog.getText(
            self, "type a name for selection", "Selection name:", QLineEdit.Normal
        )

        if success:
            self.model.save_current_query(name)


    def contextMenuEvent(self, event: QContextMenuEvent):
        """
        Overrided
        """

        current_index = self.view.currentIndex()
        item = self.model.itemFromIndex(current_index)

        menu = QMenu()

        menu.addAction(FIcon(0xf8ff),"Edit")
        menu.addSeparator()
        menu.addAction(FIcon(0xf413),"Remove")
        
        menu.exec_(event.globalPos())