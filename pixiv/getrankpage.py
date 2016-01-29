from os import makedirs
from os.path import exists, join
from urllib.parse import urlencode

from pixiv.loadpage import LoadPage


class GetRankPage(LoadPage):
    def __init__(self):
        super().__init__()
        self.rankUrl = 'http://www.pixiv.net/ranking.php?'

    def _get_rank_work_page(self, mode):
        if mode.find('ugoira') != -1:
            mode_split = mode.split('_')
            if len(mode_split) == 3:
                get_value = {'mode': '_'.join(mode_split[1:3]),
                             'content': mode_split[0]
                             }
            else:
                get_value = {'mode': mode_split[1],
                             'content': mode_split[0]
                             }
        else:
            get_value = {'mode': mode}
        self.rankDirName = join(self.imgStoreDirName, self.pixiv, mode)
        if not exists(self.rankDirName):
            makedirs(self.rankDirName)
        for i in range(1, 11):
            get_value['p'] = i
            get_data = urlencode(get_value)
            work_url = self.rankUrl + get_data
            print('Load the page ranked %d to %d ...' % (50 * (i - 1) + 1, 50 * i))
            work_page = self.url_open(work_url)
            yield work_page
