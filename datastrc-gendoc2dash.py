"""
    Generate Dash docset for Data Structure wikibooks
"""
import sqlite3
import os
import urllib2
from bs4 import BeautifulSoup as bs
import requests


# CONFIGURATION
docset_name = 'datastructure-wikibooks.docset'
output = docset_name + '/Contents/Resources/Documents'
root_url = 'http://en.wikibooks.org/wiki/Data_Structures'

# create docset directory
docpath = output + '/'
if not os.path.exists(docpath): os.makedirs(docpath)

# soup
data = requests.get(root_url).text
soup = bs(data)
open(os.path.join(output, 'index.html'), 'wb').write(data.encode('ascii', 'ignore'))


def update_db(name, path):
    typ = 'Guide'
    cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?,?,?)', (name, typ, path))
    print 'DB add >> name: %s, path: %s' % (name, path)


def add_docs():
    sections = []
    titles = []
    for i, link in enumerate(soup.findAll('a')):
        name = link.text.strip()
        path = link.get('href')

        if isinstance(path, str) and name.startswith('Chapter'):
            sections.append(path)
            titles.append(name)

    # generate letters for ascending entry index
    import string

    c = list(string.uppercase)
    l = [w for w in c]
    y = 0

    # download and update db
    for path, name in zip(sections, titles):
        # create subdir
        folder = os.path.join(output)
        for i in range(len(path.split("/")) - 1):
            folder += path.split("/")[i] + "/"
        if not os.path.exists(folder): os.makedirs(folder)

        print "%s:" % y, name, path
        try:
            # download docs
            subject = path.split('/')[-1]
            url = root_url + '/' + subject
            res = urllib2.urlopen(url)
            open(os.path.join(folder, subject + '.html'), 'wb').write(res.read())
            print "downloaded doc: ", l[y], path
            print " V"

            # update db
            name = l[y] + ': ' + name
            path += '.html'
            update_db(name, path)
            y += 1
        except:
            print " X"
            pass


def add_infoplist():
    name = docset_name.split('.')[0]
    info = " <?xml version=\"1.0\" encoding=\"UTF-8\"?>" \
           "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> " \
           "<plist version=\"1.0\"> " \
           "<dict> " \
           "    <key>CFBundleIdentifier</key> " \
           "    <string>{0}</string> " \
           "    <key>CFBundleName</key> " \
           "    <string>{1}</string>" \
           "    <key>DocSetPlatformFamily</key>" \
           "    <string>{2}</string>" \
           "    <key>isDashDocset</key>" \
           "    <true/>" \
           "    <key>dashIndexFilePath</key>" \
           "    <string>index.html</string>" \
           "</dict>" \
           "</plist>".format(name, name, name)
    open(docset_name + '/Contents/info.plist', 'wb').write(info)


if __name__ == '__main__':

    db = sqlite3.connect(docset_name + '/Contents/Resources/docSet.dsidx')
    cur = db.cursor()
    try:
        cur.execute('DROP TABLE searchIndex;')
    except:
        pass
    cur.execute('CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);')
    cur.execute('CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);')

    # start
    add_docs()
    add_infoplist()

    # commit and close db
    db.commit()
    db.close()
