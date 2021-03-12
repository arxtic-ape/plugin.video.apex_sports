import requests
import re
from .modules import adhosts
from . import resolvers
from resources.lib.modules.log_utils import log
from resources.lib.modules.constants import USER_AGENT
from resources.lib.modules import control
import time
import threading
import ctypes
try:
	from urllib.parse import urlparse
except:
	from urlparse import urlparse  # Python 2


class Liveresolver:

	def __init__(self, headers = {'user-agent': USER_AGENT}):
		self.headers = headers	
		self.session = requests.Session()
		self.session.headers.update(headers)
		self.referer_map = {}

	def resolve(self, url):
		resolved = []
		t = Thread(self.__resolve, url, resolved)
		t.start()
		t1 = time.time()
		TIMEOUT = int(control.setting("resolver_timeout"))
		while t.is_alive():
			if ((time.time() - t1) > TIMEOUT):
				t.stop()
			time.sleep(0.5)
		t.join()
		try:
			u = resolved[0]
		except:
			u = None
		return u


	def __resolve(self, url):
		self.url = url
		self.url = self.url.replace('http:http:', 'http:')
		url = self.url
		self.referer_map[self.url] = ''

		#check if first url is resolvable
		try:
			html = self.session.get(self.url, timeout=10).text
		except Exception as e:
			log('Liveresolver: Error while trying to access {}: \n\n{}'.format(url,e))
			return None
	
		if len(resolvers.check(url, html)) > 0:
			resolved = resolvers.resolve(url, self.referer_map[url], self.referer_map)
			if resolved:
				return resolved
		iframes = self.__findIframes(self.url, links=[url])
		resolved = None
		for l in iframes:
			resolved = resolvers.resolve(l, self.referer_map[l], self.referer_map)
			if resolved:
				break
		
			
		return resolved
	
	def resolve_search(self, url):
		self.url = url
		self.url = self.url.replace('http:http:', 'http:')
		url = self.url
		self.referer_map[self.url] = ''
		
		#else go through iframes
		iframes = self.__findIframes(self.url, links=[url])
		resolved = None
		for l in iframes:
			resolved = resolvers.resolve(l, self.referer_map[l], self.referer_map)
			if resolved:
				break
		
			
		return resolved
		

	def __findIframes(self, url, links = [], checked = []):
		links = links
		checked = checked
		try:
			self.session.headers.update({'Referer': self.referer_map[url]})
		except:
			pass
		try:
			r = self.session.get(url, allow_redirects=True, timeout=10)
		except Exception as e:
			log('Liveresolver: Error while trying to access {}: \n\n{}'.format(url,e))
			return []

		if r.status_code == 200:
			urls = re.findall('i?frame\s*.+?src=[\"\']?([^\"\']+)', r.text, flags=re.IGNORECASE)
			urls = self.__customUrls(r.text, url, urls)
			for u in urls:
				if urlparse(u).netloc == '':
					if u.startswith('/'):	
						u = 'http://' + urlparse(url).netloc + '/' + u
					else:
						u = 'http://' + urlparse(url).netloc + '/'.join(urlparse(url).path.split('/')[:-1]) +  '/' + u
				if urlparse(u).scheme == '':
					u = 'http://' + u.replace('//','')


				u = re.sub(r'\n+', '', u)
				u = re.sub(r'\r+', '', u)
				
				if not adhosts.isAd(u) and u not in checked and self.__checkUrl(u) and u not in links:
					links.append(u)
					self.referer_map[u] = url 
					links += self.__findIframes(u, links, checked)
					checked.append(u)
			return list(set(links))
		return []

	def __checkUrl(self, url):
		blacklist = ['chatango', 'adserv', 'live_chat', 'ad4', 'cloudfront', 'image/svg', 'getbanner.php','/ads', 'ads.', 'adskeeper', '.js', '.jpg', '.png', '/adself.', 'min.js',
					'mail.ru']
		return not any(w in url for w in blacklist)

	def __customUrls(self, r, ref, urls):
		fid = re.findall('id\s*=\s*[\"\']([^\"\']+).+?jokersplayer.+?\.js', r)
		tiny = re.findall('href\s*=\s*[\"\']([^\"\']+).+?class\s*=\s*[\"\']btn\s*btn\-secondary', r)
		unes = re.findall('=\s*[\"\']([^\"\']+)[\"\']+[^\"\']+unescape', r)
		multiline = re.findall('i?frame\s*.+?src=[\"\']?([^\"\']+)', r, flags=re.IGNORECASE | re.DOTALL)
		telerium = re.findall('id\s*=\s*[\"\']([^\"\']+).+?embed.telerium.+?\.js', r)
		url_in_url = bool(re.search('streamlink\.slice\(4\)', r))
		us = []
		if len(fid) > 0:
			u = 'http://www.jokersplayer.xyz/embed.php?u=' + fid[0]
			self.referer_map[u] = ref
			us.append(u)

		if len(telerium) > 0:
			u = 'http://telerium.club/embed/' + telerium[0] +'.html'
			self.referer_map[u] = ref
			us.append(u)

		if len(tiny) > 0:
			urls.append(tiny[0])
			self.referer_map[tiny[0]] = ref

		if len(unes) > 0:
			u = unes[0].replace('@', '%')
			import urllib
			html = urllib.unquote(u).decode('utf8')
			try:
				u = re.findall('i?frame\s*.+?src=[\"\']?([^\"\']+)', html, re.IGNORECASE)[0]
				us.append(u)
				self.referer_map[u] = ref
			except:
				pass
		if len(multiline)>0:

			for u in multiline:
				us.append(u)
		if url_in_url:
			u = re.findall('\?.{3}([^$]+)', ref)[0]
			self.referer_map[u] = ref
			us.append(u)
		for u in us:
			if not adhosts.isAd(u) and self.__checkUrl(u) and u not in urls:
				urls.append(u)
		return urls

class Thread(threading.Thread):
	def __init__(self, func, url, out):
		self.func = func
		self.url = url
		self.out = out
		self._return = None
		threading.Thread.__init__(self)

	def run(self):
		try:
			resolved = self.func(self.url)
			self.out.append(resolved)
		except Exception as e:
		 	log(e)
		 	self.out.append(None)
		log(self.out)

	def get_id(self): 

		# returns id of the respective thread 
		if hasattr(self, '_thread_id'): 
			return self._thread_id 
		for id, thread in threading._active.items(): 
			if thread is self: 
				return id

	def stop(self):
		thread_id = self.get_id() 
		res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 
			  ctypes.py_object(SystemExit)) 
		if res > 1: 
			ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0) 
			print('Exception raise failure')