from os import makedirs, listdir
from os.path import exists
from os.path import join
from re import compile, search, finditer

from common import GetData


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


class StoreImg(GetTagPage):
    def __init__(self):
        super().__init__()
        self.postShowUrl = 'http://konachan.com/post/show/'

    def __get_img_page_url(self):
        pattern = compile('<a.*?class="thumb".*?href="/post/show/(\d*)/')
        for tag_page in self._get_tag_page():
            for result in finditer(pattern, tag_page):
                print('Get image id...')
                self.img_id = result.group(1)
                if self.existedImg.find(self.img_id) != -1:
                    print('Image has been saved.')
                    continue
                img_page_url = self.postShowUrl + self.img_id
                yield img_page_url

    def __get_img_page(self):
        for img_page_url in self.__get_img_page_url():
            print('Load image page...')
            img_page = self.get_page_data(img_page_url)
            yield img_page

    def __get_ori_img_url(self):
        pattern_best = compile('<a.*?class="original-file-unchanged".*?href="(.*?)".*?id="png"')
        pattern_better = compile('<a.*?class="original-file-unchanged".*?href="(.*?)".*?id="highres"')
        pattern_good = compile('<a.*?class="original-file-changed".*?href="(.*?)".*?id="highres"')
        for img_page in self.__get_img_page():
            print('Get the original image url...')
            best_img_url = search(pattern_best, img_page)
            better_img_url = search(pattern_better, img_page)
            good_img_url = search(pattern_good, img_page)
            if best_img_url:
                yield best_img_url.group(1)
            elif better_img_url:
                yield better_img_url.group(1)
            else:
                yield good_img_url.group(1)

    def start(self):
        count = 1
        for ori_img_url in self.__get_ori_img_url():
            img_name = join(self.tagDirName, (self.img_id + '.' + str(ori_img_url.split('.')[-1])))
            self.store_img(ori_img_url, img_name)
            print('(%d)' % count)
            count += 1
        else:
            print('Task completion.')