import requests
from bs4 import BeautifulSoup
from html.parser import HTMLParser
import pandas as pd
import numpy as np
import json
import re
import time
import datetime
from pymongo import MongoClient
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TextClassificationPipeline
from krwordrank.word import summarize_with_keywords
import sys

stopwords = {'관람객', '축구', '네이버', '뉴스', '검색', '정치권', '바로가기', '언론사', '저장', 'Keep', '전북', '현대', '모터스', '선수',
             '문서', '닫기', '자동완성', '레이어', '검색어', '옵션', '테크니컬', '전체', '영역', '도움말', '설정', '홈', 'FC', '프로',
             '수원', '광주', '포항', '제주', '인천', '울산', '구단', '2023년', '개인정보처리방침',
             'NAVER', 'Corp.', '기사보내기', '댓글', '본문', '구독', '기자','기사보내기',
             '사설', '천지일보', '기자', '본문', '정치', '사회', '댓글', '국제', '문화', '박지', '경제', '종교', '서울', '없다', '20',
             '가나다라마바사', '포토', '구독', '재테크', '정치', '금융', '사회', '기업', '문화', '부동산', '정책', '증권', '서울', '경제',
             '산업', '스포', '국민의힘', '국제', '이메일', '기사', '영상', '연재', '라이프', '서경', '이용', '종목', '오피', '중앙일보',
             '서비스', 'The', 'Close', '더보기', '로그인', 'JoongAng', '고객센터', '뉴스레터', '이미지', 'by', '구독', '스페셜', '정치',
             '플러', '이용', '제공되는', '오피니언', '콘텐트', '회원', '국제', '지면', '경제', '사회', '아니', '기능', '문화', '20',
             '11', '영입', '개인', '하이', 'protected', 'email', '스포츠', '이수정', '다문화', '국회', '인사', '장관', 'D-', '누가', '출마', '총선',
             'ADVERTISEMENT', '플러스', 'hello!', 'Parents', '트위터', '디지털', '편의', 'Plus', '수신', '회원에게만', '개인정보', '브랜드', '공유',
             '동의', '간편', '메일', '메모', '있습니다', '피플', '가기', 'Posted', '글자크기', '기록', '받은', '카카',
             '복사', '국가대표', '하이엔드', '거부', '삭제', '보도', '페이스북', '머니', '영입설', '10', '수집', '함께', '운세', '가능', '알림', '기억하',
             '북마크', '보호', '보기', 'SK', '기적', '더,', '광고', '북한', '속', '대법', '카드', '충실할', '자동차', '방송·연예',
             '광고', '정보', 'TV', '디렉터', '제2', '중기', '있으', '해외증시', '오늘', '취소', '지수정', '보도', '가요', 'EBITDA', '일축',
             '출신', '스타', '매출', '총리실', '건설업계', '주택', '공시', '생생레슨', '대통령실', '간접투자', '국제일반', '금융가', '영화',
             '골프일반', '회사소개', '수신에', '개인정보취급방침', '10대골프장', '분양', '생활', '전국', '오피스·상가·토지', '채권', '사외칼럼', '이용약관',
             '통일·외교·안보','통합검색', '2023', '실시간', '모바일','가수', '전주시에', '1년', '까먹었다"', '위해', '연말', '지방', '경기', '연예',
             '결혼', '홍정호', 'IT·바이오', '내년', '예비후보', '만에', '지난', '징역', '등록', '감사', '이상민', '관람', '방미'
             '대표', '뉴시', '발전', '이달', '지역', '60', '이동', '탄생', '선거', '1~3', '이혼', '40','베스트', '위한', '국내', '일레븐', '프로스포츠단', '매체','대한민국',
             '매경', 'MK', '골프채', '최고', '지원', '공유하기', '[알립니다]', '감독', '역대', '전체메골프', '성적', 'AI', '매일', '응원', '글자',}

sentiment_tokenizer = AutoTokenizer.from_pretrained("Copycats/koelectra-base-v3-generalized-sentiment-analysis")
sentiment_model = AutoModelForSequenceClassification.from_pretrained(
    "Copycats/koelectra-base-v3-generalized-sentiment-analysis")
classifier = TextClassificationPipeline(tokenizer=sentiment_tokenizer, model=sentiment_model)


def sentiment_classifier(input: str):
    a = classifier(input)
    return (int(a[0]['label']) - 0.5) * a[0]['score'] * 2.0


client = MongoClient(host='192.168.10.123', port=27017, username='root', password='')
new_col = client['crews']['news']
worker_url = "https://proxy"
team = {6908: '전북현대모터스',
        7644: '대구FC',
        7645: '대전하나시티즌',
        7646: 'FC서울',
        7648: '인천유나이티드',
        7649: '제주유나이티드',
        7650: '포항스틸러스',
        7652: '수원삼성블루윙즈',
        7653: '울산현대축',
        34220: '강원FC',
        41261: '수원FC',
        48912: '광주FC',
        }
try:
    team_id = int(sys.argv[1])
except:
    team_id = 6908

payload_naver = json.dumps({
    "check_ip": "http://ap-northeast-2.ip.oneroom.dev:8082/check_ip",
    "method": "GET",
    "url": "https://search.naver.com/search.naver?where=news&ie=utf8&sm=nws_hty&query=" + team[team_id], #지금은 관련도 순"&sort=1" 최신순
    "body": "",
    "header": {
        "Referer": ""
    }
})
headers = {
    'Content-Type': 'application/json'
}


def get_time(before: str):
    if not '전' in before:
        try:
            return time.mktime(datetime.datetime.strptime(before, '%Y.%m.%d').timetuple())
        except:
            return 0
    elif '초' in before:
        return time.time() - int(before.split('초')[0])
    elif '분' in before:
        return time.time() - int(before.split('분')[0]) * 60
    elif '시간' in before:
        return time.time() - int(before.split('시간')[0]) * 3600
    elif '일' in before:
        return time.time() - int(before.split('일')[0]) * 86400
    elif '주' in before:
        return time.time() - int(before.split('초')[0]) * 604800
    else:
        return 0


response = requests.request("POST", worker_url, headers=headers, data=payload_naver)
soup = BeautifulSoup(response.content, "html.parser")
t = soup.select('#main_pack > section > div > div.group_news > ul > li')
vaild_news_idx = 0

try:
    for i in range(10):
        if new_col.find_one({"url": t[i].select('div > div > div.news_contents > a.dsc_thumb')[0].get('href').split('§')[0]}) is None:
            vaild_news_idx = i
        else:
            break
except:
    pass

for i in range(vaild_news_idx + 1):
    try:
        url = t[i].select('div > div > div.news_contents > a.dsc_thumb')[0].get('href').split('§')[0]  # 기사 원문 링크
        if not (('munhwa' in url) or ('sjbnews' in url) or ('khan' in url) or ('mksports' in url) or ('kmib' in url)):
            title = t[i].select('div > div > div.news_contents > a.news_tit')[0].get('title').replace('\\',"")  # 기사 제목 기사는 idx 9까지 있음
            desc = t[i].select('div > div > div.news_contents > div')[0].get_text().strip()  # desc
            written_time = get_time(t[i].select('div > div > div.news_info > div.info_group > span')[0].get_text())

            payload_news = json.dumps({
                "check_ip": "http://ap-northeast-2.ip.oneroom.dev:8082/check_ip",
                "method": "GET",
                "url": url,
                "body": "",
                "header": {
                    "Referer": ""
                }
            })

            response_news = requests.request("POST", worker_url, headers=headers, data=payload_news)
            soup_news = BeautifulSoup(response_news.content, "html.parser").get_text()
            soup_news = re.sub(r'\n+', '\n', soup_news)
            soup_news = re.sub(r' +', ' ', soup_news)
            news_body = soup_news

            sentiment_score = sentiment_classifier(desc)
            k = summarize_with_keywords(soup_news.split('.'),min_count=4, max_length=10, beta=0.85, max_iter=10,
                                        stopwords=stopwords,
                                        verbose=True)
            k_list = []
            for j in k.keys():
                k_list.append(j)
            press = t[i].select('div > div > div.news_info > div.info_group > a')[0].get_text().split(' ')[0]  # 신문사 정보
            article = dict(team_id=team_id, press=press, title=title, desc=desc, url=url,
                           body=news_body, sentiment_score=sentiment_score, keywords=k_list, date=int(written_time))
            print(new_col.insert_one(article).inserted_id)
            print(article)
    except:
        pass
