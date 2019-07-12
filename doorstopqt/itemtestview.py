from .itemview import ItemView
from .lastupdatedtext import LastUpdatedText

class ItemTestView(ItemView):
    def __init__(self):
        self.lastupdatedtext = LastUpdatedText()
        self.lastupdatedtext.name = 'lastupdated'
        self.views = [self.lastupdatedtext]
        super().__init__(self.views)
