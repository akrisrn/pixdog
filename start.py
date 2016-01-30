import pixiv_module

try:
    pixiv_module.StoreImg().start()
except KeyboardInterrupt:
    print('Abort.')
except EOFError:
    print('Abort.')
