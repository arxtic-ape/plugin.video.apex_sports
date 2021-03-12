from resources.lib.modules import cache
from resources.lib.modules.log_utils import log
from resources.lib.modules import control
import requests
import re
try:
	from urllib.parse import urlencode
except:
	from urllib import urlencode

class info():
	def __init__(self):
		self.mode = 'streamlive'
		self.name = 'Streamlive.to'
		self.icon = 'streamlive.png'
		self.enabled = control.setting(self.mode) == 'true'
		self.paginated = False
		self.categorized = False
		self.multilink = False


class main():
	
	def __init__(self, url = 'https://www.streamlive.to/channels/?sort=1'):
		self.base = 'https://www.streamlive.to/'
		self.url = url

	def events(self):
		
		post_data = "page=1&category=&language=&sortBy=0&query=&list=all&itemspp=32&package="
		post_url = "https://www.streamlive.to/channelsPages-new-1.php"
		html = requests.post(post_url, data=post_data, headers={"X-Requested-With":"XMLHttpRequest"}).text
		try:
			html = html.decode('string_escape')
		except:
			html = html.encode('utf-8').decode('unicode_escape')
		channels = re.findall('data\-id\s*=\s*[\"\'](\d+).+?title\s*=\s*[\"\']([^\"\']+).+?original\s*=\s*[\"\']([^\"\']+)', html, flags=re.DOTALL)
		events = self.__prepare_channels(channels)
		return events


	def __prepare_channels(self,channels):
		new=[]
		def premium(ch):
			html = requests.get('https://www.streamlive.to/channel-player?n={}'.format(ch)).text
			return 'activate now' in html.lower()
		for channel in channels:
			if not cache.get(premium, 99999, channel[0]):
				new.append((channel[0], channel[1], 'https:' + channel[2].replace('\\/', '/')))
			
		return new



	def resolve(self,url):
		url = 'https://www.streamlive.to/channel-player?n={}'.format(url)
		from resources.lib.modules import liveresolver
		d = liveresolver.Liveresolver().resolve(url)
		if not d or d is None:
			return ' '
		if d['url'].startswith('plugin://'):
			return d['url']

		if d:
			return '{}|{}'.format(d['url'], urlencode(d['headers']))
		return ''
