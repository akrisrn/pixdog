__author__ = 'akr'

from io import BytesIO
from gzip import GzipFile
from socket import timeout
from http.client import IncompleteRead
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


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
        response, img_data = GetData.handle_request(request, time_out)
        return img_data

    def store_img(self, img_url, img_name, time_out=90):
        print('Store %s...' % img_name)
        img_data = self.get_img_data(img_url, time_out)
        with open(img_name, 'wb') as f:
            f.write(img_data)
        print('Store success.', end=' ')

    def get_page_data(self, url, post_value=None):
        if post_value is not None:
            post_data = urlencode(post_value).encode('utf-8')
            request = Request(url, post_data, self.headers)
        else:
            request = Request(url, headers=self.headers)

        response, page_data = GetData.handle_request(request)

        if response.info().get('Content-Encoding') == 'gzip':
            f = GzipFile(fileobj=BytesIO(page_data))
            page_data = f.read().decode('utf-8')
        else:
            page_data = page_data.decode('utf-8')
        return page_data
