import pixiv_module

try:
    pixiv_module.start()
except (KeyboardInterrupt, EOFError):
    print('Abort.')