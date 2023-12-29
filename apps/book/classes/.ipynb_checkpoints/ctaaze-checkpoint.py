from apps.book.classes.abookbase import BOOKBASE


###################################################


class TAAZE(BOOKBASE):
    '''讀冊'''
    info_default = {
        "bookid": "",
    }

    def update_info(self):
        pass
