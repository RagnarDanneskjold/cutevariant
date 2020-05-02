from cutevariant.gui import plugin, FIcon
from cutevariant.core import sql
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *


class FieldsModel(QStandardItemModel):
    """Model to store all fields available for variants, annotations and samples"""

    def __init__(self, conn=None):
        super().__init__()
        self.checkable_items = []
        self.conn = conn

        
    def columnCount(self, index = QModelIndex()):
        return 2

    def headerData(self, section,orientation, role):
        
        if role != Qt.DisplayRole:
            return None 

        if orientation == Qt.Horizontal:
            if section == 0:
                return "Name"
        
        return None


    @property
    def fields(self):
        """Return checked columns
        
        Returns:
            list -- list of columns
        """
        selected_fields= []
        for item in self.checkable_items:
            if item.checkState() == Qt.Checked:
                selected_fields.append(item.data()["name"])
        return selected_fields

    @fields.setter
    def fields(self, columns):
        """Check items which name is in columns
        
        Arguments:
            columns {list} -- list of columns
        """
        self.blockSignals(True)
        for item in self.checkable_items:
            item.setCheckState(Qt.Unchecked)
            if item.data()["name"] in self.fields:
                item.setCheckState(Qt.Checked)
        self.blockSignals(False)

    def load(self):
        """Load all columns avaible into the model 
        """
        self.clear()
        self.checkable_items.clear()

        self.appendRow(self.load_fields("variants"))
        self.appendRow(self.load_fields("annotations"))

        samples_items = QStandardItem("samples")
        samples_items.setIcon(FIcon(0xf00e))
        font = QFont()
        
        samples_items.setFont(font)

        for sample in sql.get_samples(self.conn):
            sample_item = self.load_fields("samples", parent_name = sample["name"])
            sample_item.setText(sample["name"])
            samples_items.appendRow(sample_item)



        self.appendRow(samples_items)



    def load_fields(self, category, parent_name = None):
        root_item = QStandardItem(category)
        root_item.setColumnCount(2)
        root_item.setIcon(FIcon(0Xf24b))
        font = QFont()
        root_item.setFont(font)

        for field in sql.get_field_by_category(self.conn,category):
            item1 = QStandardItem(field["name"])
            item2 = QStandardItem(field["description"])
            item2.setToolTip(field["description"])
            item1.setToolTip(field["description"])
            item1.setCheckable(True)
            root_item.appendRow([item1, item2])
            self.checkable_items.append(item1)
            
            if category == "samples":
                item1.setData({"name": ("sample", parent_name, field["name"])})
            else:
                item1.setData(field)
        
        return root_item




class FieldsEditorWidget(plugin.PluginWidget):
    """Display all fields according categorie

    Usage: 

     view = FieldsWidget
     (conn)
     view.columns = ["chr","pos"]
    
    """

    ENABLE = True


    def __init__(self, parent=None):
        super().__init__()

        self.setWindowTitle(self.tr("Columns"))
        self.view = QTreeView()
        self.toolbar = QToolBar()
        self.model = FieldsModel(None)
        self.proxy_model = QSortFilterProxyModel()

        # setup proxy ( for search option )
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setRecursiveFilteringEnabled(True)

        self.view.setModel(self.proxy_model)
        self.view.setIconSize(QSize(16,16))
        self.view.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.search_edit = QLineEdit()
        # self.view.setIndentation(0)
        self.view.header().setVisible(False)
        layout = QVBoxLayout()


        layout.addWidget(self.search_edit)
        layout.addWidget(self.view)
        layout.addWidget(self.toolbar)

        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.model.itemChanged.connect(self.on_fields_changed)

        # Setup toolbar 
        self.toolbar.setIconSize(QSize(16,16))
        self.toolbar.addAction(FIcon(0XF615), self.tr("collapse"), self.view.collapseAll)
        self.toolbar.addAction(FIcon(0XF616), self.tr("Expand"), self.view.expandAll)

        # setup search edit 
        search_act = self.toolbar.addAction(FIcon(0XF349), self.tr("Search ..."))
        search_act.setCheckable(True)
        search_act.toggled.connect(self.__on_search_pressed)
        self.search_edit.setVisible(False)
        self.search_edit.setPlaceholderText(self.tr("Search by keywords ... "))

        self.search_edit.textChanged.connect(self.proxy_model.setFilterRegExp)

    def __on_search_pressed(self, checked : bool):
        self.search_edit.setVisible(checked)
        self.search_edit.setFocus(Qt.MenuBarFocusReason)




    def on_register(self, mainwindow):
        """ Overrided from PluginWidget"""
        pass 

    def on_open_project(self,conn):
        """ Overrided from PluginWidget """
        self.conn = conn

    # def on_query_model_changed(self, model):
    #     """ Overrided from PluginWidget """
    #     self.columns = model.columns
    #     # When you set columns, it means you check columns. 
    #     # This will trigger a signal itemChanged which cause an infinite loop
    #     # That's why I blocked the signal from the model. So I need to update the view manually
    #     self.view.update()
    #     self.view.resizeColumnToContents(0)

        

    def on_fields_changed(self):


        if self.mainwindow is None:
            return


        if "variant_view" in self.mainwindow.plugins:
            plugin = self.mainwindow.get_plugin("variant_view")
            plugin.fields = self.fields
            plugin.load()

    @property
    def conn(self):
        return self.model.conn

    @conn.setter
    def conn(self, conn):
        self.model.conn = conn
        if conn:
            self.model.load()

    @property
    def fields(self):
        return self.model.fields

    @fields.setter
    def fields(self, fields):
        self.model.fields = fields

    def load(self):
        self.model.load()


    def test(self):
        print(self.fields)

if __name__ == "__main__":
    import sys 
    import sqlite3
    from cutevariant.core.importer import import_reader
    from cutevariant.core.reader import FakeReader

    app = QApplication(sys.argv)

    conn = sql.get_sql_connexion(":memory:")
    import_reader(conn, FakeReader())
    #import_file(conn, "examples/test.snpeff.vcf")


    view = FieldsEditorWidget()

    view.conn = conn
    view.fields = ["chr", "pos"]

    #view.changed.connect(lambda : print(view.columns))


    view.show()

    app.exec_()

