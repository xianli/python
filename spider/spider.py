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
		self.retries=int(parser.get("crawler","retries"))
		self.root_data_path=parser.get("data", "save_path")

	def get_by_curl(self, url , save=None):
		failcount=0
		while (failcount<self.retries):
			try:
				logger.info("get "+url)
				c=pycurl.Curl()
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
					write2file(save, html)
				b.close()
				c.close()	
				return html
			except Exception as e:
				logger.error(e)
				traceback.print_exc()
				failcount = failcount + 1 
				time.sleep(10)
		return None 

	def download_image(self, imageurl, savename):
		failcount=0
		while (failcount<self.retries):
			try:
				logger.info("get "+url)
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
			except Exception as e:
				logger.error(e)
				traceback.print_exc()
				failcount = failcount + 1 
				time.sleep(10)
		return None 


	def wget(url, save):
		command = "wget -O {1} -- {0}".format(url, save)
		os.system(command)
	
	def write2file(filepath, content):
		f = open(filepath, "w")
		f.write(content)
		f.close()

	def crawler(self):
		pass

	def udpate(self):
		pass

class TvplaySpider(VideoSpider)	:

	def __init__(self, logger, start, area):
		VideoSpider.__init__(logger)	
		self.root_page={"page":"http://video.baidu.com/commonapi/tvplay2level/?order=pubtime&start=%s&area=%s&pn=%s", "update_page":"http://video.baidu.com/commonapi/tvplay2level/?order=pubtime&pn=%s"}
		self.second_pages={"episode":"http://video.baidu.com/tv_intro/?dtype=tvEpisodeIntro&service=json&id=%s","playurl":"http://video.baidu.com/tv_intro/?dtype=tvPlayUrl&service=json&id=%s", "recommend":"http://video.baidu.com/tv_intro/?dtype=tvCombine&service=json&id=%s","periphery":"http://video.baidu.com/tv_intro/?dtype=tvPeriphery&service=json&id=%s"}
		self.record_file=self.root_data_path+"/tvplay.rec"
		self.save_path=self.root_data_path+"/tvplayindex"
		self.end=112
		
		self.pattern_intro=re.compile(r"<input type=\"hidden\" value=\"(.*?)\" name=\"longIntro\"/>")

		#read record file 	
		frec=open(self.record_file)
		rec=json.load(frec)
		frec.close();

	def crawler(self, start, area):
		'''crawler the all videos at the begining'''
		current=int(rec["current_page"])
		count=0
		for s in start :
			for a in area:
				 for i in range (current, self.end):
						url = self.root_page["page"] % (s,a,i)
						save = full_path("page", "%s_%s_%s"%(s, a, i))
						content = self.get_by_curl(url, save)
						video_json = json.loads(content)
						video_num = video_json["videoshow"]["video_num"]
						for j in range(1, video_num):
							video = video_json["videoshow"]["videos"][j]
							download_video(video)
							rec["current_page"]=i
							#save record file 
							count = count+1
							if (count == 50):
								json.dumps(rec, open(self.record_file))

						
	def update(self, check_pages):
		'''call this method after crawler done, this will get new videos incrementally'''
	 	for i in range (1, check_pages):
			url = self.root_page["update_page"] % (i)
			save = full_path("update_page", i)
			content = self.get_by_curl(url, save)
			video_json = json.loads(content)
			video_num = video_json["videoshow"]["video_num"]
			for j in range(1, video_num):
				video = video_json["videoshow"]["videos"][j]
				video_id = video["id"]
				download_video(video)
				#dump the new video json object
				if video_id not in self.rec.keys:
					json.dumps(video, open(fullpath("update_page", video_id)))

						
	def download_video(self,video):
			try :
				video_id = video["id"]
				big_image_url = video["imgh_url"]
				small_image_url = video["imgv_url"]
				detail_url = video["url"]
				epi=0
				m = re.match(r".*(\d+).*",  video["update"])
				if m:
					epi_num=re.group(1)
				to_run = False
				if video_id not in rec.keys:	
					to_run = True
				elif int(self.rec[video_id][episodes]) < epi_num:
					#compare the episodes num 
					to_run = True 

				if to_run:
					# download required information 
					playurl=self.get_video_part(video_id)
					self.get_play_site(video_id, json.loads(playurl))
					self.get_video_intro(detail_url)
					self.download_image(small_image_url, full_path("image_big", video_id))
					self.download_image(big_image_url, full_path("image_small", video_id))
					#all are downloaded, add it to old list 
					self.rec[video_id]="{page:%s, episodes:%s}" % (i, epi_num)
					
			except Exception as e:
				self.rec.dump(rec, open(self.record_file))
				traceback.print_exc()
				logger.error(e)	
	
	def get_video_part(self, id):
		ret=""	
		for (save, url) in self.second_pages:
			url = url % id
			html=self.get_by_curl(url, full_path(save, id))
			if save=='playurl':
				ret = html
		return ret

	def get_video_intro(self, id, url):
		'''extract introduction in detail page'''
		html=get_by_curl(url)
		ms = self.pattern_intro.finditer(html)
		if ms:
			for m in ms:
				introduction=ms.group(1)
				self.write2file(full_path("intro", id), introduction)
		

	def get_play_site(self, id, playurls):
		for playsite in playurls:
			episodes=playsite["episodes"]
			for episode in episodes:
				title=episode["single_title"]
				url=episode["url"]
				epi=episode["episode"]
				isplay=episode["is_play"]
				siteorder=episode["site_order"]
				siteurl=episode["site_url"]
				html=self.get_by_curl(url)
				

	def full_path(name, id)	:
		return "%s/%s/%s" % (self.save_path, name, id)

'''
class MovieSpider(VideoSpider):

class CartoonSpider(VideoSpider):

class TvshowSpider(VideoSpider):
'''
if __name__ == "__main__" :

	
	if (len(sys.argv)!=3):
		print "usage: python spider.py spider.conf [crawler|update]"
	else: 
		#init logger
		logger = logging.getLogger()
		loghandler = logging.FileHandler( "./log/%s.log" % datetime.datetime.now().date() )
		logformat = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
		loghandler.setFormatter(logformat)
		logger.addHandler(loghandler)
		logger.setLevel(logging.NOTSET)
		#process argv
		parser = ConfigParser.ConfigParser()
		parser.read(sys.argv[1])
		spider_name=parser.get("crawler", "name")
		start = parser.get("crawler","start")
		area = parser.get("crawler","area")
	
		scan_pages = int(parser.get("update", "scan_pages")
		st = [item.strip('') for item in start.strip('\n').split(',') ]
		ar = [item.strip('') for item in area.strip('\n').split(',') ]
		#init spider
		spider = None
		if (spider.name=="tvplay")	:
			spider = TvplaySpider(logger)
		elif (spider.name=="movie"):
			spider = MovieSpider(logger)
		elif (spider.name=="cartoon"):
			spider = CartoonSpider(logger)
		elif (spider.name=="tvshow"):
			spider = TvshowSpider(logger)

		if spider:
			if (sys.argv[2]=="update"):
				spider.update(scan_pages)
			elif (sys.argv[2]=="crawler"):	
				spider.crawler(st, ar)
