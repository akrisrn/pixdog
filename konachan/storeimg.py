__author__ = 'akr'

from os import mkdir, listdir
from os.path import exists
from re import compile, search, finditer

from tool.getdata import GetData


class StoreImg(GetData):
    def __init__(self):
        super().__init__()
        self.konachan = 'konachan'
        self.postShowUrl = 'http://konachan.com/post/show/'
        self.tagPageUrl = 'http://konachan.com/post?page=%d&tags=%s'

    def __get_tag_page(self):
        self.tag = input('Please enter the tag name:')
        self.tagDirName = '%s/%s' % (self.konachan, self.tag)
        if not exists(self.tagDirName):
            mkdir(self.tagDirName)
        else:
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

    def __get_img_page_url(self):
        pattern = compile('<a.*?class="thumb".*?href="/post/show/(\d*)/')

        for tag_page in self.__get_tag_page():
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

    def __get_original_img_url(self):
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
        for ori_img_url in self.__get_original_img_url():
            img_name = '%s/%s.%s' % (self.tag, self.img_id, ori_img_url.split('.')[-1])

            print('Load the original image...')
            img_data = self.get_img_data(ori_img_url)

            print('Store %s...' % img_name)
            f = open(img_name, 'wb')
            f.write(img_data)
            f.close()
            print('Store success. (%d)' % count)

            count += 1
        else:
            print('Task completion.')
