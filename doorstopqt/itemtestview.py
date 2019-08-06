from .itemview import ItemView
from .lastupdatedtext import LastUpdatedText
from .variabletables import VariableTables


class ItemTestView(ItemView):
    def __init__(self):
        self.vartables = VariableTables()
        self.lastupdatedtext = LastUpdatedText()
        self.lastupdatedtext.name = 'lastupdated'
        self.tableviews = self.vartables.views
        self.views = [self.vartables, self.lastupdatedtext]
        self.viewssplitted = self.tableviews + [self.lastupdatedtext]
        super().__init__(self.views, self.viewssplitted)

        self.vartables.inputtable.table.cellChanged.connect(self.vieweditor)
        self.vartables.inputtable.table.cellChanged.connect(self.textChanged)

        self.vartables.outputtable.table.cellChanged.connect(self.vieweditor)
        self.vartables.outputtable.table.cellChanged.connect(self.textChanged)
