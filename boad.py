#!/usr/bin/env python
from pyquery import PyQuery
from dateutil import parser
import mechanize,cookielib,json,os,eyed3,argparse,subprocess
import boto
from boto.s3.key import Key


class BOAD:
    def __init__(self):
        self.username = os.environ.get('BOAD_USERNAME', '')
        self.password = os.environ.get('BOAD_PASSWORD', '')
        self.bucket_name = os.environ.get('AWS_BUCKET')
        self.base_url = 'http://www.bigoanddukes.com'
        self.login_url = '/reloaded'
        self.list_url ='/index.asp?bid=13&pclPageNumber='
        self.page_number = 1
        self.mp3_path = './reloaded/'

    def login(self):
        cj = cookielib.LWPCookieJar()
        br = mechanize.Browser()
        br.set_cookiejar(cj)
        br.set_handle_equiv(True)
        br.set_handle_redirect(True)
        br.set_handle_referer(True)
        br.set_handle_robots(False)
        br.follow_meta_refresh = True
        br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
        br.open('%s%s' % (self.base_url ,self.login_url))
        br.select_form(nr=0)
        form = [x for x in br.forms()][0]
        usr = form.find_control(id='LoginUsernameInput')
        br[usr.name] = self.username
        pwd = form.find_control(type='password')
        br[pwd.name] = self.password
        br.submit()
        return br

    def get_page(self, page_number):
        """
            parses a page on bigoanddukes.com and grabs info
            about the podcasts.
            TODO: also grab the episode image
        """
        eps = []
        br = self.login()
        html = br.open('%s%s' % (self.list_url, page_number or self.page_number)).get_data()
        d = PyQuery(html)
#        print [(dir(x), x.getchildren()) for x in d("#latest-podcast-wrapper")]
        for div in d('#latest-podcast-wrapper'):
            children = div.getchildren()
#            print [x.tag for x in children[0].getchildren()]
#            print dir(children[0].getchildren()[1])
            title = children[0].getchildren()[1].text
            date = children[0].getchildren()[2].text
            mp3 = children[0].getchildren()[3].getchildren()[4].getchildren()[0].get("href")


#            print 'title:', title, 'date:', date, 'mp3:', mp3
            eps.append({'title' : title, 'date' : date, 'mp3' : mp3})

#        print [x.keys() for x in d(".downloadLink")]
        self.save_metadata(eps)

    def download(self):
        for ep in json.loads(open('./metadata.json').read()):
            if not os.path.exists('%s/%s' % (self.mp3_path, self._get_filename(ep.get('mp3')))):
                print '"%s" does not exist' % self._get_filename(ep.get('mp3'))
                self._download_file(ep.get('mp3'))
                print 'file downloaded, will set id3 tags'
                self._set_id3tags(ep)

    def _download_file(self, url):
        print('wget --directory-prefix=%s %s' % (self.mp3_path, url))
        os.popen('wget --directory-prefix=%s %s' % (self.mp3_path, url))

    def _get_filename(self, f):
        return f[f.rfind('/')+1:].strip()

    def _set_id3tags(self, ep):
        date = parser.parse(ep.get('date'))
        subprocess.call(['/usr/local/bin/eyeD3', '-a', 'Big O and Dukes Reloaded', '-t', '%s %s' % (date.strftime('%Y-%m-%d'), ep.get('title')), '%s/%s' % (self.mp3_path,  self._get_filename(ep.get('mp3'))) ])

    def save_metadata(self, eps):
        already = json.loads(open('./metadata.json').read())
        all=[]
        for e in already:
            if not [x for x in eps if x["date"] == e["date"]]:
                all.append(e)
        all += eps
        with open('./metadata.json', 'w') as f:
            f.write(json.dumps(all, indent=4))

    def get_eps(self):
        afs = []
        for m in [x for x in os.listdir(self.mp3_path) if 'mp3' in x.lower()]:
            af = eyed3.load('%s/%s' % (self.mp3_path, m))
            if af.tag.title != '':
                afs.append(af)
        return sorted([(x.tag.title, {'title':x.tag.title, 'filename':x.path, 'audiofile':x}) for x in afs], reverse=True)
        
    def get_s3_eps(self):
        conn = boto.connect_s3()
        bucket = conn.get_bucket(self.bucket_name)
        return sorted([key.key for key in bucket.list()], reverse=True)
            
            
        
    def upload_to_s3(self, overwrite=False):
        conn = boto.connect_s3()
        bucket = conn.get_bucket(self.bucket_name)
        for ep in self.get_eps():
            if not bucket.get_key(ep[0]):
                key = Key(bucket)
                key.key = ep[0]
                key.set_contents_from_filename(ep[1]['filename'])

if __name__=='__main__':
#    parser = argparse.ArgumentParser()
#    parser.add_argument('--foo', help='foo help')
#    subparsers = parser.add_subparsers(title="subcommands")
#    subparsers.add_parser('web')
#    subparsers.add_parser('fetch')#, aliases=['fe'])

#    args = parser.parse_args()



    boad = BOAD()
    boad.get_page(1)
    boad.download()
