

def write_file(fpath, text, encoding='utf8'):
    with open(fpath, 'w', encoding=encoding) as f:
        f.write(text)
