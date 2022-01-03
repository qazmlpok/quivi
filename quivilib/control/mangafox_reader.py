from quivilib.thirdparty import httplib2
from quivilib.thirdparty.BeautifulSoup import BeautifulSoup
from wx.lib.pubsub import pub as Publisher
import re
import string
from quivilib.thirdparty.path import path
BASE_URL = u"http://www.mangafox.com"

class MFPage(object):
    def __init__(self,episode,name,url):
        self.conn = episode.conn
        self.episode = episode
        self.name = name
        self._url = url
        self._img_url = None

    def getImgUrl(self):
        if self._img_url is None:
            page = self.conn.request(self._url,"GET")
            soup = BeautifulSoup(page[1])
            tag = soup.find('div', {'id': 'viewer'}).find('img')
            self._img_url = tag['src']
        return self._img_url

    def show(self):
        import webbrowser
        webbrowser.open(self._img_url)

    def __repr__(self):
        return u"MFPage(Page %s of %s)" % (self.name,self.episode.name)

    url = property(getImgUrl,None,None,"Image of page.")


class MFEpisode(object):
    def __init__(self,conn,name,url):
        self.conn = conn
        self.name = name
        self.url = u"%s/%s" % (BASE_URL, url)
        self._pages = None

    def getPages(self):
        if self._pages is None:
            page = self.conn.request(self.url, "GET")
            soup = BeautifulSoup(page[1])
            tags = soup.find('select', 'middle').findChildren()
            self._pages = [ MFPage(self, tag.string, self.url + '/' + tag['value'] + '.html') for tag in tags]
        return self._pages

    def __getitem__(self,i):
        return self.pages[i]

    def __len__(self):
        return len(self.pages)

    def __repr__(self):
        if self._pages is None:
            return u"MFEpisode(%s)" % self.name
        return u"MFEpisode(%s, %s pages)" % (self.name,len(self) or "???")

    pages = property(getPages,None,None,"Pages of manga.")


class MFSeries(object):
    def __init__(self, conn, name, url):
        self.conn = conn
        self.name = name
        self.url = u"%s/%s?no_warning=1" % (BASE_URL, url)
        self._episodes = None

    def getEpisodes(self):
        if self._episodes is None:
            soup = BeautifulSoup(self.conn.request(self.url,"GET")[1])
            tags = soup.find('table', {'id': 'listing'}).findAll('a','chico')
            self._episodes = [ MFEpisode(self.conn, re.sub('\s+', ' ', tag.string), tag['href']) for tag in tags ]
        return self._episodes

    def __getitem__(self,i):
        return self.episodes[i]

    def __len__(self):
        return len(self.episodes)

    def __repr__(self):
        if self._episodes is None:
            return u"MFSeries(%s)" % self.name
        return u"MFSeries(%s, %s episodes)" % (self.name,len(self))

    episodes = property(getEpisodes,None,None,"Manga episodes.")


class MFLetterSeries(object):
    def __init__(self, conn, name):
        self.conn = conn
        self.name = name
        self._series = None

    def getSeries(self):
        if self._series is None:
            front = self.conn.request(u"%s/directory/%s/" % (BASE_URL, self.name.lower()), "GET")
            soup = BeautifulSoup(front[1])
            tags = soup.findAll('a', {'class': re.compile('manga_(open|close)')})
            
            a_tags = soup.find('div', {'id':'nav'}).findAll('a')
            if a_tags:
                for a_tag in a_tags[0:-1]:
                    front = self.conn.request(u"http://www.mangafox.com/directory/%s/%s" % (self.name.lower(), a_tag['href']), "GET")
                    soup = BeautifulSoup(front[1])
                    ntags = soup.findAll('a', {'class': re.compile('manga_(open|close)')})
                    tags += ntags
            
            self._series = [MFSeries(self.conn, tag.string, tag['href']) for tag in tags]

        return self._series

    def __len__(self):
        return len(self.series)

    def __getitem__(self,i):
        typ = type(i)
        if typ == str or typ == unicode:
            for serie in self.series:
                if serie.name.lower() == i.lower():
                    return serie
        return self.series[i]

    def __repr__(self):
        if self._series is None:
            return u"MFReader(%s/%s/)" % (BASE_URL, self.name)
        return u"MFReader(%s/%s/, %s series)" % (BASE_URL, self.name, len(self))

    series = property(getSeries,None,None,"Manga series.")
    
class MFReader(object):
    def __init__(self, temp_dir):
        self.conn = httplib2.Http(temp_dir / '.cache')
        self._letters = None

    def getLetters(self):
        if self._letters is None:
            self._letters = [MFLetterSeries(self.conn, letter,) for letter in
                             '9' + string.ascii_uppercase]
        return self._letters

    def __len__(self):
        return len(self.letters)

    def __getitem__(self, i):
        typ = type(i)
        if typ == str or typ == unicode:
            for letter in self.letters:
                if letter.name.lower() == i.lower():
                    return letter
        return self.letters[i]

    def __repr__(self):
        if self._letters is None:
            return u"MFReader(%s/)" % BASE_URL
        return u"MFReader(%s/, %s letters)" % (BASE_URL, len(self))

    letters = property(getLetters, None, None)
    
if __name__ == '__main__':
    r = MFReader(path('.'))
    print r.letters
    l = r['a']
    print l.series
    s = l[1]
    print s.episodes
    p = s[1]
    print p.pages
    i = p[1]
    print i.url

