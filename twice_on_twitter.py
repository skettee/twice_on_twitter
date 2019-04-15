#
# Twice 트윗 
#
#%%
import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
from datetime import timedelta

if __debug__:
    import os.path

# 모아보기 컴포넌트를 가져온다.
import moabogey_database as moabogey
from moabogey_id import *

# 사이트 이름
site_name = 'twitter'
# 사이트에서 가져올 주제
subject_name = 'JYPETWICE'
# 사이트 주소
site_url = 'https://twitter.com/JYPETWICE'
if __debug__:
    print('{} 데이터 수집 중...'.format(site_url))

# 사이트의 HTML을 가져온다.
try:
    response = requests.get(site_url)
    # 에러가 발생 했을 경우 에러 내용을 출력하고 종료한다.
    response.raise_for_status()
except HTTPError as http_err:
    print(f'HTTP error occurred: {http_err}')
except Exception as err:
    print(f'Other error occurred: {err}')
else:
    html_source = response.text
    
    # BeautifulSoup 오브젝트를 생성한다.
    soup = BeautifulSoup(html_source, 'html.parser')
    
    # HTML을 분석하기 위해서 페이지의 소스를 파일로 저장한다.
    if __debug__:
        file_name = site_name + '_source.html'
        if not os.path.isfile(file_name):
            print('file save: ', file_name)
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(soup.prettify())

    # 데이터를 저장할 데이터베이스를 생성한다. 
    # bot_id는 moabogey_id에서 가져온 값이다.
    db_name = subject_name + '_on_' + site_name 
    my_db = moabogey.Dbase(db_name, bot_id)
            
    # 반복해서 포스트의 목록을 하나씩 검색하며 데이터를 수집한다.
    for post in soup.find_all('div', class_='content'):
        # 포스트를 올린 작성자를 수집한다.
        moa_createBy = post.find('strong', class_='fullname').text.strip()
        #print('createdBy: ', moa_createBy)

        # 포스트의 주소를 수집한다.
        href = post.find('a', {"class": "tweet-timestamp", "href": True})
        if href:
            href = href['href'] 
            href_url = 'https://twitter.com' + href
            #print('href: ', href_url)

            # 포스트를 올린 날짜를 수집한다.
            if __debug__:
                # LANGUAGE KOREA CASE
                post_time = post.find('a', class_="tweet-timestamp")['title'].replace('오전', 'AM').replace('오후', 'PM')
                # 시간 형식 - AM 2:27 - 2019년 3월 11일
                moa_createdAt = datetime.strptime(post_time, '%p %I:%M - %Y년 %m월 %d일')
            else:
                # LANGUAGE UNDEFINED CASE
                post_time = post.find('a', class_="tweet-timestamp")['title']
                # 시간 형식 - 8:01 PM - 30 Mar 2019
                moa_createdAt = datetime.strptime(post_time, '%I:%M %p - %d %b %Y')

            # 시간을 보정한다. UTC (+7) ?
            moa_createdAt = moa_createdAt + timedelta(hours=7)

            # 포스트의 HTML을 가져온다.
            try:
                response =  requests.get(href_url)
                response.raise_for_status()
            except HTTPError as http_err:
                print(f'HTTP error occurred: {http_err}')
            except Exception as err:
                print(f'Other error occurred: {err}')
            else:
                subhtml_source = response.text
                # BeautifulSoup 오브젝트를 생성한다.
                post = BeautifulSoup(subhtml_source, 'html.parser')

                # HTML을 분석하기 위해서 포스트의 소스를 파일로 저장한다.
                if __debug__:
                    file_name = site_name + '_post_source.html'
                    if not os.path.isfile(file_name):
                        print('file save: ', file_name)
                        with open(file_name, 'w', encoding='utf-8') as f:
                            f.write(post.prettify())

                # 포스트 제목을 수집/가공 한다.
                #moa_title = post.find('meta', property="og:title")
                moa_title = post.find('meta', property="og:description")
                if moa_title:
                    moa_title = moa_title['content'].splitlines()[0]
                
                # 포스트 요약을 수집/가공한다.
                moa_desc = post.find('meta', property="og:description")
                if moa_desc:
                    moa_desc = ''.join(moa_desc['content'].splitlines()[1:])
                
                # 대표 이미지의 주소를 수집한다.
                moa_image = post.find('meta', property="og:image")
                if moa_image:
                    moa_image = moa_image['content']
                
                # 사이트 이름을 수집한다.
                moa_site_name = post.find('meta', property="og:site_name")
                if moa_site_name:
                    moa_site_name = moa_site_name['content']
                
                # 포스트의 주소를 가공한다.
                moa_url = 'https://mobile.twitter.com' + href
                
                # 현재 날짜와 시간을 수집한다.
                moa_timeStamp = datetime.now()

                # 오늘 발행된 포스트만 선택한다.
                delta = moa_timeStamp - moa_createdAt + timedelta(hours=9)
                if delta.days <=0:
                
                    # 데이터베이스에 있는 포스트와 중복되는지를 확인한다.
                    if my_db.isNewItem('title', moa_title):
                        # 데이터 타입을 확인한다.
                        assert type(moa_title) == str, 'title: type error'
                        assert type(moa_desc) == str, 'desc: type error'
                        assert type(moa_url) == str, 'url: type error'
                        assert type(moa_image) == str, 'image: type error'
                        assert type(moa_site_name) == str, 'siteName: type error'
                        assert type(moa_createBy) == str, 'createBy: type error'
                        assert type(moa_createdAt) == datetime, 'createdAt: type error'
                        assert type(moa_timeStamp) == datetime, 'timeStamp: type error'
                        
                        # JSON형식으로 수집한 데이터를 변환한다.
                        db_data = { 'title': moa_title, 
                            'desc': moa_desc,
                            'url': moa_url,
                            'image': moa_image,
                            'siteName': moa_site_name,
                            'createdBy': moa_createBy,
                            'createdAt': moa_createdAt,
                            'timeStamp': moa_timeStamp
                        }

                        if __debug__:
                            # 디버그를 위해서 수집한 데이터를 출력한다.
                            temp_data = db_data.copy()
                            temp_data['desc'] = temp_data['desc'][:20] + '...'
                            print('collected json data: ')
                            print(json.dumps(temp_data, indent=4, ensure_ascii=False, default=str))

                        # 수집한 데이터를 데이터베이스에 전송한다.
                        my_db.insertTable(db_data)

    # 데이터 베이스에 저장된 데이터를 디스플레이 한다.
    if __debug__:
        my_db.displayHTML()

    # 데이터 베이스를 닫는다.
    my_db.close()
    