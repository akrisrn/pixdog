from gc import collect
from gzip import GzipFile
from http.client import IncompleteRead
from http.cookiejar import MozillaCookieJar
from io import BytesIO
from math import ceil
from os import listdir, makedirs, mkdir, remove
from os.path import join, exists
from re import compile, finditer, search
from shutil import rmtree
from socket import timeout
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, build_opener, install_opener, Request, urlopen
from zipfile import ZipFile

from images2gif import writeGif


class GetData(object):
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 5.1; rv:5.0) Gecko/20100101 Firefox/5.0',
                        'Accept-Encoding': 'gzip, deflate'
                        }
        self.imgStoreDirName = 'images'

    @staticmethod
    def handle_request(request, time_out=30):
        try:
            try:
                response = urlopen(request, timeout=time_out)
                data = response.read()
            except URLError as e:
                print(e.reason)
                raise SystemExit(1)
            except timeout:
                print('Load slowly.')
                print('Reload...')
                response = urlopen(request, timeout=time_out)
                data = response.read()
            except IncompleteRead:
                print('Load error.')
                print('Reload...')
                response = urlopen(request, timeout=time_out)
                data = response.read()
        except URLError as e:
            print(e.reason)
            raise SystemExit(1)
        except timeout:
            print('Load slowly.')
            print('Please wait a moment and check the network.')
            raise SystemExit(1)
        except IncompleteRead:
            print('Load error.')
            print('Please wait a moment and check the network.')
            raise SystemExit(1)
        return response, data

    def get_img_data(self, url, time_out):
        request = Request(url, headers=self.headers)
        response, img_data = self.handle_request(request, time_out)
        return img_data

    def store_img(self, img_url, img_name, time_out=90):
        print('Store %s...' % img_name)
        img_data = self.get_img_data(img_url, time_out)
        with open(img_name, 'wb') as f:
            f.write(img_data)
        del img_data
        print('Store success.', end=' ')

    def get_page_data(self, url, post_value=None):
        if post_value is not None:
            post_data = urlencode(post_value).encode('utf-8')
            request = Request(url, post_data, self.headers)
        else:
            request = Request(url, headers=self.headers)
        response, page_data = self.handle_request(request)
        if response.info().get('Content-Encoding') == 'gzip':
            f = GzipFile(fileobj=BytesIO(page_data))
            page_data = f.read().decode('utf-8')
        else:
            page_data = page_data.decode('utf-8')
        return page_data


class Login(GetData):
    def __init__(self):
        super().__init__()
        self.userSetUrl = 'http://www.pixiv.net/setting_user.php'
        self.loginUrl = 'https://www.secure.pixiv.net/login.php'
        self.cookiesFile = 'pixiv-cookies.txt'
        self.pixiv_id = ''
        self.password = ''

    def check_cookies(self):
        if exists(self.cookiesFile):
            self.have_cookie_login()
        else:
            self.have_not_cookie_login()

    def have_cookie_login(self):
        print('Load cookies...')
        cookie = MozillaCookieJar()
        cookie.load(self.cookiesFile, ignore_discard=True, ignore_expires=True)
        opener = build_opener(HTTPCookieProcessor(cookie))
        install_opener(opener)
        print('Test cookies...')
        page = self.get_page_data(self.userSetUrl)
        if not search('page-setting-user', page):
            print('This cookies has been invalid.')
            print('Delete the old cookies.')
            remove(self.cookiesFile)
            self.have_not_cookie_login()
        else:
            print('Test success.')

    def have_not_cookie_login(self):
        select = input('Use the default account to login? (y / n)\n')
        select = select.lower()
        if select == 'y':
            self.login()
        elif select == 'n':
            self.pixiv_id = input('Input your account: ')
            self.password = input('Input your account password: ')
            self.login(self.pixiv_id, self.password)
        else:
            print('Wrong input.')
            raise SystemExit(1)

    def login(self, pixiv_id='614634238', password='spider614634238'):
        cookie = MozillaCookieJar(self.cookiesFile)
        opener = build_opener(HTTPCookieProcessor(cookie))
        install_opener(opener)
        print('Login...')
        post_value = {'mode': 'login',
                      'return_to': '/',
                      'pixiv_id': pixiv_id,
                      'pass': password
                      }
        page = self.get_page_data(self.loginUrl, post_value)
        if search('error-guide', page):
            print('Login failed.')
            raise SystemExit(1)
        else:
            print('Login success.')
        print('Store cookies...')
        cookie.save(ignore_discard=True, ignore_expires=True)


class LoadPage(Login):
    def __init__(self):
        super().__init__()
        self.pixiv = 'pixiv'

    def url_open(self, url, post_value=None):
        page = self.get_page_data(url, post_value)
        if (page.find('welcome') != -1) or (page.find('login-button') != -1):
            print('This cookies has been invalid.')
            print('Delete the old cookies.')
            remove(self.cookiesFile)
            if hasattr(self, 'pixiv_id'):
                print('Automatic re ', end='')
                self.login(self.pixiv_id, self.password)
                page = self.get_page_data(url, post_value)
            else:
                self.have_not_cookie_login()
                page = self.get_page_data(url, post_value)
        return page


class GetRankPage(LoadPage):
    def __init__(self):
        super().__init__()
        self.rankUrl = 'http://www.pixiv.net/ranking.php?'
        self.rankDirName = ''

    def get_rank_work_page(self, mode):
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


class GetUserPage(LoadPage):
    def __init__(self):
        super().__init__()
        self.memIllUrl = 'http://www.pixiv.net/member_illust.php?'
        self.userId = ''
        self.userDirName = ''

    def get_user_work_page(self):
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


class SwitchPage(GetUserPage, GetRankPage):
    def __init__(self):
        GetUserPage.__init__(self)
        GetRankPage.__init__(self)
        self.dirName = ''
        self.existedName = ''

    def switch_work_page(self):
        print('Please choose a model:')
        print('0.To get image according to the user id')
        print('1.To get image according to the rank')
        option = input('Input 0 or 1: ')
        if option == '0':
            for work_page in self.get_user_work_page():
                self.dirName = self.userDirName
                self.existedName = ','.join(listdir(self.dirName))
                yield work_page
        elif option == '1':
            choose = input('Please choose daily/weekly/monthly/rookie/original/male/female/ugoira_daily/ugoira_weekly/'
                           'daily_r18/weekly_r18/male_r18/female_r18/ugoira_daily_r18/ugoira_weekly_r18:\n'
                           )
            if choose not in ['daily', 'weekly', 'monthly', 'rookie', 'original', 'male', 'female',
                              'ugoira_daily', 'ugoira_weekly',
                              'daily_r18', 'weekly_r18', 'male_r18', 'female_r18',
                              'ugoira_daily_r18', 'ugoira_weekly_r18'
                              ]:
                print('Wrong input.')
                raise SystemExit(1)
            for work_page in self.get_rank_work_page(choose):
                self.dirName = self.rankDirName
                self.existedName = ','.join(listdir(self.dirName))
                yield work_page
        else:
            print('Wrong input.')
            raise SystemExit(1)


class StoreImg(SwitchPage):
    def __init__(self):
        super().__init__()
        self.check_cookies()
        select = input('Enable to get dynamic images? (y / n)\n')
        select = select.lower()
        if select == 'y':
            try:
                __import__('PIL')
            except ImportError:
                print('Please install pillow module first.')
                print('`pip install pillow`')
                raise SystemExit(1)
            self.enable_dy_img = True
        elif select == 'n':
            self.enable_dy_img = False
        else:
            print('Wrong input.')
            raise SystemExit(1)
        self.img_id = ''
        self.img_class = ''

    def get_img_page_url(self):
        pattern = compile('image-item.*?href=".*?id=(\d*).*?"\s*class="work\s*_work\s*(.*?)\s*"')
        for work_page in self.switch_work_page():
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
                    if self.existedName.find(self.img_id + '_ugoira1920x1080') != -1:
                        print('Exist zip file.', end='')
                        zip_name = self.img_id + '_ugoira1920x1080.zip'
                        zip_name = join(self.dirName, zip_name)
                        self.get_gif_img(zip_name)
                        print()
                        continue
                    elif self.existedName.find(self.img_id) != -1:
                        print('Image has been saved.')
                        continue
                    else:
                        print('Load image page...')
                else:
                    print('Get multiple images...')
                yield img_page_url

    def get_img_page(self):
        for img_page_url in self.get_img_page_url():
            img_page = self.url_open(img_page_url)
            self.headers['Referer'] = img_page_url
            yield img_page

    def get_img_url(self):
        pattern = compile('data-src="(.*?)"\s*class="original-image">')
        pattern_meta2 = compile('class="meta"><li>.*?</li><li>(.*?)</li>')
        for img_page in self.get_img_page():
            ori_img_url = search(pattern, img_page)
            if ori_img_url:
                print('Get the original image url...')
                yield ori_img_url.group(1)
            else:
                meta2 = search(pattern_meta2, img_page).group(1)
                if meta2.find('P') != -1:
                    img_num = meta2.split()[-1][:-1]
                    yield from self.get_mul_img_url(self.img_id, img_num)
                elif img_page.find('ugoira') != -1:
                    if self.enable_dy_img:
                        print('Get the original dynamic image url...')
                        dyn_ori_img_url = search('Full.*?"src":"(.*?)"', img_page).group(1).replace('\\', '')
                        yield dyn_ori_img_url
                    else:
                        print('Can not get dynamic image.')
                else:
                    yield from self.get_ori_img_url(self.img_id)

    def get_ori_img_url(self, img_id):
        get_value = {'mode': 'big',
                     'illust_id': img_id,
                     }
        get_data = urlencode(get_value)
        ori_img_page_url = self.memIllUrl + get_data
        ori_img_page = self.url_open(ori_img_page_url)
        self.headers['Referer'] = ori_img_page_url
        ori_img_url = search('src="(.*?)"', ori_img_page).group(1)
        yield ori_img_url

    def get_mul_img_url(self, img_id, img_num):
        get_value = {'mode': 'manga_big',
                     'illust_id': img_id,
                     }
        print('Total number of image: %s' % img_num)
        for i in range(int(img_num)):
            if self.existedName.find('%s_p%d' % (img_id, i)) != -1:
                print('Image has been saved. (%d / %s)' % (i + 1, img_num))
                continue
            get_value['page'] = i
            get_data = urlencode(get_value)
            ori_img_page_url = self.memIllUrl + get_data
            print('Load the original image page...')
            ori_img_page = self.url_open(ori_img_page_url)
            self.headers['Referer'] = ori_img_page_url
            print('Get the original image url...(%d / %s)' % (i + 1, img_num))
            ori_img_url = search('src="(.*?)"', ori_img_page).group(1)
            yield ori_img_url

    def get_gif_img(self, zip_name):
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
        zip_file.close()
        print('Store %s...' % gif_name)
        from PIL import Image
        images = [Image.open(img_name) for img_name in tmp_files]
        writeGif(gif_name, images, subRectangles=False)
        del images
        print('Store success.', end=' ')
        remove(zip_name)
        rmtree(tmp_dir)

    def start(self):
        count = 1
        for img_url in self.get_img_url():
            img_name = join(self.dirName, img_url.split('/')[-1])
            if img_name.endswith('zip'):
                self.store_img(img_url, img_name, 120)
                self.get_gif_img(img_name)
            else:
                self.store_img(img_url, img_name)
            print('(%d)' % count)
            count += 1
            collect()
        else:
            print('Task completion.')
