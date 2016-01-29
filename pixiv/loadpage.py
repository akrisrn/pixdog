from os import remove

from pixiv.login import Login


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
                self._login(self.pixiv_id, self.password)
                page = self.get_page_data(url, post_value)
            else:
                self._have_not_cookie_login()
                page = self.get_page_data(url, post_value)
        return page
