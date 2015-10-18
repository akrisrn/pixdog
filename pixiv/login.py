__author__ = 'akr'

from re import search
from os import remove
from os.path import exists
from http.cookiejar import MozillaCookieJar
from urllib.request import HTTPCookieProcessor, build_opener, install_opener

from tool.getdata import GetData


class Login(GetData):
    def __init__(self):
        super().__init__()
        self.userSetUrl = 'http://www.pixiv.net/setting_user.php'
        self.loginUrl = 'https://www.secure.pixiv.net/login.php'
        self.cookiesFile = 'cookies.txt'

    def login(self):
        if exists(self.cookiesFile):
            self._have_cookie_login()
        else:
            self._have_not_cookie_login()

    def _have_cookie_login(self):
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
            self._have_not_cookie_login()
        else:
            print('Test success.')

    def _have_not_cookie_login(self):
        select = input('Use the default account to login? (yes / no)\n')

        if select == 'yes':
            self._login()
        elif select == 'no':
            self.pixiv_id = input('Input your account: ')
            self.password = input('Input your account password: ')
            self._login(self.pixiv_id, self.password)
        else:
            print('Wrong input.')
            raise SystemExit(1)

    def _login(self, pixiv_id='614634238', password='spider614634238'):
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
