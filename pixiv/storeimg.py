__author__ = 'akr'

from re import compile, finditer, search
from urllib.parse import urlencode

from pixiv.switchpage import SwitchPage


class StoreImg(SwitchPage):
    def __init__(self):
        super().__init__()
        self.login()

    def __get_img_page_url(self):
        pattern = compile('image-item.*?href=".*?id=(\d*).*?"\s*class="work\s*_work\s*(.*?)\s*"')

        for work_page in self._switch_work_page():
            for result in finditer(pattern, work_page):
                print('Get image id...')
                self.img_id = result.group(1)
                self.img_class = result.group(2)

                get_value = {'mode': 'medium',
                             'illust_id': self.img_id
                             }
                get_data = urlencode(get_value)
                img_page_url = self.memIllUrl + get_data

                if self.img_class.find('multiple') == -1:
                    if self.existedImg.find('%s_p0' % self.img_id) != -1:
                        print('Image has been saved.')
                        continue
                    print('Load image page...')
                else:
                    print('Get multiple images...')
                yield img_page_url

    def __get_img_page(self):
        for img_page_url in self.__get_img_page_url():
            self.refererUrl = img_page_url
            img_page = self.url_open(img_page_url)
            yield img_page

    def __get_original_img_url(self):
        pattern = compile('data-src="(.*?)"\s*class="original-image">')
        pattern_meta2 = compile('class="meta"><li>.*?</li><li>(.*?)</li>')

        for img_page in self.__get_img_page():
            meta2 = search(pattern_meta2, img_page).group(1)
            ori_img_url = search(pattern, img_page)

            if ori_img_url:
                print('Get the original image url...')
                yield ori_img_url.group(1)
            elif meta2.find('P') != -1:
                img_num = meta2.split()[-1][:-1]
                yield from self.__get_mul_original_img_url(self.img_id, img_num)
            else:
                print('Can not store dynamic images.')

    def __get_mul_original_img_url(self, img_id, img_num):
        get_value = {'mode': 'manga_big',
                     'illust_id': img_id,
                     }
        print('Total number of image: %s' % img_num)

        for i in range(int(img_num)):
            if self.existedImg.find('%s_p%d' % (img_id, i)) != -1:
                print('Image has been saved. (%d / %s)' % (i + 1, img_num))
                continue

            get_value['page'] = i
            get_data = urlencode(get_value)
            ori_img_page_url = self.memIllUrl + get_data
            self.refererUrl = ori_img_page_url

            print('Load the original image page...')
            ori_img_page = self.url_open(ori_img_page_url)

            print('Get the original image url...(%d / %s)' % (i + 1, img_num))
            ori_img_url = search('src="(.*?)"', ori_img_page).group(1)
            yield ori_img_url

    def start(self):
        count = 1
        for ori_img_url in self.__get_original_img_url():
            img_name = '%s/%s' % (self.dirName, ori_img_url.split('/')[-1])

            self.headers['Referer'] = self.refererUrl

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