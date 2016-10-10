import pixiv_module
import ehentai_module

try:
    print("0.pixiv")
    print("1.g.ehentai")
    select = input('Enter id: ')
    if select == "0":
        pixiv_module.start()
    elif select == "1":
        ehentai_module.start()
    else:
        print('Wrong input.')
except (KeyboardInterrupt, EOFError):
    print('Abort.')
