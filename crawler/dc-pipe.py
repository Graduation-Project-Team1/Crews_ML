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
             'NAVER', 'Corp.', '기사보내기', '댓글', '본문', '구독', '기자', '기사보내기',
             '사설', '천지일보', '기자', '본문', '정치', '사회', '댓글', '국제', '문화', '박지', '경제', '종교', '서울', '없다', '20',
             '가나다라마바사', '포토', '구독', '재테크', '정치', '금융', '사회', '기업', '문화', '부동산', '정책', '증권', '서울', '경제',
             '산업', '스포', '국민의힘', '국제', '이메일', '기사', '영상', '연재', '라이프', '서경', '이용', '종목', '오피', '중앙일보',
             '서비스', 'The', 'Close', '더보기', '로그인', 'JoongAng', '고객센터', '뉴스레터', '이미지', 'by', '구독', '스페셜', '정치',
             '플러', '이용', '제공되는', '오피니언', '콘텐트', '회원', '국제', '지면', '경제', '사회', '아니', '기능', '문화', '20',
             '11', '영입', '개인', '하이', 'protected', 'email', '스포츠', '이수정', '다문화', '국회', '인사', '장관', 'D-', '누가', '출마',
             '총선',
             'ADVERTISEMENT', '플러스', 'hello!', 'Parents', '트위터', '디지털', '편의', 'Plus', '수신', '회원에게만', '개인정보', '브랜드',
             '공유',
             '동의', '간편', '메일', '메모', '있습니다', '피플', '가기', 'Posted', '글자크기', '기록', '받은', '카카',
             '복사', '국가대표', '하이엔드', '거부', '삭제', '보도', '페이스북', '머니', '영입설', '10', '수집', '함께', '운세', '가능', '알림', '기억하',
             '북마크', '보호', '보기', 'SK', '기적', '더,', '광고', '북한', '속', '대법', '카드', '충실할', '자동차', '방송·연예',
             '광고', '정보', 'TV', '디렉터', '제2', '중기', '있으', '해외증시', '오늘', '취소', '지수정', '보도', '가요', 'EBITDA', '일축',
             '출신', '스타', '매출', '총리실', '건설업계', '주택', '공시', '생생레슨', '대통령실', '간접투자', '국제일반', '금융가', '영화',
             '골프일반', '회사소개', '수신에', '개인정보취급방침', '10대골프장', '분양', '생활', '전국', '오피스·상가·토지', '채권', '사외칼럼', '이용약관',
             '통일·외교·안보', '통합검색', '2023', '실시간', '모바일', '가수', '전주시에', '1년', '까먹었다"', '위해', '연말', '지방', '경기', '연예',
             '결혼', '홍정호', 'IT·바이오', '내년', '예비후보', '만에', '지난', '징역', '등록', '감사', '이상민', '관람', '방미'
                                                                                             '대표', '뉴시', '발전', '이달',
             '지역', '60', '이동', '탄생', '선거', '1~3', '이혼', '40', '베스트', '위한', '국내', '일레븐', '프로스포츠단', '매체', '대한민국',
             '매경', 'MK', '골프채', '최고', '지원', '공유하기', '[알립니다]', '감독', '역대', '전체메골프', '성적', 'AI', '매일', '응원', '글자'}

sentiment_tokenizer = AutoTokenizer.from_pretrained("Copycats/koelectra-base-v3-generalized-sentiment-analysis")
sentiment_model = AutoModelForSequenceClassification.from_pretrained(
    "Copycats/koelectra-base-v3-generalized-sentiment-analysis")
classifier = TextClassificationPipeline(tokenizer=sentiment_tokenizer, model=sentiment_model)

model = AutoModelForSequenceClassification.from_pretrained('JminJ/kcElectra_base_Bad_Sentence_Classifier')
tokenizer = AutoTokenizer.from_pretrained('JminJ/kcElectra_base_Bad_Sentence_Classifier')
b_classifier = TextClassificationPipeline(tokenizer=tokenizer, model=model)


def sentiment_classifier(input: str):
    a = classifier(input)
    return (int(a[0]['label']) - 0.5) * a[0]['score'] * 2.0


def bs_classifier(input: str):
    b = b_classifier(input)
    if b[0]['label'] == 'bad_sen':
        return b[0]['score'] * -1
    else:
        return b[0]['score']


client = MongoClient(host='192.168.10.123', port=27017, username='root', password='')
dc_col = client['crews']['dc']
worker_url = "https://proxy"
team = {6908: '%ec%a0%84%eb%b6%81%ed%98%84%eb%8c%80%eb%aa%a8%ed%84%b0%ec%8a%a4',
        7644: '%eb%8c%80%ea%b5%acFC',
        7645: '%eb%8c%80%ec%a0%84%ed%95%98%eb%82%98%ec%8b%9c%ed%8b%b0%ec%a6%8c',
        7646: 'FC%ec%84%9c%ec%9a%b8',
        7648: '%ec%9d%b8%ec%b2%9c%ec%9c%a0%eb%82%98%ec%9d%b4%ed%8b%b0%eb%93%9c',
        7649: '%ec%a0%9c%ec%a3%bc%ec%9c%a0%eb%82%98%ec%9d%b4%ed%8b%b0%eb%93%9c',
        7650: '%ed%8f%ac%ed%95%ad%ec%8a%a4%ed%8b%b8%eb%9f%ac%ec%8a%a4',
        7652: '%ec%88%98%ec%9b%90%ec%82%bc%ec%84%b1%eb%b8%94%eb%a3%a8%ec%9c%99%ec%a6%88',
        7653: '%ec%9a%b8%ec%82%b0%ed%98%84%eb%8c%80%ec%b6%95%ea%b5%ac',
        34220: '%ea%b0%95%ec%9b%90FC',
        41261: '%ec%88%98%ec%9b%90FC',
        48912: '%ea%b4%91%ec%a3%bcFC',
        }
try:
    team_id = int(sys.argv[1])
except:
    team_id = 6908

payload_dc = json.dumps({
    "check_ip": "http://ap-northeast-2.ip.oneroom.dev:8082/check_ip",
    "method": "GET",
    "url": "https://search.dcinside.com/combine/q/"+team[team_id],
    "body": "",
    "header": {
        "Referer": "https://gall.dcinside.com"
    }
})
headers = {
    'Content-Type': 'application/json'
}


def get_time(before: str):
    return time.mktime(datetime.datetime.strptime(before, '%Y.%m.%d %H:%M').timetuple())


response = requests.request("POST", worker_url, headers=headers, data=payload_dc)

soup = BeautifulSoup(response.content, "html.parser")
t = soup.select('#container > div > section.center_content > div.inner > div.integrate_cont.sch_result > ul > li')

for i in range(15):
    try:
        if dc_col.find_one({"url": t[i].find('a').get('href')}) is None:
            title = t[i].find('a').get_text()  # 제목
            url = t[i].find('a').get('href')  # 원문
            desc = t[i].find('p').get_text()  # desc
            gall = t[i].find_all('a')[1].get_text()  # 갤러리
            written_time = get_time(t[i].find('span').get_text())  # 시간

            payload_article = json.dumps({
                "check_ip": "http://ap-northeast-2.ip.oneroom.dev:8082/check_ip",
                "method": "GET",
                "url": url,
                "body": "",
                "header": {
                    "Referer": "https://gall.dcinside.com"
                }
            })
            headers = {
                'Content-Type': 'application/json'
            }

            response_article = requests.request("POST", worker_url, headers=headers, data=payload_article)
            soup_article = BeautifulSoup(response_article.content, "html.parser")

            recommendation = int(soup_article.select('div.up_num_box p:nth-child(1)')[0].get_text())
            nonrecommendation = int(soup_article.select('div.down_num_box p:nth-child(1)')[0].get_text())
            view = int(soup_article.select('span.gall_count')[0].get_text().split(' ')[1])
            article_body = soup_article.select(
                '#container > section > article:nth-child(3) > div.view_content_wrap > div > div.inner.clear > div.writing_view_box > div.write_div')[0].get_text()
            article_body = re.sub(r'\n+', '\n', article_body)
            article_body = re.sub(r' +', ' ', article_body)
            '''
            if url.split("https://gall.dcinside.com/")[1].split("/board")[0] == "mgallery":
                gt = "M"
            else:
                gt = "G"
            payload_cmt = json.dumps({
                "check_ip": "http://ap-northeast-2.ip.oneroom.dev:8082/check_ip",
                "method": "GET",
                "url": "https://gall.dcinside.com/board/comment",
                "body": {"id": 12,
                         "no": 1,
                         "cmt_id": url.split("?id=")[1].split("&no=")[0],
                         "cmt_no": url.split("?id=")[1].split("&no=")[1],
                         "focus_cno": "",
                         "focus_pno": "",
                         "e_s_n_o": soup_article.select('#e_s_n_o')[0].get('value'),
                         "comment_page": "1",
                         "sort": "",
                         "prevCnt": "",
                         "board_type": "",
                         "_GALLTYPE_": gt},
                "header": {
                    "Referer": "https://gall.dcinside.com"
                }
            })
            response_cmt = requests.request("POST", worker_url, headers=headers, data=payload_article)
            '''
            sentiment_score = sentiment_classifier(desc)
            k = summarize_with_keywords(article_body.split('.'), min_count=1, max_length=10, beta=0.85, max_iter=10,
                                        stopwords=stopwords,
                                        verbose=True)
            k_list = []
            for j in k.keys():
                k_list.append(j)
            print(article_body)
            bad_words_score = bs_classifier(desc)
            print(bad_words_score)
            article = dict(team_id=team_id, press='dcinside', gall=gall, title=title, desc=desc, url=url,
                           body=article_body, sentiment_score=sentiment_score, keywords=k_list,
                           recommendation=recommendation, nonrecommendation=nonrecommendation,
                           date=int(written_time), view=view,
                           bad_words_score=bad_words_score)
            print(dc_col.insert_one(article).inserted_id)
            print(article)
    except:
        pass
