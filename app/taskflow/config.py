
# from multidict import CIMultiDict

task = {
    'max_concurrent': 3,
    'tempdir': '',
    'async': True,
}
script = {
    'max_concurrent': 3,
    'async': False,
}
download = {
    'engine': 'Nbdler',
    'max_concurrent': 5,
    'max_speed': None,
    'timeout': None,
    'max_retries': 10,
    'async': True,
}
ffmpeg = {
    'engine': 'ffmpeg',
    'max_concurrent': 5,
    'source': r'',
    'name': 'ffmpeg',
    'overwrite': True,
    'async': True,
}
convert = {
    'engine': 'ffmpeg',
    'max_concurrent': 3,
    'async': True,
}
live = {
    'max_concurrent': 5,
    'async': True
}
jsruntime = {
    'engine': 'NodeJS',
    'max_concurrent': 2,
    'name': 'node',
    'source': '',
    'version': None,
    'shell': False,
    'async': False,
}
cleanup = {
    'max_concurrent': 3,
    'async': False
}
stop = {
    'max_concurrent': 10,
    'entrypoint': 'submit',
    'async': False
}


# def __getitem__(name):
#     return globals()[name]

# worker = {
#     'task': {
#         'max_concurrent': 3,
#         'tempdir': '',
#         'async': True,
#     },
#     'script': {
#         'max_concurrent': 3,
#         'async': False,
#     },
#     'download': {
#         'engine': 'Nbdler',
#         'max_concurrent': 5,
#         'max_speed': None,
#         'timeout': None,
#         'max_retries': 10,
#         'async': True,
#     },
#     'ffmpeg': {
#         'engine': 'ffmpeg',
#         'max_concurrent': 5,
#         'source': r'',
#         'name': 'ffmpeg',
#         'overwrite': True,
#         'async': True,
#     },
#     'convert': {
#         'engine': 'ffmpeg',
#         'max_concurrent': 3,
#         'async': True,
#     },
#     'live': {
#         'max_concurrent': 5,
#         'async': True
#     },
#     'jsruntime': {
#         'engine': 'NodeJS',
#         'max_concurrent': 2,
#         'name': 'node',
#         'source': '',
#         'version': None,
#         'shell': False,
#         'async': False,
#     },
#     'cleanup': {
#         'max_concurrent': 3,
#         'async': False
#     },
#     'stop': {
#         'max_concurrent': 10,
#         'entrypoint': 'submit',
#         'async': False
#     }
# }


# def get_config(name):
#     return CIMultiDict(globals())[name]
#     # return __REQUESTER_CONFIG__[name]

