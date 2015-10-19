__author__ = 'akr'

from re import search, compile
from os import makedirs
from os.path import exists, join
from math import ceil
from urllib.parse import urlencode

from pixiv.loadpage import LoadPage


class GetUserPage(LoadPage):
    def __init__(self):
        super().__init__()
        self.memIllUrl = 'http://www.pixiv.net/member_illust.php?'

    def _get_user_work_page(self):
        self.userId = input('Enter User id: ')
        self.userDirName = join(self.imgStoreDirName, self.pixiv, self.userId)

        if self.userId.isdigit():
            if not exists(self.userDirName):
                makedirs(self.userDirName)
        else:
            print('Wrong id.')
            raise SystemExit(1)

        get_value = {'id': self.userId,
                     'type': 'all',
                     'p': 1
                     }
        get_data = urlencode(get_value)
        work_url = self.memIllUrl + get_data

        print('Load the first page of work directory...')
        work_page = self.url_open(work_url)

        pattern = compile('class="count-badge">(.*?)</span>')
        count_num = search(pattern, work_page)

        count_num = int(count_num.group(1)[:-1])
        total_page = ceil(count_num / 20)
        print('Total number of pages: %d' % total_page)

        yield work_page

        for i in range(2, total_page + 1):
            get_value['p'] = i
            get_data = urlencode(get_value)
            work_url = self.memIllUrl + get_data

            print('Load a new page of work directory...(%d / %d)' % (i, total_page))
            work_page = self.url_open(work_url)
            yield work_page
