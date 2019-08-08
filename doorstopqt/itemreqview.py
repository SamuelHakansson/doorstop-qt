from .itemview import ItemView
from .lastupdatedtext import LastUpdatedText
from.decisionview import DecisionView


class ItemReqView(ItemView):
    def __init__(self):

        self.lastupdatedtext = LastUpdatedText()
        self.lastupdatedtext.name = 'lastupdated'
        self.decisionview = DecisionView()
        self.views = [self.decisionview, self.lastupdatedtext]
        self.viewssplitted = self.decisionview.views + [self.lastupdatedtext]
        super().__init__(self.views, self.viewssplitted)

        self.decisionview.decisionlog.textview.selectionChanged.connect(self.vieweditor)
        self.decisionview.decisionlog.textview.textChanged.connect(self.textChanged)
        #self.decisionview.decisiontakers.listview.dataChanged.connect(self.textChanged)
        #self.decisionview.decisiontakers.listview.selectionChanged.connect(self.vieweditor)

