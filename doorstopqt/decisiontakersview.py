from .extratextview import ExtratextView


class DecisiontakersView(ExtratextView):
    def __init__(self, name):
        super().__init__(name)
        self.text = self.getdecisiontakerslist

    def settextlist(self, decisiontakers):
        if type(decisiontakers) is list:
            decisiontakers = ', '.join(decisiontakers)
        self.setText(decisiontakers)

    def getdecisiontakerslist(self):
        decisiontakers = self.document().toPlainText()
        decisiontakerstrimmed = decisiontakers.split(',')
        decisiontakerslist = []
        for name in decisiontakerstrimmed:
            if name != '' and name[0].isspace():
                name = name[1:]
            decisiontakerslist.append(name)
        return decisiontakerslist