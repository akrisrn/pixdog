__author__ = 'akr'

from os import makedirs, listdir
from os.path import exists, join
from re import search

from pdlib.getdata import GetData


class GetTagPage(GetData):
    def __init__(self):
        super().__init__()
        self.konachan = 'konachan'
        self.tagPageUrl = 'http://konachan.com/post?page=%d&tags=%s'

    def _get_tag_page(self):
        self.tag = input('Please input the tag name: ')
        self.tagDirName = join(self.imgStoreDirName, self.konachan, self.tag)
        if not exists(self.tagDirName):
            makedirs(self.tagDirName)
        self.existedImg = ','.join(listdir(self.tagDirName))

        page_num = 1
        while True:
            print('Load tag page %d...' % page_num)
            tag_page = self.get_page_data(self.tagPageUrl % (page_num, self.tag))
            if search('Nobody here but us chickens!', tag_page):
                print('Nobody here but us chickens.')
                break
            yield tag_page
            page_num += 1
