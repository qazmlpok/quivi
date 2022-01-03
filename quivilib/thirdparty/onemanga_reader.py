from quivilib.thirdparty import httplib2
from quivilib.thirdparty.BeautifulSoup import BeautifulSoup
from wx.lib.pubsub import pub as Publisher
import re
BASE_URL = u"http://www.onemanga.com"
import logging as log

class OMPage(object):
    def __init__(self,episode,tag):
        self.conn = episode.conn
        self.episode = episode
        self.name = tag.string
        self._url = u"%s%s/" % (episode.url,tag['value'])
        self._img_url = None

    def getImgUrl(self):
        if self._img_url is None:
            log.debug('Requesting ' + self._url)
            page = self.conn.request(self._url,"GET")
            soup = BeautifulSoup(page[1])
            tag = soup.find('img','manga-page')
            self._img_url = tag['src']
        return self._img_url

    def show(self):
        import webbrowser
        webbrowser.open(self._img_url)

    def __repr__(self):
        return u"OMPage(Page %s of %s)" % (self.name,self.episode.name)

    url = property(getImgUrl,None,None,"Image of page.")


class OMEpisode(object):
    def __init__(self,conn,tag):
        self.conn = conn
        self.name = tag.string
        self.url = u"%s%s" % (BASE_URL, tag['href'])
        self._pages = None

    def getPages(self):
        if self._pages is None:
            log.debug('Requesting ' + self.url)
            page = self.conn.request(self.url,"GET")
            soup = BeautifulSoup(page[1])
            url = soup.find('ul').find('a')['href']
            url = u'%s%s' % (BASE_URL, url)
            log.debug('Requesting ' + url)
            page = self.conn.request(url, "GET")
            soup = BeautifulSoup(page[1])
            select = soup.find('select', 'page-select')
            self._pages = [ OMPage(self,tag) for tag in select.findChildren() ]
        return self._pages

    def __getitem__(self,i):
        return self.pages[i]

    def __len__(self):
        return len(self.pages)

    def __repr__(self):
        if self._pages is None:
            return u"OMEpisode(%s)" % self.name
        return u"OMEpisode(%s, %s pages)" % (self.name,len(self) or "???")

    pages = property(getPages,None,None,"Pages of manga.")


class OMSeries(object):
    def __init__(self, conn, name, url):
        self.conn = conn
        self.name = name.replace('/', '-')
        self.url = u"%s/%s/" % (BASE_URL, url)
        self._episodes = None

    def getEpisodes(self):
        if self._episodes is None:
            log.debug('Requesting ' + self.url)
            soup = BeautifulSoup(self.conn.request(self.url,"GET")[1])
            tds = soup.findAll('td','ch-subject')
            tags = [ x.findChild() for x in tds ]
            self._episodes = [ OMEpisode(self.conn,tag) for tag in tags ]
            self._episodes.reverse()
        return self._episodes

    def __getitem__(self,i):
        return self.episodes[i]

    def __len__(self):
        return len(self.episodes)

    def __repr__(self):
        if self._episodes is None:
            return u"OMSeries(%s)" % self.name
        return u"OMSeries(%s, %s episodes)" % (self.name,len(self))

    episodes = property(getEpisodes,None,None,"Manga episodes.")


class OMReader(object):
    def __init__(self, temp_dir):
        self.conn = httplib2.Http(temp_dir / '.cache')
        self._series = None

    def getSeries(self):
        if self._series is None:
            front = self.conn.request(u"http://om-content.onemanga.com/content-data.js", "GET")
            text = front[1]
            matches = re.findall(r'\["([^"]*)",' + r'"([^"]*)"', text)
            self._series = [OMSeries(self.conn, name, url) for name, url in matches]

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
            return u"OMReader(%s/)" % BASE_URL
        return u"OMReader(%s/, %s series)" % (BASE_URL, len(self))

    series = property(getSeries,None,None,"Manga series.")
    
if __name__ == '__main__':
    r = OMReader()
    s = r['Bakuman']
    e = s[0]
    e.pages
