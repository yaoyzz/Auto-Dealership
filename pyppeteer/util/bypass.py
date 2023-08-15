import random

@staticmethod
def generate_random_user_agent():
    platforms = [
        '(Windows NT 10.0; Trident/7.0; rv:11.0)',  # Less common Windows IE11
        '(Windows NT 10.0; WOW64; Trident/7.0; AS; rv:11.0)',  # Less common Windows IE11
        '(Windows NT 5.1; rv:7.0.1) Gecko/20100101 Firefox/7.0.1',  # Windows XP with Firefox 7
        '(Windows NT 6.0; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0',  # Windows Vista with Firefox 12
        '(X11; CrOS x86_64 8172.45.0)',  # Chrome OS
        '(Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/600.2.5 (KHTML, like Gecko) Version/6.2.2 Safari/537.85.11',  # Less common Mac OS X with Safari 6
        '(X11; Linux i686; rv:64.0) Gecko/20100101 Firefox/64.0',  # Linux with Firefox 64
        '(X11; OpenBSD amd64; rv:62.0) Gecko/20100101 Firefox/62.0',  # OpenBSD with Firefox 62
        '(Windows NT 5.1; rv:36.0) Gecko/20100101 Firefox/36.0',  # Windows XP with Firefox 36
        '(Windows NT 6.0; rv:34.0) Gecko/20100101 Firefox/34.0',  # Windows Vista with Firefox 34
        '(Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0',  # Windows 7 with Firefox 50
        '(Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0',  # Windows 10 with Firefox 78
        '(Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/534.59.8 (KHTML, like Gecko) Version/5.1.9 Safari/534.59.8',  # Mac OS X 10.6 with Safari 5
        '(Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.77.4 (KHTML, like Gecko) Version/6.1.5 Safari/537.77.4',  # Mac OS X 10.7 with Safari 6
        '(Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/600.8.9 (KHTML, like Gecko) Version/8.0.8 Safari/600.8.9',  # Mac OS X 10.10 with Safari 8
        '(Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15',  # Mac OS X 10.11 with Safari 11
        '(X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/31.0',  # Linux i586 with Firefox 31
        '(X11; Ubuntu; Linux i686; rv:15.0) Gecko/20100101 Firefox/15.0.1',  # Ubuntu with Firefox 15
        '(X11; Linux x86_64; rv:28.0) Gecko/20100101 Firefox/28.0',  # Linux x86_64 with Firefox 28
        '(X11; Fedora; Linux x86_64; rv:21.0) Gecko/20100101 Firefox/21.0'  # Fedora with Firefox 21
    ]
    
    browsers = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36',  # Chrome 96
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',  # Chrome 97
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0',  # Firefox 94
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0',  # Firefox 95
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36 Edg/96.0.1054.43',  # Edge 96
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 Edg/97.0.1072.62',  # Edge 97
    ]



    

    platform = random.choice(platforms)
    browser = random.choice(browsers)
    
    return f'Mozilla/5.0 {platform} {browser}'
