__author__ = 'akr'

from os import listdir

from pixiv.getuserpage import GetUserPage
from pixiv.getrankpage import GetRankPage


class SwitchPage(GetUserPage, GetRankPage):
    def __init__(self):
        GetUserPage.__init__(self)
        GetRankPage.__init__(self)

    def _switch_work_page(self):
        print('Please choose a model:')
        print('0.To get the image according to the user ID')
        print('1.To get the image according to the rank')
        option = input('Input 0 or 1: ')

        if option == '0':
            for work_page in self._get_user_work_page():
                self.dirName = self.userDirName
                self.existedImg = ','.join(listdir(self.dirName))
                yield work_page
        elif option == '1':
            choose = input('Please choose daily/weekly/monthly/rookie/original/male/female/'
                           'daily_r18/weekly_r18/male_r18/female_r18: ')

            if choose not in ['daily', 'weekly', 'monthly', 'rookie', 'original', 'male', 'female',
                              'daily_r18', 'weekly_r18', 'male_r18', 'female_r18']:
                print('Wrong input.')
                raise SystemExit(1)

            for work_page in self._get_rank_work_page(choose):
                self.dirName = self.rankDirName
                self.existedImg = ','.join(listdir(self.dirName))
                yield work_page
        else:
            print('Wrong input.')
            raise SystemExit(1)
