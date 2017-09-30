#!/usr/bin/python3

import requests
import imaplib
import email
import datetime
from bs4 import BeautifulSoup

mailString = 'email@yandex.ru';
mailPwd = 'password';

lostfilmLogin = 'email%40yandex.ru'; # replace @ to %40
lostfilmPwd = 'password';

#torrentPath = '/tmp/';
torrentPath = '/home/user/xbmc/torrent-files/';

def getNameForTorrrent():
    n = datetime.datetime.now();
    ret = torrentPath + '/';
    ret += n.strftime('%d-%m-%Y-%H:%M:%S');
    ret += '.torrent';
    return ret;

def saveToFile(_html):
    fn = "/tmp/log.htm"
    f = open(fn, "wb")
    f.write(_html)
    f.close()

def getRetreLink(_html):
    soup = BeautifulSoup(_html, 'lxml');
    linkElem = soup.find('a');
    link = linkElem.get('href');
    return link;

def getSdLink(_html):
    soup = BeautifulSoup(_html, 'lxml');
    linkElem = soup.findAll('a')[1];
    link = linkElem.get('href');
    return link;

def getJsTorrentLink(_html):
    soup = BeautifulSoup(_html, 'lxml');
    btnElem = soup.find('div', attrs={'class': 'external-btn'})
    onClick = btnElem.get('onclick');
    onClick = onClick[onClick.find('\''):];
    onClick = onClick[:onClick.find(')')];
    onClick = onClick.replace('\'', '');
    arr = onClick.split(',');
    if len(arr) != 3:
        return '';
    # "https://www.lostfilm.tv/v_search.php?c=321&s=1&e=10"
    ret = "https://www.lostfilm.tv/v_search.php?c="
    ret += str(arr[0]);
    ret += '&s=';
    ret += str(arr[1]);
    ret += '&e=';
    ret += str(arr[2]);
    print(ret)
    return ret;

def downloadFile(_url, _path):
    res = requests.get(_url);
    print("GET", res.url, res.status_code);
    if res.status_code != 200 :
    	return False;
    f = open(_path, 'wb');
    f.write(res.content);
    f.close();
    return True;

def downloadTorrent(_link, _path):
    s = requests.session()
    proxies = { 'http' : '127.0.0.1:8085', 'https' : '127.0.0.1:8085' }
    userAgent = { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0' }
    s.headers = userAgent;
    #s.proxies = proxies;
    #s.verify = False;

    form = { 'act': 'users', 'type': 'login',
             'mail': lostfilmLogin, 'pass': lostfilmPwd, 'rem': '0'  }
    res = s.post("https://www.lostfilm.tv/ajaxik.php", form);
    print("POST", res.url, res.status_code)
    saveToFile(res.content)
    if res.status_code != 200 :
        return False;    
    
    res = s.get(_link);
    print("GET", res.url, res.status_code)
    saveToFile(res.content)
    if res.status_code != 200 :
        return False;

    # преобразовать ссылку в формат "https://www.lostfilm.tv/v_search.php?c=321&s=1&e=10"
    jsLink = getJsTorrentLink(res.content)
    if len(jsLink) == 0:
        return False;

    res = s.get(jsLink);
    print("GET", res.url, res.status_code)
    saveToFile(res.content)
    if res.status_code != 200 :
        return False;
    
    retreLink = getRetreLink(res.content)
    res = s.get(retreLink);
    print("GET", res.url, res.status_code)
    saveToFile(res.content)
    if res.status_code != 200 :
        return False;

    sdLink = getSdLink(res.content);
    return downloadFile(sdLink, _path);
    
def getLinkFromMail(_html) :
    soup = BeautifulSoup(_html, "lxml")    
    links = soup.findAll('a')
    ret = links[-2].get('href')
    #ret = ret[1:]
    ret = ret[0:-1]
    return ret
    
def checkMail():
    mail = imaplib.IMAP4_SSL("imap.yandex.ru");
    mail.login(mailString, mailPwd);
    mail.list();
    mail.select("INBOX");

    result, data = mail.search(None,  '(UNSEEN)');
    ids = data[0];
    id_list = ids.split();
    for cur in id_list :
        latest_email_id = cur;

        result, data = mail.fetch(latest_email_id, "(RFC822)");
        raw_email = data[0][1];

        msg = email.message_from_bytes(raw_email);
        fr = msg['from'];
        if not "LostFilm.TV" in fr :
            continue;
        print("From: ", fr);
        for part in msg.walk() :
            body = part.get_payload();
            #print(body)
            link = getLinkFromMail(body);
            success = False;
            print("============ ", link);
            for i in range(5):
                if downloadTorrent(link, getNameForTorrrent()):
                    success = True;
                    break;
            if not success:
                print("[ERROR] FAIL");

def main():
    checkMail()

if __name__ == '__main__':
    main();
