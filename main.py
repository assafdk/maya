from email_module import emailsender
import rss
import untangle, requests
dividend_msg_str = ""
maya_url = "https://maya.tase.co.il/rss/maya.xml"
str_to_find = ["שפע"]
subscribers_email_list = ["assafdk@gmail.com","guyhilb@gmail.com", "barakalon13@gmail.com"]
rss_obj = rss.WhizRssAggregator(maya_url, str_to_find)
dividend_msg_str = rss_obj.parse()

# header = u'Here is your dividend alert from HaLevi AlgoTrading:\n'
# header = u"הנה התראות הדיבידנד שלך מיהודה הלוי אלגוטריידינג:\n".encode('utf-8')
header = """Here is your dividend alert from HaLevi AlgoTrading"""
email_obj = emailsender(header, dividend_msg_str, subscribers_email_list)
email_obj.send()
