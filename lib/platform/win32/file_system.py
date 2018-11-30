__all__ = ['_path_for_url']

def _path_for_url(path):
    idx = path.find(':\\')
    if idx != -1:
        return ':windows:{}:{}'.format(path[:idx],
                                       path[idx+2:].replace('\\', ':'))
    else:
        return path.replace('\\', ':')
