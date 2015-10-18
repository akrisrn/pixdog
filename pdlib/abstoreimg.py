__author__ = 'akr'

from abc import ABCMeta, abstractclassmethod


class AbStoreImg(object):
    __metaclass__ = ABCMeta

    @abstractclassmethod
    def __get_img_page_url(self):
        pass

    @abstractclassmethod
    def __get_img_page(self):
        pass

    @abstractclassmethod
    def __get_ori_img_url(self):
        pass

    @abstractclassmethod
    def start_store_img(self):
        pass
