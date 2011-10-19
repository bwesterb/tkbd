""" Loads occupation from www.ru.nl/pc-zalen/bezetting.aspx """

import urllib2

from BeautifulSoup import BeautifulSoup, NavigableString

BEZETTING_URL = 'https://www.ru.nl/pc-zalen/bezetting.aspx?orgname=fnwi'

def parse_bezetting(txt):
        """ From the HTML page, extract the occupation """
        ret = {}
        page = BeautifulSoup(txt)
        table = page('table', {
                'id': 'ctl00_ContentPlaceHolder1_TableFacilityInfo'})[0]
        for c in table:
                if isinstance(c, NavigableString):
                        continue
                assert c.name == 'tr'
                if c['class'] in ('header', 'footer'):
                        continue
                free = 0
                occupied = 0
                what = None
                for td in c('td'):
                        if len(td) == 0:
                                continue
                        cnt = td.contents[0]
                        if not isinstance(cnt, NavigableString):
                                continue
                        try:
                                if td['class'] == 'occupied':
                                        occupied = int(cnt)
                                elif td['class'] == 'free':
                                        free = int(cnt)
                                else:   
                                        assert False
                        except KeyError:
                                what = cnt
                ret[normalize_room_name(what)] = (free, occupied)
        return ret

def normalize_room_name(name):
        """ eg.: 'HG00.149 (pc-onderwijsruimte)' -> 'HG00.149' """
        return name.split(' ')[0].upper()

def scrape_bezetting():
        """ Returns a dictionary
                { <room> : ( <free pcs>, <used pcs> ) } """
        return parse_bezetting(urllib2.urlopen(BEZETTING_URL).read())

if __name__ == '__main__':
        import pprint
        pprint.pprint(scrape_bezetting())
