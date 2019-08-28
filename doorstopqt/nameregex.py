import re


class Nameregex():
    def __init__(self):
        pass

    def gettitle(self, text):
        try:
            search = re.findall("\\*\\*(.+?)\\*\\*", text)
            search2 = re.findall("(.+?)\n", text)
        except AttributeError:
            return
        if not search:
            return
        start = self.setasterisks(search[0])
        end = search2[0]
        title = end.replace(start, '')
        return title.strip()

    def setasterisks(self, text):
        return "{}{}{}".format('**', text, '**')
