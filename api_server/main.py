from fastapi import FastAPI
from pymongo import MongoClient
import json
import requests
from bs4 import BeautifulSoup
client = MongoClient(host='192.168.10.123', port=27017, username='root', password='')
dc_col = client['crews']['dc']
news_col = client['crews']['news']
app = FastAPI()


# 이슈탭 sns 이슈 트위터, 인스타, 레딧 1개씩 v
# 커뮤니티 핫이슈 v
# 뉴스 탑 5 v
# 커뮤니티 핫이슈?
# 긍정 커뮤 글 3 v
# 부정 커뮤 글 3 v
# 트랜드 차트 (키워드, 트랜드 순위, 댓글 반응) v
# 트랜드 순위 v
# 우리 팀 트랜드 키워드 탑 3개 v
# 긍정 부정 비율 v

@app.get("/")
async def root():
    return {"message": "Crews ML server"}


@app.get("/news/{team_id}")  # 뉴스 탑 5
async def news_top5(team_id: str):
    n = news_col.find({"team_id": int(team_id)}).sort("date", -1).limit(5)
    list = []
    for i in n:
        list.append(dict(title=i["title"], press=i['press'], date=i['date'], url=i['url']))
    return {"news": list}


@app.get("/news/positive/{team_id}")  # 긍정 뉴스 3
async def news_pos_top3(team_id: str):
    n = news_col.aggregate(
        [{"$match": {"team_id": int(team_id)}}, {"$match": {"sentiment_score": {"$gte": 0.6}}}, {"$sort": {"date": -1}},
         {"$limit": 3}])
    list = []
    for i in n:
        list.append(dict(title=i["title"], press=i['press'], date=i['date'], url=i['url']))
    return {"news": list}


@app.get("/news/negative/{team_id}")  # 부정 뉴스 3
async def news_neg_top3(team_id: str):
    n = news_col.aggregate([{"$match": {"team_id": int(team_id)}}, {"$match": {"sentiment_score": {"$lte": -0.6}}},
                            {"$sort": {"date": -1}}, {"$limit": 3}])
    list = []
    for i in n:
        list.append(dict(title=i["title"], press=i['press'], date=i['date'], url=i['url']))
    return {"news": list}


@app.get("/sns/{team_id}")  # sns
async def sns(team_id: str):
    return {"sns": [
        dict(sns="twitter", name="전북현대", id="@eum_ugim", rt=4, heart=21,
             body='🎉 전역 🎉 \n#이지훈 선수가 김천상무에서 군복무를 마치고 #전북현대 로 복귀합니다 💚🫡',
             date=1702375440, url="https://twitter.com/eun_ugim/status/1734514455458034022"),
        dict(sns="instagram", name="전북현대모터스FC", id="jeonbuk1994", cmt=33, heart=21, body='티켓 오픈 안내 \n▶️ 예매 일정 \n2023.12.08 (금) 정오 12:00 오픈',
             date=1701928800, url="https://www.instagram.com/p/C0irSh6yEvJ/?img_index=1"),
        dict(sns="reddit", id="SmartLychee4913", cmt=0, heart=1, body='“뮌헨의 숨겨진 영웅! 대체 불가한 선수”',
             date=1701089423, url="https://www.reddit.com/r/kor_sportstv/comments/1879kfk/뮌헨의_숨겨진_영웅_대체_불가한_선수/")]}


@app.get("/community/positive/{team_id}")  # 긍정 커뮤 3
async def com_pos_top3(team_id: str):
    n =  dc_col.aggregate([{"$match": {"team_id": int(team_id)}}, {"$match": {"bad_words_score": {"$lte": -0.6}}},
                   {"$match": {"sentiment_score": {"$gte": 0.6}}},
                   {"$sort": {"date": -1}},{"$sort": {"view": -1}}, {"$limit": 3}])
    list = []
    for i in n:
        list.append(dict(title=i["title"], press=i['press'], date=i['date'], view=i['view'], url=i['url']))
    return {"community": list}


@app.get("/community/negative/{team_id}")  # 부정 커뮤 3
async def com_neg_top3(team_id: str):
    n =  dc_col.aggregate([{"$match": {"team_id": int(team_id)}}, {"$match": {"bad_words_score": {"$lte": -0.6}}},
                   {"$match": {"sentiment_score": {"$lte": -0.6}}},
                   {"$sort": {"date": -1}},{"$sort": {"view": -1}}, {"$limit": 3}])
    list = []
    for i in n:
        list.append(dict(title=i["title"], press=i['press'], date=i['date'], view=i['view'], url=i['url']))
    return {"community": list}
@app.get("/community/{team_id}")  # 커뮤 5
async def com_top5(team_id: str):
    n =  dc_col.aggregate([{"$match": {"team_id": int(team_id)}}, {"$match": {"bad_words_score": {"$lte": -0.6}}},
                   {"$sort": {"date": -1}},{"$sort": {"view": -1}}, {"$limit": 5}])
    list = []
    for i in n:
        list.append(dict(title=i["title"], press=i['press'], date=i['date'], view=i['view'], url=i['url']))
    return {"community": list}

@app.get("/keywords/{team_id}")  # 키워드 5
async def keywords(team_id: str):

    return {"keywords": [dict(rank=1, keyword="기부", buzz=153, comment="좋은 일 하시네요"),
                         dict(rank=2, keyword="복귀", buzz=145, comment="전역 축하드려요"),
                         dict(rank=3, keyword="대선", buzz=60, comment="사실 무근이라던데"),
                         dict(rank=4, keyword="500만원", buzz=40, comment="좋은 일 하시네요"),
                         dict(rank=5, keyword="전주", buzz=30, comment="좋은 일 하시네요")]}
@app.get("/opinion/{team_id}")  # 민심
async def opinion(team_id: str):
    return {"opinion": dict(positive=0.78, negative=0.2, p_keywords=['기부', '복귀', '전주'],
                            n_keywords=['대선', '국민의힘','사실무근'])}

@app.get("/k2r/{name}")  # 로마자 변경
async def k2r(name: str):
    team_dic = {"전북": "Jeonbuk Hyundai Motors",
                "전북현대": "Jeonbuk Hyundai Motors",
                "전북 현대": "Jeonbuk Hyundai Motors",
                "전북 현대 모터스": "Jeonbuk Hyundai Motors",
                "전북현대 모터스": "Jeonbuk Hyundai Motors",
                "전북현대모터스": "Jeonbuk Hyundai Motors",
                "전북 현대모터스": "Jeonbuk Hyundai Motors",
                "현대모터스": "Jeonbuk Hyundai Motors",
                "대구 FC": "Daegu FC",
                "대구FC": "Daegu FC",
                "대구 에프씨": "Daegu FC",
                "대구": "Daegu FC",
                "대전 하나 시티즌": "Daejeon Hana Citizen",
                "대전 하나시티즌": "Daejeon Hana Citizen",
                "대전하나시티즌": "Daejeon Hana Citizen",
                "대전하나 시티즌": "Daejeon Hana Citizen",
                "대전": "Daejeon Hana Citizen",
                "FC 서울": "FC Seoul",
                "FC서울": "FC Seoul",
                "서울": "FC Seoul",
                "인천 유나이티드": "Incheon United",
                "인천유나이티드": "Incheon United",
                "인천": "Incheon United",
                "제주 유나이티드": "Jeju United",
                "제주": "Jeju United",
                "제주유나이티드": "Jeju United",
                "포항 스틸러스": "Pohang Steelers",
                "포항스틸러스": "Pohang Steelers",
                "포항": "Pohang Steelers",
                "수원 삼성 블루윙즈": "Suwon Samsung Bluewings",
                "수원 삼성 블루윙스": "Suwon Samsung Bluewings",
                "수원 삼성블루윙즈": "Suwon Samsung Bluewings",
                "수원삼성 블루윙즈": "Suwon Samsung Bluewings",
                "수원삼성블루윙즈": "Suwon Samsung Bluewings",
                "수원 삼성블루윙스": "Suwon Samsung Bluewings",
                "수원삼성블루윙스": "Suwon Samsung Bluewings",
                "수원삼성 블루윙스": "Suwon Samsung Bluewings",
                "삼성 블루윙스": "Suwon Samsung Bluewings",
                "수원 블루윙즈": "Suwon Samsung Bluewings",
                "삼성 블루윙즈": "Suwon Samsung Bluewings",
                "수원 블루윙스": "Suwon Samsung Bluewings",
                "수원 삼성": "Suwon Samsung Bluewings",
                "삼성": "Suwon Samsung Bluewings",
                "울산현대": "Ulsan Hyundai",
                "울산 현대": "Ulsan Hyundai",
                "울산": "Ulsan Hyundai",
                "강원 FC": "Gangwon FC",
                "강원FC": "Gangwon FC",
                "강원": "Gangwon FC",
                "수원 FC": "Suwon FC",
                "수원FC": "Suwon FC",
                "광주 FC": "Gwangju FC",
                "광주FC": "Gwangju FC"}
    if not (team_dic.get(name) is None):
        return {"name": team_dic.get(name)}
    payload = json.dumps({
        "check_ip": "http://ap-northeast-2.ip.oneroom.dev:8082/check_ip",
        "method": "GET",
        "url": "https://dict.naver.com/name-to-roman/translation/?query="+name,
        "body": "",
        "header": {
            "Referer": ""
        }
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", "https://proxy",
                                headers=headers, data=payload)
    soup = BeautifulSoup(response.content, "html.parser").select('#container > div > table > tbody > tr > td > a')
    return {"name": [name_rome.get_text() for name_rome in soup]}