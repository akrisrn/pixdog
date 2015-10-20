__author__ = 'akr'

from shutil import rmtree
from os import mkdir, remove
from os.path import join, exists
from re import compile, finditer, search
from urllib.parse import urlencode
from zipfile import ZipFile
from PIL import Image

from pdlib.images2gif import writeGif
from pdlib.abstoreimg import AbStoreImg
from pixiv.switchpage import SwitchPage


class StoreImg(SwitchPage, AbStoreImg):
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
                    if self.existedImg.find(self.img_id) != -1:
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

    def __get_ori_img_url(self):
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
                yield from self.__get_mul_ori_img_url(self.img_id, img_num)
            else:
                print('Get the original dynamic image url...')
                dyn_ori_img_url = search('Full.*?"src":"(.*?)"', img_page).group(1).replace('\\', '')
                yield dyn_ori_img_url

    def __get_mul_ori_img_url(self, img_id, img_num):
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

    def __get_gif_img(self, zip_name):
        tmp_files = []
        gif_name = zip_name.split('_ugoira')[0] + '.gif'

        tmp_dir = join(self.dirName, 'tmp')
        if not exists(tmp_dir):
            mkdir(tmp_dir)

        print('\nUnzip the file...')
        zip_file = ZipFile(zip_name)

        for file_name in zip_file.namelist():
            tmp_file_name = join(tmp_dir, file_name)
            zip_data = zip_file.read(file_name)
            with open(tmp_file_name, 'wb') as f:
                f.write(zip_data)
            tmp_files.append(tmp_file_name)

        print('Store %s...' % gif_name)
        images = [Image.open(img_name) for img_name in tmp_files]
        writeGif(gif_name, images, subRectangles=False)
        print('Store success.', end=' ')

        remove(zip_name)
        rmtree(tmp_dir)

    def start_store_img(self):
        count = 1
        for ori_img_url in self.__get_ori_img_url():
            img_name = join(self.dirName, ori_img_url.split('/')[-1])
            self.headers['Referer'] = self.refererUrl

            if img_name.endswith('zip'):
                self.store_img(ori_img_url, img_name, 120)
                self.__get_gif_img(img_name)
            else:
                self.store_img(ori_img_url, img_name)

            print('(%d)' % count)
            count += 1
        else:
            print('Task completion.')
