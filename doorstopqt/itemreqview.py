from .itemview import ItemView
from .lastupdatedtext import LastUpdatedText
from .decisiontakersview import DecisiontakersView
from .extratextview import ExtratextView

class ItemReqView(ItemView):
    def __init__(self):
        self.decisionlog = ExtratextView('Decision log')
        self.decisiontakers = DecisiontakersView('Decision takers')
        self.lastupdatedtext = LastUpdatedText()
        self.decisionlog.weight = 10
        self.decisionlog.name = 'decisionlog'
        self.decisiontakers.name = 'decisiontakers'
        self.lastupdatedtext.name = 'lastupdated'
        self.views = [self.decisionlog, self.decisiontakers, self.lastupdatedtext]
        super().__init__(self.views)

        self.decisionlog.textview.selectionChanged.connect(self.vieweditor)
        self.decisionlog.textview.textChanged.connect(self.textChanged)
        self.decisiontakers.textview.textChanged.connect(self.textChanged)
        self.decisiontakers.textview.selectionChanged.connect(self.vieweditor)

