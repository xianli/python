import sys
import StringIO
import re
import logging
import datetime
sys.path.append('/home/work/xl/spider/pycurl/lib/python2.7/site-packages/')
import pycurl
#init curl

if len(sys.argv)!=2 :
	print 'usage python get_price.py device_file'
	sys.exit()	

#init logger
logger = logging.getLogger()
loghandler = logging.FileHandler( "./log/spider_%s.log" % datetime.datetime.now().date() )
logformat = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
loghandler.setFormatter(logformat)
logger.addHandler(loghandler)
logger.setLevel(logging.NOTSET)

def get(url) :
	'''get a web page,  retry 3 times on fail'''
	failcount=0
	while (failcount<3):
		try:
			logger.info("get "+url)
			c=pycurl.Curl()
			c.setopt(c.HTTPHEADER, ["Accept: text/html;q=0.9,*/*;q=0.8",
					"Accept-Language: zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3",
					"Connection: keep-alive"])
			c.setopt(c.USERAGENT, 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36')
			b = StringIO.StringIO()
			c.setopt(c.WRITEFUNCTION, b.write)
			c.setopt(c.FOLLOWLOCATION, 5)
			c.setopt(c.URL, url) 
			c.perform()
			html=b.getvalue()
			b.close()
			c.close()	
			return html
		except Exception as e:
			logger.error(e)
			faile_count = fail_count + 1 
	return None 

def parser(html, pattern, model):
	'''get price for model by extracting pattern in html'''
	if (html == None):
		return -1
	ms = pattern.finditer(html)
	prices=[]
	for m in ms:
		prices.append(int(m.group(1)))
	if (len(prices)==0) :
		logger.warn("no price for "+model)
		return -1
	prices.sort()
	#get the median value
	price=prices[len(prices)/2]
	logger.info( model +":" + str(price))
	return price
	
#init pattern
etao_pattern=re.compile(r"<span class=\"price\">.*?(\d+).*?</span>", re.I )
etao_url="http://s.etao.com/search?q={0}&cat=50080001"
shop139_pattern = re.compile(r"<dd class=\"Price\"><font color=red>.*?</font>.*?(\d+).*?</dd>", re.I)
shop139_url="http://mobile.139shop.com/brand/0/0_0_0-0-0-0-0-0_{0}_001_1.htm"


#uncomment for debug parser function
#f = open("result")
#html=f.read()
f = open(sys.argv[1])
for line in f:
	line = line.strip('\n')
	origin = line
	if (line != 'other'):
		line = line.replace(",", "%20")
		model = line.replace(" ", "%20")
		
		#get price from etao
		html = get(etao_url.format(model))
		price = parser(html, etao_pattern, model)
		
		if price == -1:
			html = get(shop139_url.format(model))
			price = parser(html, shop139_pattern, model)
		print origin+"\t"+str(price)
