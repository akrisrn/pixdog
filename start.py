import pixiv_module
import konachan_module

try:
    print('Please choose a site:')
    print('0.pixiv')
    print('1.konachan')
    option = input('Input 0 or 1: ')
    if option == '0':
        pixiv_module.StoreImg().start()
    elif option == '1':
        konachan_module.StoreImg().start()
    else:
        print('Wrong input.')
except KeyboardInterrupt:
    print('Abort.')
except EOFError:
    print('Abort.')
