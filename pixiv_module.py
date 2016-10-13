from gzip import GzipFile
from http.client import IncompleteRead, RemoteDisconnected
from http.cookiejar import MozillaCookieJar
from io import BytesIO
from math import ceil
from os import listdir, makedirs, remove
from os.path import join, exists, split
from re import compile, finditer, search
from shutil import rmtree
from socket import timeout
from threading import Thread
from time import sleep
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, build_opener, install_opener, Request, urlopen
from zipfile import ZipFile

from socks import SOCKS5
from sockshandler import SocksiPyHandler

from images2gif import writeGif


class GetData(object):
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 5.1; rv:5.0) Gecko/20100101 Firefox/5.0',
                        'Accept-Encoding': 'gzip, deflate'
                        }
        self.imgStoreDirName = 'images'

    @staticmethod
    def handle_request(request, time_out=30):
        while True:
            try:
                response = urlopen(request, timeout=time_out)
                data = response.read()
                return response, data
            except URLError as e:
                print(e.reason)
                return "", ""
            except (timeout, IncompleteRead, RemoteDisconnected):
                print('Reload...')

    @staticmethod
    def build_opener(cookie, use_proxy):
        if use_proxy:
            opener = build_opener(HTTPCookieProcessor(cookie), SocksiPyHandler(SOCKS5, '127.0.0.1', 1080))
        else:
            opener = build_opener(HTTPCookieProcessor(cookie))
        install_opener(opener)

    def get_img_data(self, url, time_out):
        request = Request(url, headers=self.headers)
        response, img_data = self.handle_request(request, time_out)
        return img_data

    def store_img(self, img_url, img_name, time_out=90):
        path, name = split(img_name)
        img_data = self.get_img_data(img_url, time_out)
        with open(img_name, 'wb') as f:
            f.write(img_data)
        del img_data
        if name.find('zip') == -1:
            print('%s is saved in %s.' % (name, path), end=' ')

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
        self.loginUrl = 'https://accounts.pixiv.net/login'
        self.cookiesFile = 'pixiv-cookies.txt'
        self.pixiv_id = ''
        self.password = ''
        self.use_proxy = False

    def check_cookies(self):
        if exists(self.cookiesFile):
            self.have_cookie_login()
        else:
            self.have_not_cookie_login()

    def have_cookie_login(self):
        print('Test cookies...')
        cookie = MozillaCookieJar()
        cookie.load(self.cookiesFile, ignore_discard=True, ignore_expires=True)
        self.build_opener(cookie, self.use_proxy)
        page = self.get_page_data(self.userSetUrl)
        if not search('page-setting-user', page):
            print('This cookies has been invalid.')
            remove(self.cookiesFile)
            self.have_not_cookie_login()

    def have_not_cookie_login(self):
        select = input('Use the default account to login? [Y/N]: ')
        select = select.lower()
        if select == 'y':
            self.login()
        elif select == 'n':
            self.pixiv_id = input('Input your account: ')
            self.password = input('Input your password: ')
            self.login(self.pixiv_id, self.password)
        else:
            print('Wrong input.')
            raise SystemExit(1)

    def login(self, pixiv_id='614634238', password='spider614634238'):
        cookie = MozillaCookieJar(self.cookiesFile)
        self.build_opener(cookie, self.use_proxy)
        print('Login...')

        page = self.get_page_data(self.loginUrl)
        pattern = compile('name="post_key"\s*value="(.*?)"')
        post_key = search(pattern, page).group(1)

        post_value = {
            'pixiv_id': pixiv_id,
            'password': password,
            'g_recaptcha_response': '',
            'post_key': post_key,
            'source': 'pc'
        }
        page = self.get_page_data(self.loginUrl, post_value)
        if search('error-msg-list', page):
            print('Login failed.')
            raise SystemExit(1)
        cookie.save(ignore_discard=True, ignore_expires=True)


class LoadPage(Login):
    def __init__(self):
        super().__init__()
        self.pixiv = 'pixiv'

    def url_open(self, url, post_value=None):
        page = self.get_page_data(url, post_value)
        if page.find('ui-button _login') != -1:
            print('This cookies has been invalid.')
            remove(self.cookiesFile)
            if hasattr(self, 'pixiv_id'):
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
            if not work_page:
                break
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
        print("Load the page 1...")
        work_page = self.url_open(work_url)
        pattern = compile('class="count-badge">(.*?)</span>')
        count_num = search(pattern, work_page)
        count_num = int(count_num.group(1)[:-1])
        total_page = ceil(count_num / 20)
        yield work_page
        for i in range(2, total_page + 1):
            get_value['p'] = i
            get_data = urlencode(get_value)
            work_url = self.memIllUrl + get_data
            print("Load the page %d..." % i)
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
            rank = ['daily', 'weekly', 'monthly', 'rookie', 'original', 'male', 'female',
                    'ugoira_daily', 'ugoira_weekly',
                    'daily_r18', 'weekly_r18', 'male_r18', 'female_r18',
                    'ugoira_daily_r18', 'ugoira_weekly_r18'
                    ]
            print('Please choose a rank:')
            print('0.daily')
            print('1.weekly')
            print('2.monthly')
            print('3.rookie')
            print('4.original')
            print('5.male')
            print('6.female')
            print('7.ugoira_daily')
            print('8.ugoira_weekly')
            print('9.daily_r18')
            print('10.weekly_r18')
            print('11.male_r18')
            print('12.female_r18')
            print('13.ugoira_daily_r18')
            print('14.ugoira_weekly_r18')
            choose = input('Input 0~14: ')
            if not choose.isdigit() or not (int(choose) in range(len(rank))):
                print('Wrong input.')
                raise SystemExit(1)
            for work_page in self.get_rank_work_page(rank[int(choose)]):
                self.dirName = self.rankDirName
                self.existedName = ','.join(listdir(self.dirName))
                yield work_page
        else:
            print('Wrong input.')
            raise SystemExit(1)


class StoreImg(SwitchPage):
    def __init__(self):
        super().__init__()
        self.img_id = ''
        self.img_class = ''

    def get_img_page_url(self):
        pattern = compile('image-item.*?href=".*?id=(\d*).*?"\s*class="work\s*_work\s*(.*?)\s*"')
        for work_page in self.switch_work_page():
            for result in finditer(pattern, work_page):
                self.img_id = result.group(1)
                self.img_class = result.group(2)
                get_value = {'mode': 'medium',
                             'illust_id': self.img_id
                             }
                get_data = urlencode(get_value)
                img_page_url = self.memIllUrl + get_data
                if self.img_class.find('multiple') == -1:
                    if self.existedName.find(self.img_id + '_ugoira1920x1080') != -1:
                        zip_name = self.img_id + '_ugoira1920x1080.zip'
                        zip_name = join(self.dirName, zip_name)
                        self.get_gif_img(zip_name)
                        continue
                    elif self.existedName.find(self.img_id) != -1:
                        print('Image has been saved.')
                        continue
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
                yield ori_img_url.group(1)
            else:
                meta2 = search(pattern_meta2, img_page).group(1)
                if meta2.find('P') != -1:
                    img_num = meta2.split()[-1][:-1]
                    yield from self.get_mul_img_url(self.img_id, img_num)
                elif img_page.find('ugoira') != -1:
                    dyn_ori_img_url = search('Full.*?"src":"(.*?)"', img_page).group(1).replace('\\', '')
                    yield dyn_ori_img_url
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
        for i in range(int(img_num)):
            if self.existedName.find('%s_p%d' % (img_id, i)) != -1:
                print('Image has been saved.')
                continue
            get_value['page'] = i
            get_data = urlencode(get_value)
            ori_img_page_url = self.memIllUrl + get_data
            ori_img_page = self.url_open(ori_img_page_url)
            self.headers['Referer'] = ori_img_page_url
            ori_img_url = search('src="(.*?)"', ori_img_page).group(1)
            yield ori_img_url

    def get_gif_img(self, zip_name):
        tmp_files = []
        gif_name = zip_name.split('_ugoira')[0] + '.gif'
        path, name = split(gif_name)
        tmp_dir = join(self.dirName, 'tmp', name)
        if not exists(tmp_dir):
            makedirs(tmp_dir)
        zip_file = ZipFile(zip_name)
        for file_name in zip_file.namelist():
            tmp_file_name = join(tmp_dir, file_name)
            zip_data = zip_file.read(file_name)
            with open(tmp_file_name, 'wb') as f:
                f.write(zip_data)
            tmp_files.append(tmp_file_name)
        zip_file.close()
        from PIL import Image
        images = [Image.open(img_name) for img_name in tmp_files]
        writeGif(gif_name, images, subRectangles=False)
        del images
        print('%s is saved in %s.' % (name, path), end=' ')
        remove(zip_name)
        rmtree(tmp_dir)


count = 1


def th(si, img_url):
    global count
    img_name = join(si.dirName, img_url.split('/')[-1])
    if img_name.endswith('zip'):
        si.store_img(img_url, img_name, 120)
        si.get_gif_img(img_name)
    else:
        si.store_img(img_url, img_name)
    print('(%d)' % count)
    count += 1


def start():
    si = StoreImg()
    proxy = input('Use proxy(sock5, port=1080)? [Y/N]: ')
    if proxy.lower() == 'y':
        si.use_proxy = True
    si.check_cookies()
    max_thread = 10
    thread = []
    for img_url in si.get_img_url():
        while True:
            thread = [t for t in thread if t.is_alive()]
            if len(thread) < max_thread:
                t = Thread(target=th, args=(si, img_url))
                thread.append(t)
                t.setDaemon(True)
                t.start()
                break
            else:
                sleep(1)
    for t in thread:
        t.join()
    print('Task completion.')
