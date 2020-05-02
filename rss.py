import feedparser

class WhizRssAggregator():
    feedurl = ""
    substrings_list = []

    def __init__(self, paramrssurl, substrings_list):
        print(paramrssurl)
        self.feedurl = paramrssurl
        self.substrings_list = substrings_list

    def parse(self):
        thefeed = feedparser.parse(self.feedurl)

        # print("Getting Feed Data")
        # print(thefeed.feed.get("title", ""))
        # print(thefeed.feed.get("link", ""))
        # print(thefeed.feed.get("description", ""))
        # print(thefeed.feed.get("published", ""))
        # print(thefeed.feed.get("published_parsed",
        #                    thefeed.feed.published_parsed))
        return_str = ""
        for thefeedentry in thefeed.entries:
            for substring in self.substrings_list:
                if (0 == thefeedentry.get("title", "").find(substring)):
                    return_str = '\n'.join((return_str,"__________", thefeedentry.get("title", ""), "__________"))
                # print(thefeedentry.get("guid", ""))
                # print(thefeedentry.get("title", ""))
                # print(thefeedentry.get("link", ""))
                # print(thefeedentry.get("description", ""))
                print(return_str)
        return return_str