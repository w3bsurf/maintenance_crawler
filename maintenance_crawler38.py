import urllib.request
from html.parser import HTMLParser
import time
from multiprocessing import Process, Lock
import re
from collections import Counter

def crawler(url):
    """Return content from passed webpage."""
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    page = opener.open(url)
    content = page.read()
    content = content.decode('utf-8')

    return content

def remove_extra(text):
    """Removes characters not contained in keep."""
    keep = 'ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖabcdefghijklmnopqrstuvwxyzåäö%&.#@ '
    text = ''.join(list(filter(lambda x: x in keep, text)))
    text = re.sub(' +', ' ', text)

    return text

class HTMLStripper(HTMLParser):
    """From: https://www.semicolonworld.com/question/43039/strip-html-from-strings-in-python
    Strips HTML from text.
    Author: Sahil Kothiya """
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
        self.css = False

    def handle_starttag(self, tag, attrs):
        if tag == "style" or tag == "script":
            self.css = True

    def handle_endtag(self, tag):
        if tag=="style" or tag == "script":
            self.css = False

    def handle_data(self, d):
        if not self.css:
            self.fed.append(d)

    def get_content(self):
        return ''.join(self.fed)

def strip_html(html):
    """Remove HTML elements from content."""
    strip = HTMLStripper()
    strip.feed(html)
    content = strip.get_content()

    return content

def remove_common(text):
    """Removes words listed in the dictionary file from the text"""
    text = text.split(' ')
    filteredtext = ''

    try:
        file = open('dict_FIN.txt', 'r', encoding='utf-8')
    except Exception:
        print('Dictionary not found!')
        raise

    dictionary = file.readlines()
   
    for i in range(0, len(dictionary)):
        dictionary[i] = dictionary[i].split(' ')
        dictionary[i] = dictionary[i][1].rstrip('\n')

    for i in range(0, len(text)):
        if text[i].upper() not in dictionary:
            filteredtext = filteredtext + str(text[i]) + ' '

    file.close()

    return filteredtext

def word_counter(text, category=''):
    """Counts occurrence of words and sentences in text and returns list of unique items and a count for each item."""
    templist = []
    count = []
    uniquelist = []
    result = []

    if category == 'words':
    	textlist = text.split(' ')
    	textlist = list(filter(None, textlist))
    elif category == 'sentences':
        textlist = re.split('\n|([.])', text)
        textlist = list(filter(None, textlist))
    
    for i in range(0, len(textlist)):
        templist.append(textlist[i].upper())

    count = Counter(templist)

    for x in templist:
    	if x not in uniquelist:
    	    uniquelist.append(x)

    for i in range(0, len(uniquelist)):
    	result.append([uniquelist[i], str(count[uniquelist[i]])])

    print('Analysis complete, creating log.')

    return result

def write_put_log(content, lock):
    """Writes processed/parsed content from websites into put_log.txt."""
    try:
        try:
            lock.acquire()
            file = open('put_log_file.txt', 'a')
        except Exception:
            print('File write exception!')
            raise

    finally:
        lock.release()

    file.write(content)
    file.close()

def crawl_process(url, lock):
    """Calls approriate methods for each separate process during the crawl"""
    print('Working on:', url)
    html = crawler(url)
    content = strip_html(html)
    content = remove_extra(content)
    content = remove_common(content)
    write_put_log(content, lock)

def write_log(textlist, category=''):
    """Writes list of words/senteces into a file named: hour-day-month-year-output.csv."""
    fname = str(time.strftime('%H-%d-%m-%Y', time.localtime())) + '-' + category + '-output.csv'
    output = open('./outputs/' + fname, 'w')

    for i in range(0, len(textlist)):
        line = str(textlist[i][0]) + ';' + str(textlist[i][1] + '\n')
        output.write(line)

    output.close()
    print('Log ' + fname + ' written.')

def main():
    """Main Function."""
    lock = Lock()
    file = open('put_log_file.txt', 'w')
    file.close()

    try:
        urlfile = open('sources.txt', 'r')
        url_list = urlfile.readlines()
    except Exception:
        print('URL source file error')
        raise

    processes = []

    for i in range(0, len(url_list)):
        processes.append(Process(target = crawl_process, args = (url_list[i].rstrip('\n'), lock)))
        print('Started: ' + url_list[i].rstrip('\n'))

    for i in range(0, len(processes)):
        processes[i].start()

    for i in range(0, len(processes)):
        processes[i].join()

    print('Data collected, analyzing.')

    try:
        file = open('put_log_file.txt', 'r', encoding='latin1')
        content = file.read()
    except Exception:
        print('File read exception!')
        raise

    words = word_counter(content, category='words')
    write_log(words, category='words')
    sentences = word_counter(content, category='sentences')
    write_log(sentences, category='sentences')
    print('All done!')

if __name__ == '__main__':
    main()

