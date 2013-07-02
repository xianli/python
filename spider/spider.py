# -*- coding: utf-8 -*-
import sys
import StringIO
import re
import logging
import datetime
import time
import json
import os
import ConfigParser
import logging
import traceback
sys.path.append("/home/work/xl/spider/pycurl/lib/python2.7/site-packages/")
import pycurl

class VideoSpider() :

	def __init__(self, logger):
		self.logger=logger
		parser = ConfigParser.ConfigParser()
		parser.read("crawler.conf")
			
		self.interval=int(parser.get("crawler", "interval"))
		self.interval_on_error=int(parser.get("crawler", "interval_on_error"))
		self.interval_dump_record = int(parser.get("crawler","interval_dump_record"))
		self.retries=int(parser.get("crawler","retries"))
		self.root_data_path=parser.get("data", "root_path")
		
		self.debug= True if int(parser.get("crawler","debug"))==1 else False
		

	def get_by_curl(self, url , save=None):
		if self.debug:
			sys.stdin.readline()
		if not self.debug:
			time.sleep(self.interval)
		failcount=0
		while (failcount<self.retries):
			try:
				self.logger.info("%s==>%s" % (url,save))
				c=pycurl.Curl()
				c.setopt(c.ENCODING, 'gzip,deflate,sdch')
				c.setopt(c.REFERER, "http://video.baidu.com")
				c.setopt(c.HTTPHEADER, ["Accept: text/html;q=0.9,*/*;q=0.8",
						"Accept-Language: zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3",
						"Connection: keep-alive"])
				c.setopt(c.USERAGENT, "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36")
				b = StringIO.StringIO()
				c.setopt(c.WRITEFUNCTION, b.write)
				c.setopt(c.FOLLOWLOCATION, 5)
				c.setopt(c.URL, str(url))
				c.perform()
				html=b.getvalue()
				if save:
					self.write2file(save, html)
				b.close()
				c.close()	
				return html
			except Exception as e:
				self.logger.error(e)
				traceback.print_exc()
				failcount = failcount + 1 
				time.sleep(self.interval_on_error)
		return None 

	def download_image(self, imageurl, savename):
		failcount=0
		while (failcount<self.retries):
			if self.debug:
				sys.stdin.readline()
			try:
				self.logger.info(imageurl+"==>"+savename)
				c=pycurl.Curl()
				c.setopt(c.HTTPHEADER, ["Accept: text/html;q=0.9,*/*;q=0.8",
						"Accept-Language: zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3",
						"Connection: keep-alive"])
				c.setopt(c.USERAGENT, "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36")
				f=open(savename,"w")
				c.setopt(c.WRITEDATA, f)
				c.setopt(c.REFERER, "http://video.baidu.com")
				c.setopt(c.FOLLOWLOCATION, 5)
				c.setopt(c.URL, str(imageurl))
				c.perform()
				c.close()	
				f.close()
				return True
			except Exception as e:
				self.logger.error(e)
				traceback.print_exc()
				failcount = failcount + 1 
				time.sleep(self.interval_on_error)
		return None 


	def wget(self, url, save=None):
		if self.debug:
			print url 
			sys.stdin.readline()
		command = "wget -O {1} -- {0}".format(url, save)
		os.system(command)
	
	def write2file(self, filepath, content):
		f = open(filepath, "w")
		f.write(content)
		f.close()

	def crawler(self, start, area):
		'''crawler all videos at the begining'''
	
		count=0
		#restore form previous crawler with parameter area, start
		si = int(self.rec["start"]) 
		ai = int(self.rec["area"])
		#for s in start :
		#	if self.rec["start"] != "" and s != self.rec["start"]:
		#		si = si + 1
		#		continue
		#	for a in area:
		#		if self.rec["area"] != "" and a != self.rec["area"]:
		#			ai = ai + 1
		#			continue
		current = self.rec["current_page"]
		while (si<len(start)):
			s = start[si]
			self.rec["start"]=si
			while (ai<len(area)):
				a=area[ai]
				self.rec["area"]=ai
				i = current	
				last_confidence=1
				while True:
					url = self.root_page["page"] % (s,a,i)
					save = self.full_path("page", str("%s_%s_%s"%(s, a, i)))
					content = self.get_by_curl(url, save)
					video_json = json.loads(content)
					if len(video_json["videoshow"])==0:
						last_confidence = last_confidence + 1
						if last_confidence==3:
							self.logger.info("try last page 3 times for %s, %s, %s" %(s, a, i))
							break		
						else:
							continue
					video_num = video_json["videoshow"]["video_num"]
					for j in range(1, video_num):
						video = video_json["videoshow"]["videos"][j]
						self.download_video(video)
						self.rec["current_page"]=i
						#save record file 
						count = count+1
						if (count == self.interval_dump_record):
							json.dump(self.rec, open(self.record_file, "w"))
					i = i + 1
				ai = ai + 1
			si = si + 1

						
	def update(self, check_pages):
		'''call this method after crawler done, this will get new videos incrementally'''
	 	for i in range (1, check_pages):
			url = self.root_page["update_page"] % (i)
			save = self.full_path("update_page", i)
			content = self.get_by_curl(url, save)
			video_json = json.loads(content)
			video_num = video_json["videoshow"]["video_num"]
			for j in range(1, video_num):
				video = video_json["videoshow"]["videos"][j]
				video_id = video["id"]
				download_video(video )
				#dump the new video json object
				if video_id not in self.rec.keys():
					json.dump(video, open(fullpath("update_page", video_id)), "w")

	
	def regex_extract(self, pattern, string, index):
		items = pattern.finditer(string)
		mat = ""
		for item in items:
			mat = item.group(index)
		return mat	

	def full_path(self, name, id)	:
		path = "%s/%s/%s" % (self.save_path, name, id)
		dirname = os.path.dirname(path)
		if  not os.path.exists(dirname):
			os.mkdir(dirname)
		return path

class TvplaySpider(VideoSpider)	:

	def __init__(self, logger, start, area):
		VideoSpider.__init__(self, logger)	
		self.root_page={"page":"http://video.baidu.com/commonapi/tvplay2level/?order=pubtime&start=%s&area=%s&pn=%s", "update_page":"http://video.baidu.com/commonapi/tvplay2level/?order=pubtime&pn=%s"}
		self.second_pages={"episode":"http://video.baidu.com/tv_intro/?dtype=tvEpisodeIntro&service=json&id=%s","playurl":"http://video.baidu.com/tv_intro/?dtype=tvPlayUrl&service=json&id=%s", "recommend":"http://video.baidu.com/tv_intro/?dtype=tvCombine&service=json&id=%s","periphery":"http://video.baidu.com/tv_intro/?dtype=tvPeriphery&service=json&id=%s"}
		self.record_file=self.root_data_path+"/tvplay.rec"
		self.save_path=self.root_data_path+"/tvplayindex"
		
		self.pattern_intro=re.compile(r"<input type=\"hidden\" value=\"(.*?)\" name=\"longIntro\"/>")
		self.pattern_iqiyi=re.compile(r"data-drama-vid=\"(.*?)\"")
		self.pattern_sohu=re.compile(r"vid=\"(\d+)\"")
		#self.pattern_pptv=re.compile(r"pid/(\d*?).js")				
		self.pattern_wasu=re.compile(r"<embed src=\"http://play.wasu.cn/(.*?).swf\"")

		#read record file 	
		if os.path.exists(self.record_file):
			frec=open(self.record_file)
			self.rec=json.load(frec)
			frec.close()
		else:
			self.rec=json.loads("{\"current_page\":1, \"start\":\"\", \"area\":\"\"}")
			json.dump(self.rec, open(self.record_file,"w"))
						

	def download_video(self,video):
			try :
				video_id = video["id"]
				big_image_url = video["imgh_url"]
				small_image_url = video["imgv_url"]
				detail_url = video["url"]
				epi_num=0
				m = re.match(r".*?(\d+).*?",  video["update"])
				if m:
					epi_num=m.group(1)
					self.logger.info("title: %s, episodes: %s" % (video["title"], str(epi_num)))
				to_run = False
				if video_id not in self.rec.keys():	
					to_run = True
				elif int(self.rec[video_id]["episodes"]) < epi_num:
					#compare the episodes num 
					to_run = True 
				self.logger.info("to run:" + str(to_run))
				if to_run:
					# download required information 
					self.get_tv_intro(video_id,detail_url)
					self.download_image(small_image_url, self.full_path("image_big", video_id))
					self.download_image(big_image_url, self.full_path("image_small", video_id))
					playurl=self.get_tv_parts(video_id)
					self.get_play_site(video_id, json.loads(playurl))
					#all are downloaded, add it to old list 
					self.rec[video_id]=epi_num
					
			except Exception as e:
				json.dump(self.rec, open(self.record_file, "w"))
				traceback.print_exc()
				self.logger.error(e)	
	
	def get_tv_parts(self, id):
		ret=""	
		for (save, url) in self.second_pages.items():
			url = url % id
			html=self.get_by_curl(url, self.full_path(save, id))
			if save=='playurl':
				ret = html
		return ret

	def get_tv_intro(self, id, url):
		'''extract introduction in detail page'''
		html=self.get_by_curl(url)
		ms = self.pattern_intro.finditer(html)
		if ms:
			for m in ms:
				introduction=m.group(1)
				self.write2file(self.full_path("intro", id), introduction)
		

	def get_play_site(self, id, playurls):
		#{19061_2_youku:''}
		playparam = dict()
		for playsite in playurls:
			episodes=playsite["episodes"]
			site_epi = dict()
			for episode in episodes:
				title=episode["single_title"]
				url=episode["url"]
				epi=episode["episode"]
				isplay=episode["is_play"]
				siteorder=episode["site_order"]
				siteurl=episode["site_url"]
				swf = ""
				if siteurl=="youku.com":	
					#http://v.youku.com/v_show/id_XNTcxODIzNTEy.html
					swf = "http://player.youku.com/player.php/sid/%s/v.swf" % url[-18:-5]
				elif siteurl=="tudou.com":
					#http://www.tudou.com/albumplay/iZ6TjiWzLbU/FVZFKAzJTbA.html
					swf = "http://www.tudou.com/a/%s/v.swf" % url[-28:-5]
				elif siteurl=="iqiyi.com":
					#http://www.iqiyi.com/dianshiju/20130628/7459ad8ec9562fc9.html
					html = self.get_by_curl(url)
					#extract drama_id
					swf = "http://player.video.qiyi.com/%s/%s.swf" % (self.regex_extract(self.pattern_iqiyi, html, 1), url[21:-5])
				elif siteurl=="letv.com":
					#http://www.letv.com/ptv/vplay/1996316.html
					swf = "id=%s" % url[-12:-5]
				elif siteurl=="ku6.com":
					#http://player.ku6.com/refer/PSB0bt6sdmb7UB6xNZsNVg../v.swf 
					swf = "vid=%s" % url[-29:-5]				
				elif siteurl=="qq.com":
					#http://v.qq.com/cover/x/xgnnne5is86cqh2/c0012bs0bij.html?ptag=baidu.video.tv
					swf = "http://static.video.qq.com/TPout.swf?vid=%s&auto=1" % url[-36:-25]
				elif siteurl=="sohu.com":
					#http://tv.sohu.com/20130624/n379618347.shtml
					html = self.get_by_curl(url)
					swf = "http://share.vrs.sohu.com/%s/v.swf&autoplay=false" % self.regex_extract(self.pattern_sohu, html, 1) 
				elif siteurl=="pps.tv":
					#http://v.pps.tv/play_369GGU.html#frombaidu
					swf = "http://player.pps.tv/player/sid/%s/v.swf" % url[21:27]
				#elif siteurl=="pptv.com":
					#http://v.pptv.com/show/CHvpZ881peNGxCw.html
				#	html = self.get_by_curl(url)
				#	swf = "pid=%s" % self.regex_extract(self.pattern_pptv, html, 1)
				elif siteurl=="56.com":
					#http://www.56.com/u28/v_OTE4MzcxNjk.html
					swf = "http://player.56.com/v_%s.swf" % url[-16:-5]
				elif siteurl=="wasu.cn":
					html = self.get_by_curl(url)
					swf = "http://play.wasu.cn/%s.swf" % self.regex_extract(self.pattern_wasu, html, 1)
				#elif siteurl=="funshion.com":
				#elif siteurl=="m1905.com":
				#elif siteurl=="kankan.com":
					#http://vod.kankan.com/v/70/70469/318343.shtml
				site_epi[epi]=swf
				playparam[siteurl]=site_epi
			json.dump(playparam, open(self.full_path("playparam", id), "w"))
	
			


class MovieSpider(VideoSpider):
	def __init__(self, logger, start, area):
		VideoSpider.__init__(self, logger)	
		self.root_page={"page":"http://video.baidu.com/commonapi/movie2level/?&order=pubtime&start=%s&area=%s&pn=%s", "update_page":"http://video.baidu.com/commonapi/movie2level/?order=pubtime&pn=%s"}
		self.second_pages={"comment":"http://video.baidu.com/movie_intro/?dtype=commentCombine&service=json&id=%s","recommend":"http://video.baidu.com/movie_intro/?dtype=movieCombine&service=json&id=%s","periphery":"http://video.baidu.com/movie_intro/?dtype=periphery&service=json&id=%s","playurl":"http://video.baidu.com/movie_intro/?dtype=playUrl&service=json&id=%s"}
		self.record_file=self.root_data_path+"/movie.rec"
		self.save_path=self.root_data_path+"/movieindex"
		self.end=112
		
		self.pattern_intro=re.compile(r"<input type=\"hidden\" value=\"(.*?)\" name=\"longIntro\"/>")
		self.pattern_iqiyi=re.compile(r"data-drama-vid=\"(.*?)\"")
		self.pattern_sohu=re.compile(r"vid=\"(\d+)\"")
		#self.pattern_pptv=re.compile(r"pid/(\d*?).js")				
		self.pattern_wasu=re.compile(r"<embed src=\"http://play.wasu.cn/(.*?).swf\"")

		#read record file 	
		if os.path.exists(self.record_file):
			frec=open(self.record_file)
			self.rec=json.load(frec)
			frec.close()
		else:
			self.rec=json.loads("{\"current_page\":1}")
			json.dump(self.rec, open(self.record_file,"w"))



def run(argv) :

	if (len(argv)!=3):
		print "usage: python spider.py spider.conf [crawler|update]"
	else: 
		#init logger
		logger = logging.getLogger()
		loghandler = logging.FileHandler( "./log/%s.log" % datetime.datetime.now().date() )
		logformat = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
		loghandler.setFormatter(logformat)
		logger.addHandler(loghandler)

	#	logger.addHandler(logging.StreamHandler())
		logger.setLevel(logging.NOTSET)
		#process argv
		parser = ConfigParser.ConfigParser()
		parser.read(argv[1])
		spider_name=parser.get("crawler", "name")
		start = parser.get("crawler","start")
		area = parser.get("crawler","area")
	
		scan_pages = int(parser.get("update", "scan_pages"))
		st = [item.strip('') for item in start.strip('\n').split(',')]
		ar = [item.strip('') for item in area.strip('\n').split(',')]
		#init spider
		spider = None
		if (spider_name=="tvplay"):
			spider = TvplaySpider(logger, st, ar)
		elif (spider_name=="movie"):
			spider = MovieSpider(logger, st, ar)
		elif (spider_name=="cartoon"):
			spider = CartoonSpider(logger, st, ar)
		elif (spider_name=="tvshow"):
			spider = TvshowSpider(logger, st, ar)

		if spider:
			if (argv[2]=="update"):
				spider.update(scan_pages)
			elif (argv[2]=="crawler"):	
				spider.crawler(st, ar)
			elif (argv[2]=="test"):
				json_video=json.load(open(spider.full_path("page", 1)))
				for i in range(1,18):
					spider.download_video( 
					json_video["videoshow"]["videos"][i])

if __name__ == "__main__" :
	run(sys.argv)	
