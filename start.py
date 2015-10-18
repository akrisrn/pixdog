__author__ = 'akr'

import pixiv.storeimg
import konachan.storeimg

try:
    print('Please choose a site:')
    print('0.pixiv')
    print('1.konachan')
    option = input('Input 0 or 1: ')
    if option == '0':
        pss = pixiv.storeimg.StoreImg()
        pss.start_store_img()
    elif option == '1':
        kss = konachan.storeimg.StoreImg()
        kss.start_store_img()
    else:
        print('Wrong input.')
except KeyboardInterrupt:
    print('Abort.')
except EOFError:
    print('Abort.')
