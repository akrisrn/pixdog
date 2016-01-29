from os.path import join
from re import compile, search, finditer

from pdlib.abstoreimg import AbStoreImg
from konachan.gettagpage import GetTagPage


class StoreImg(GetTagPage, AbStoreImg):
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

    def start_store_img(self):
        count = 1
        for ori_img_url in self.__get_ori_img_url():
            img_name = join(self.tagDirName, (self.img_id + '.' + str(ori_img_url.split('.')[-1])))
            self.store_img(ori_img_url, img_name)
            print('(%d)' % count)
            count += 1
        else:
            print('Task completion.')
