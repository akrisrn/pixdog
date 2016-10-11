from math import ceil
from socks import SOCKS5
from socket import timeout
from os import listdir, makedirs
from os.path import join, exists
from urllib.error import URLError
from re import compile, findall, search
from urllib.request import build_opener, urlopen
from sockshandler import SocksiPyHandler
from http.client import IncompleteRead, RemoteDisconnected

opener = build_opener(SocksiPyHandler(SOCKS5, "127.0.0.1", 1080))


def url_open(url, use_proxy, t=60):
    while True:
        try:
            if use_proxy:
                return opener.open(url, timeout=t).read()
            else:
                return urlopen(url, timeout=t).read()
        except URLError as e:
            print(e.reason)
            raise SystemExit(1)
        except (timeout, IncompleteRead, RemoteDisconnected):
            print('Load error.')
            print('Reload...')


def get_img_mark(page_data, page_num, manga_page_url, use_proxy):
    pattern = compile('<a href="http://g\.e-hentai\.org/s/(.*?)">')
    for img_mark in findall(pattern, page_data):
        yield img_mark

    for i in range(1, page_num):
        print("Load the page %d..." % page_num)
        page_data = url_open(manga_page_url + "?p=" + str(i), use_proxy).decode('utf-8')
        for img_mark in findall(pattern, page_data):
            yield img_mark


def start():
    use_proxy = False
    proxy = input("Use proxy(sock5, port=1080)?[Y/n]: ")
    if proxy.lower() == "y":
        use_proxy = True

    manga_mark = input('Input your mysterious code: ')
    if manga_mark[0] == "/":
        manga_mark = manga_mark[1:]
    if manga_mark[-1] != "/":
        manga_mark += "/"
    result = manga_mark.split("/")
    if result.__len__() != 3:
        print("Error code.")
        raise SystemExit(1)

    manga_page_url = "http://g.e-hentai.org/g/" + manga_mark
    img_page_url = "http://g.e-hentai.org/s/"

    print("Load the page 1...")
    page_data = url_open(manga_page_url, use_proxy).decode('utf-8')

    pattern = compile('<h1 id="gj">(.*?)</h1>')
    title = search(pattern, page_data).group(1)
    if title == "":
        pattern = compile('<h1 id="gn">(.*?)</h1>')
        title = search(pattern, page_data).group(1)
    path = join("images", "ehentai", title)
    if not exists(path):
        makedirs(path)

    pattern = compile('<p class="gpc">Showing 1 - (\d*) of (\d*) images</p>')
    result = search(pattern, page_data).groups()
    img_count = int(result[1])
    page_num = ceil(img_count / int(result[0]))

    count = 1
    for img_mark in get_img_mark(page_data, page_num, manga_page_url, use_proxy):
        print("Load image page...")
        page_data = url_open(img_page_url + img_mark, use_proxy).decode('utf-8')
        pattern = compile('<img id="img" src="(.*?)"')
        img_url = search(pattern, page_data).group(1)
        img_name = str(img_url.split('/')[-1])
        exist_img = ','.join(listdir(path))
        if exist_img.find(img_name) != -1:
            print('Image has been saved.', end="")
        else:
            img_path = join(path, img_name)
            print('Store %s...' % img_path)
            img_data = url_open(img_url, use_proxy)
            with open(img_path, 'wb') as f:
                f.write(img_data)
            del img_data
            print('Store success.', end=' ')
        print("(%d/%d)" % (count, img_count))
        count += 1
    print('Task completion.')