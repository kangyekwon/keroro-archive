#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keroro Archive - Bulk Data Insertion Script
Adds quotes, trivia, items, and character relations to keroro.db
"""

import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = 'data/keroro.db'

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ============================================================
# 1. QUOTES (55 new quotes)
# ============================================================
NEW_QUOTES = [
    # ---- Keroro (id=1) ----
    (1, 'ケロロ小隊、出動であります！', '케로로 소대, 출동이であります!', None,
     '소대원들을 소집할 때 외치는 구호. 대체로 한심한 작전이 뒤따른다.'),
    (1, '今日の侵略はお休みであります！', '오늘의 침략은 쉬겠であります!', None,
     '건프라 신제품이 나왔거나 TV 특집이 있을 때 자주 하는 말.'),
    (1, '我輩のガンプラコレクションに触るな！', '내 건프라 컬렉션에 손대지 마!', None,
     '누군가 자신의 건프라에 손을 대려 할 때 필사적으로 외치는 대사.'),
    (1, 'お掃除は侵略の基本であります！', '청소는 침략의 기본이であります!', None,
     '나츠미에게 청소를 시키면서도 침략과 연결시키려는 궁색한 변명.'),
    (1, '夏美殿の怒りは宇宙最強であります…', '나츠미 님의 분노는 우주 최강이であります…', None,
     '나츠미에게 혼날 때마다 느끼는 공포를 솔직하게 표현한 대사.'),
    (1, 'ケロン星の誇りにかけて！', '케론성의 자존심을 걸고!', None,
     '드물게 진지해질 때 하는 대사. 하지만 금방 다시 건프라로 돌아간다.'),
    (1, '冬樹殿、一緒にガンプラ作るであります！', '후유키 님, 같이 건프라 만들겠であります!', None,
     '후유키를 건프라의 세계로 끌어들이려는 케로로의 일상적인 권유.'),

    # ---- Giroro (id=2) ----
    (2, '俺は戦士だ。感情に流されるわけにはいかん。', '나는 전사다. 감정에 휘둘릴 수는 없어.', None,
     '나츠미를 의식하면서도 군인으로서의 자세를 유지하려는 기로로.'),
    (2, 'ケロロ！いい加減に侵略に本気を出せ！', '케로로! 제발 침략에 진심을 보여라!', None,
     '매일같이 게으름 피우는 케로로에게 화를 내는 기로로의 단골 대사.'),
    (2, 'この銃は俺の魂だ。', '이 총은 나의 영혼이다.', None,
     '무기를 소중히 여기는 기로로의 전사로서의 신념을 보여주는 대사.'),
    (2, '夏美…今日も綺麗だな…', '나츠미… 오늘도 예쁘구나…', None,
     '나츠미를 몰래 바라보며 중얼거리는 기로로. 본인은 들키지 않았다고 생각한다.'),
    (2, 'キャンプファイヤーは兵士の基本だ。', '캠프파이어는 군인의 기본이다.', None,
     '텐트 앞에서 고구마를 구우며 하는 말. 실은 나츠미를 기다리고 있다.'),
    (2, '戦場では一瞬の判断が命を分ける。', '전장에서는 한순간의 판단이 생사를 가른다.', None,
     '전투 경험을 바탕으로 한 기로로의 진지한 격언.'),
    (2, '猫…お前だけが俺を理解してくれるな。', '고양이… 너만이 나를 이해해주는구나.', None,
     '기로로가 키우는 고양이에게 속마음을 털어놓는 장면.'),

    # ---- Tamama (id=3) ----
    (3, 'タマタマインパクト！！', '타마타마 임팩트!!', None,
     '타마마의 필살기를 발동할 때 외치는 기합. 강력한 에너지 빔을 발사한다.'),
    (3, 'ぐんそーさん、大好きであります！', '군조님, 너무 좋아하であります!', None,
     '케로로에 대한 맹목적인 애정을 드러내는 타마마의 대표 대사.'),
    (3, 'あの女…許さないでありますよ…', '저 여자… 용서 못 하であります…', None,
     '모아가 케로로에게 가까이 갈 때 흑화하며 중얼거리는 타마마의 질투.'),
    (3, 'かわいいは正義であります！', '귀여움은 정의であります!', None,
     '자신의 귀여운 외모를 무기로 삼는 타마마의 철학.'),
    (3, 'ジェラシーパワー全開！', '질투 파워 전개!', None,
     '질투심이 극에 달했을 때 엄청난 전투력을 발휘하는 타마마.'),
    (3, 'お菓子がないと生きていけないであります！', '과자가 없으면 살 수 없であります!', None,
     '과자를 향한 무한한 사랑. 모모카의 집에서 과자를 무한으로 먹는다.'),
    (3, 'ぐんそーさんの隣は私の場所であります！', '군조님 옆자리는 제 자리であります!', None,
     '케로로 옆자리를 사수하려는 타마마의 집착.'),

    # ---- Kururu (id=4) ----
    (4, 'クックックッ…面白いデータが取れたぜ。', '쿠쿠쿠… 재미있는 데이터를 얻었군.', None,
     '실험 결과를 분석하며 음침하게 웃는 쿠루루의 전형적인 반응.'),
    (4, '俺の発明に不可能はない。', '내 발명에 불가능은 없다.', None,
     '천재 발명가로서의 자부심. 실제로 거의 모든 것을 만들 수 있다.'),
    (4, 'クックックッ…お前ら全員実験台だ。', '쿠쿠쿠… 너희 전부 실험 대상이다.', None,
     '소대원들을 자신의 발명품 실험에 이용하려는 쿠루루.'),
    (4, '感情？そんな非効率なもの、いらねーよ。', '감정? 그런 비효율적인 것, 필요 없어.', None,
     '감정을 배제하고 합리적으로만 행동하려는 쿠루루의 성격.'),
    (4, 'このカレーには特別な隠し味が入ってるぜ。', '이 카레에는 특별한 비밀 재료가 들어있지.', None,
     '쿠루루가 만든 카레. 맛은 좋지만 무엇이 들어있는지 아무도 모른다.'),
    (4, '情報は最大の武器だ。クックックッ。', '정보는 최대의 무기다. 쿠쿠쿠.', None,
     '모든 소대원의 비밀을 파악하고 있는 쿠루루의 정보 철학.'),
    (4, 'クックックッ…修理代は高くつくぜ？', '쿠쿠쿠… 수리비는 비쌀 텐데?', None,
     '자신의 발명품이 부서졌을 때 수리비를 청구하는 쿠루루.'),

    # ---- Dororo (id=5) ----
    (5, '皆さん…また僕のこと忘れてますよね…', '여러분… 또 저를 잊으셨죠…', None,
     '소대원들에게 존재감을 무시당할 때마다 하는 도로로의 슬픈 대사.'),
    (5, '自然を守ることこそ、真の忍の道。', '자연을 지키는 것이야말로 진정한 닌자의 길.', None,
     '환경보호를 사명으로 여기는 도로로의 신념.'),
    (5, 'トラウマスイッチ、オン…', '트라우마 스위치, 온…', None,
     '과거의 안 좋은 기억이 떠올랐을 때 움츠러드는 도로로.'),
    (5, '小雪殿、今日も稽古をお願いします。', '코유키 님, 오늘도 수련 부탁드립니다.', None,
     '동료 닌자인 코유키와 함께 수련하는 도로로의 일상.'),
    (5, 'この星の美しさを、もっと多くの者に知ってほしい。', '이 별의 아름다움을, 더 많은 이들이 알았으면 좋겠습니다.', None,
     '지구의 자연을 사랑하게 된 도로로의 진심 어린 소원.'),
    (5, '侵略より大切なものがある…', '침략보다 소중한 것이 있습니다…', None,
     '침략보다 지구의 자연과 평화를 우선시하는 도로로의 가치관.'),
    (5, 'ケロロ殿…いつか僕の名前を覚えてくれますか…', '케로로 님… 언젠가 제 이름을 기억해주실 건가요…', None,
     '케로로에게 이름조차 잊힌 도로로의 서글픈 독백.'),

    # ---- Natsumi (id=12) ----
    (12, 'ケロロ！今日中に掃除終わらせなさい！', '케로로! 오늘 안에 청소 끝내!', None,
     '케로로에게 가사를 시키는 나츠미의 일상적인 명령.'),
    (12, '宇宙人だろうが何だろうが、悪いことは悪い！', '우주인이든 뭐든, 나쁜 건 나쁜 거야!', None,
     '정의감이 강한 나츠미의 확고한 신념.'),
    (12, 'あたし、負けず嫌いだから。', '나, 지기 싫어하는 성격이거든.', None,
     '어떤 도전이든 물러서지 않는 나츠미의 강한 승부욕.'),
    (12, 'フユキ、あんた또 그 개구리한테 속은 거지?', '후유키, 너 또 그 개구리한테 속은 거지?', None,
     '후유키가 케로로의 말에 넘어갈 때마다 한심해하는 나츠미.'),
    (12, 'この家は私が守る！', '이 집은 내가 지킨다!', None,
     '히나타 가의 수호자로서의 나츠미의 결의.'),

    # ---- Fuyuki (id=11) ----
    (11, 'すごい！これが本物のオカルトだ！', '대단해! 이게 진짜 오컬트야!', None,
     '초자연적인 현상을 접할 때마다 흥분하는 후유키.'),
    (11, '軍曹、それは侵略じゃなくて犯罪だよ。', '군조, 그건 침략이 아니라 범죄야.', None,
     '케로로의 무모한 계획에 냉정하게 태클을 거는 후유키.'),
    (11, 'ケロロ軍曹との出会いは僕の人生を変えた。', '케로로 군조와의 만남은 내 인생을 바꿨어.', None,
     '케로로와의 동거 생활을 긍정적으로 받아들이는 후유키.'),
    (11, 'オカルト研究は科学の未来なんだ！', '오컬트 연구는 과학의 미래야!', None,
     '오컬트에 대한 학문적(?) 열정을 보이는 후유키.'),

    # ---- Angol Mois (id=14) ----
    (14, 'おじさま、大好きです！', '아저씨, 너무 좋아해요!', None,
     '케로로를 "아저씨"라 부르며 따르는 모아의 애정 표현.'),
    (14, 'ルシファースピア！', '루시퍼 스피어!', None,
     '모아의 필살기. 행성도 파괴할 수 있는 엄청난 위력을 가지고 있다.'),
    (14, '地球の文化って素敵ですね！', '지구의 문화는 멋지네요!', None,
     '지구 문화에 순수하게 감탄하는 모아.'),
    (14, '아르마겟돈은 잠시 연기할게요~', '아르마게돈은 잠시 연기할게요~', None,
     '후유키와 케로로 때문에 지구 멸망을 미루는 모아.'),

    # ---- Momoka (id=15) ----
    (15, 'フユキ君…今日こそ告白を…！', '후유키 군… 오늘이야말로 고백을…!', None,
     '매번 고백하려다 실패하는 모모카의 반복되는 결심.'),
    (15, '西澤家の財力を見せてあげるわ！', '니시자와 가의 재력을 보여줄게!', None,
     '흑화 모모카가 재벌의 힘을 과시할 때의 대사.'),
    (15, '穏やかな心で…穏やかな心で…ブチッ！', '차분한 마음으로… 차분한 마음으로… 뿌직!', None,
     '참으려다 결국 흑화하는 모모카의 반복 패턴.'),

    # ---- Koyuki (id=16) ----
    (16, 'なつみー！一緒に遊ぼう！', '나츠미! 같이 놀자!', None,
     '나츠미를 가장 친한 친구로 여기는 코유키의 순수한 호출.'),
    (16, '忍法！木の葉隠れの術！', '인법! 나뭇잎 숨기의 술!', None,
     '닌자로서의 능력을 사용하는 코유키의 기술 발동 대사.'),

    # ---- Garuru (id=6) ----
    (6, '任務は完璧に遂行する。それが軍人だ。', '임무는 완벽하게 수행한다. 그것이 군인이다.', None,
     '완벽주의 군인 가루루의 철학. 케로로 소대와는 격이 다르다.'),
    (6, 'ケロロ…お前はまだ成長していないようだな。', '케로로… 넌 아직 성장하지 못한 모양이군.', None,
     '케로로의 한심한 모습을 보며 실망하는 가루루.'),

    # ---- Saburo (id=17) ----
    (17, 'この筆で描いたものは全て現実になる。', '이 붓으로 그린 것은 모두 현실이 된다.', None,
     '리얼리티 펜의 능력을 설명하는 사부로의 대사.'),
    (17, '芸術は爆発だ。', '예술은 폭발이다.', None,
     '예술가적 기질이 강한 사부로의 철학.'),
]


# ============================================================
# 2. TRIVIA (55 entries)
# ============================================================
TRIVIA_DATA = [
    # ---- production ----
    ('요시자키 미네의 원작 만화 「케로로 군소」는 1999년 카도카와 쇼텐의 월간 소년 에이스에서 연재를 시작했다.', 'production', '월간 소년 에이스'),
    ('TV 애니메이션은 2004년 4월 3일부터 2011년 4월 2일까지 총 358화가 방영되었다.', 'production', 'TV 도쿄'),
    ('애니메이션 제작은 선라이즈(SUNRISE)가 담당했으며, 건담 시리즈와 같은 제작사이다.', 'production', '선라이즈'),
    ('한국에서는 투니버스를 통해 「개구리 중사 케로로」라는 제목으로 방영되었다.', 'production', '투니버스'),
    ('극장판은 총 5편이 제작되었으며, 2006년부터 2010년까지 매년 1편씩 개봉했다.', 'production', '카도카와'),
    ('원작 만화의 누적 발행 부수는 2400만 부를 돌파했다.', 'production', '카도카와 쇼텐'),
    ('애니메이션 시리즈의 총 감독은 사토 준이치가 맡았다.', 'production', '선라이즈'),
    ('케로로 역의 성우는 와타나베 쿠미코로, 도라에몽의 노비타 역으로도 유명하다.', 'production', ''),
    ('2014년에 「케로로 군소」 신 애니메이션 시리즈(플래시 애니)가 제작되었다.', 'production', ''),
    ('만화 연재 25주년을 기념하여 2024년에 특별 이벤트가 개최되었다.', 'production', ''),
    ('케로로의 한국판 성우는 정미숙이 담당했다.', 'production', '투니버스'),

    # ---- character ----
    ('케로로의 이름은 일본어로 개구리 울음소리인 "케로케로(ケロケロ)"에서 유래했다.', 'character', ''),
    ('기로로의 이름은 "기로(ギロ)" 즉 "째려보다"에서 유래하여 날카로운 성격을 반영한다.', 'character', ''),
    ('타마마의 이름은 올챙이를 뜻하는 "오타마자쿠시(おたまじゃくし)"에서 유래했다.', 'character', ''),
    ('쿠루루의 이름은 "쿠루쿠루(くるくる)" 즉 "빙글빙글"에서 유래하여 머리가 잘 돌아감을 의미한다.', 'character', ''),
    ('도로로의 이름은 데즈카 오사무의 만화 「도로로」에서 따왔다.', 'character', ''),
    ('앙골 모아의 "앙골"은 예언서에 등장하는 공포의 대왕 앙골모아에서 유래했다.', 'character', '노스트라다무스'),
    ('후유키(冬樹)는 "겨울 나무"라는 뜻으로, 나츠미(夏美)의 "여름 아름다움"과 대비된다.', 'character', ''),
    ('히나타 가의 어머니 아키(秋)는 "가을"을 의미하며, 가족 이름이 모두 계절과 관련있다.', 'character', ''),
    ('가루루 소대는 케로로 소대의 상위 호환 버전으로, 각 멤버가 케로로 소대원의 라이벌이다.', 'character', ''),
    ('케론인의 모자(?)는 실제로 머리카락이 아니라 촉수의 일종이다.', 'character', ''),
    ('모모카 니시자와는 평소에는 온순하지만, 흥분하면 "흑 모모카"로 변하는 이중인격이다.', 'character', ''),
    ('556(코고로)의 이름은 숫자 "5-5-6"의 일본어 발음 "코-고-로"에서 유래했다.', 'character', ''),
    ('케로로의 계급 "군조(軍曹)"는 일본 군대의 하사관 계급으로, 한국어로는 "중사"에 해당한다.', 'character', ''),

    # ---- easter_egg ----
    ('작중 케로로가 만드는 건프라는 실제 반다이의 건담 플라모델 상품이 등장한다.', 'easter_egg', ''),
    ('나츠미의 방에는 종종 현실의 인기 아이돌 포스터가 패러디되어 등장한다.', 'easter_egg', ''),
    ('쿠루루가 만든 발명품 중 일부는 도라에몽의 비밀도구를 패러디한 것이다.', 'easter_egg', ''),
    ('케로로의 건프라 수집 장면에서 실제 건담 시리즈의 기체가 정확하게 재현되어 있다.', 'easter_egg', ''),
    ('에피소드 중간에 등장하는 아이캐치에는 매번 다른 패러디 요소가 숨어있다.', 'easter_egg', ''),
    ('작중 등장하는 TV 프로그램은 대부분 실존 일본 프로그램의 패러디이다.', 'easter_egg', ''),
    ('기로로의 텐트 옆 캠프파이어 장면은 「람보」 시리즈의 오마주이다.', 'easter_egg', ''),
    ('도로로의 닌자 기술명은 실제 닌자 역사에서 가져온 이름이 많다.', 'easter_egg', ''),
    ('케로로가 침략 계획서를 발표하는 형식은 일본 기업의 프레젠테이션을 패러디한 것이다.', 'easter_egg', ''),
    ('모아의 루시퍼 스피어는 에반게리온의 롱기누스의 창을 오마주한 것이라는 설이 있다.', 'easter_egg', ''),

    # ---- crossover ----
    ('케로로 군소에는 같은 선라이즈 제작의 건담 시리즈 레퍼런스가 매우 자주 등장한다.', 'crossover', '선라이즈'),
    ('건담 시리즈의 메카 디자이너 오카와라 쿠니오가 케로로 로보 디자인에 참여했다.', 'crossover', ''),
    ('작중 케로로가 "통상의 3배"를 언급하는 것은 기동전사 건담의 샤아 아즈나블의 대사 패러디이다.', 'crossover', '기동전사 건담'),
    ('타마마의 임팩트 기술은 드래곤볼의 에너지파를 연상시키는 연출이다.', 'crossover', '드래곤볼'),
    ('일부 에피소드에서 에반게리온, 세일러문, 원피스 등의 패러디가 등장한다.', 'crossover', ''),
    ('케로로의 "지구 침략" 컨셉은 「우루세이 야츠라」의 외계인 설정과 유사점이 있다.', 'crossover', ''),
    ('556(코고로)의 탐정 캐릭터는 명탐정 코난의 코고로를 패러디한 것이다.', 'crossover', '명탐정 코난'),
    ('기로로의 전투 장면 연출은 종종 건담이나 보톰즈 같은 리얼로봇 작품을 오마주한다.', 'crossover', ''),

    # ---- record ----
    ('TV 애니메이션 총 방영 기간은 약 7년(2004~2011)으로, 장수 애니메이션 중 하나이다.', 'record', ''),
    ('TV 시리즈 총 에피소드 수는 358화로, 매주 방영 애니메이션 중 상당한 분량이다.', 'record', ''),
    ('극장판 5편의 총 누적 관객 수는 일본에서 약 300만 명을 넘었다.', 'record', ''),
    ('원작 만화는 30권 이상 발행되었으며 현재도 연재 중이다.', 'record', '월간 소년 에이스'),
    ('캐릭터 상품 매출은 한때 연간 수백억 엔을 기록할 정도로 인기가 높았다.', 'record', ''),
    ('한국에서의 인지도는 일본 다음으로 높으며, 투니버스 대표 애니메이션 중 하나였다.', 'record', '투니버스'),
    ('케로로 군소의 건프라 콜라보레이션 상품은 수십 종이 출시되었다.', 'record', '반다이'),
    ('게임화도 다수 이루어져 PS2, PSP, DS 등 다양한 플랫폼에서 게임이 출시되었다.', 'record', ''),
    ('2006년 극장판 제1편은 일본 박스오피스에서 개봉 첫 주 3위를 기록했다.', 'record', ''),
    ('만화 연재 기간이 25년을 넘기며, 장기 연재 만화 반열에 올랐다.', 'record', ''),
]


# ============================================================
# 3. ITEMS (35 new items)
# ============================================================
NEW_ITEMS = [
    ('Keron Suit', '케론 수트', 'gadget', 'Keroro Platoon',
     '케론인의 기본 장비로, 체온 조절과 방어 기능을 가진 전투복. 각 소대원의 색상과 디자인이 다르다.'),
    ('Space Phone', '우주 전화기', 'gadget', 'Keroro Platoon',
     '케론성과의 통신에 사용하는 장거리 우주 통신 장치. 본부와의 연락에 필수적이다.'),
    ('Giroro Weapon Arsenal', '기로로 무기고', 'weapon', 'Giroro',
     '기로로가 텐트 안에 보관하는 방대한 무기 컬렉션. 온갇 종류의 빔 건과 폭발물이 있다.'),
    ('Tamama Impact Generator', '타마마 임팩트 발생기', 'weapon', 'Tamama',
     '타마마의 질투 에너지를 증폭시켜 임팩트 기술의 위력을 배가시키는 장치.'),
    ('Kururu Lab Computer', '쿠루루 연구실 컴퓨터', 'gadget', 'Kururu',
     '쿠루루의 지하 연구실에 있는 메인 컴퓨터. 지구의 모든 정보 시스템에 접근할 수 있다.'),
    ('Dororo Shuriken Set', '도로로 수리검 세트', 'weapon', 'Dororo',
     '도로로가 사용하는 특수 제작 수리검 세트. 케론 기술이 접목된 고성능 닌자 도구.'),
    ('Nishizawa Helicopter', '니시자와 헬리콥터', 'vehicle', 'Momoka Nishizawa',
     '모모카가 이동할 때 자주 사용하는 개인 헬리콥터. 니시자와 가의 재력을 보여준다.'),
    ('Reality Pen', '리얼리티 펜', 'gadget', 'Saburo',
     '사부로가 소유한 특수한 펜. 이것으로 그린 것은 무엇이든 현실이 된다.'),
    ('Keroro Hat', '케로로 모자', 'other', 'Keroro',
     '케로로의 상징인 별 모양 모자. 실제로는 모자가 아니라 케론인의 신체 일부이다.'),
    ('Angol Stone', '앙골 스톤', 'weapon', 'Angol Mois',
     '앙골 모아가 루시퍼 스피어를 발동할 때 사용하는 에너지원. 앙골 족의 비보.'),
    ('Growth Accelerator', '성장 가속기', 'gadget', 'Kururu',
     '대상의 성장 속도를 극적으로 가속시키는 장치. 소대원들이 어른이 되는 에피소드에 등장.'),
    ('Memory Eraser', '기억 지우개', 'gadget', 'Keroro Platoon',
     '일반인의 기억을 지울 수 있는 장치. 케론인의 존재가 발각되었을 때 사용한다.'),
    ('Keron Underground Base', '케론 지하 기지', 'other', 'Keroro Platoon',
     '히나타 가 지하에 건설한 케로로 소대의 비밀 기지. 의외로 넓고 다양한 시설이 있다.'),
    ('Body Swap Machine', '몸 바꾸기 머신', 'gadget', 'Kururu',
     '두 사람의 몸을 바꿀 수 있는 장치. 코미디 에피소드의 단골 소재.'),
    ('Pekopon Suit Mark II', '포코펜 수트 마크 II', 'gadget', 'Keroro Platoon',
     '인간으로 변장하기 위한 개량형 수트. 기존 모델보다 더 자연스러운 변장이 가능하다.'),
    ('Keroro Drone', '케로로 드론', 'vehicle', 'Keroro',
     '케로로가 정찰용으로 사용하는 소형 무인기. 주로 나츠미 감시에 사용되다 발각된다.'),
    ('Emotion Amplifier', '감정 증폭기', 'gadget', 'Kururu',
     '대상의 감정을 극단적으로 증폭시키는 장치. 사용하면 소소한 감정도 폭발적으로 변한다.'),
    ('Keron Army Medal', '케론 군 훈장', 'other', 'Keron Army',
     '뛰어난 공로를 세운 케론 군인에게 수여하는 훈장. 케로로는 아직 받지 못했다.'),
    ('Invisibility Cape', '투명 망토', 'gadget', 'Dororo',
     '도로로가 닌자 임무에 사용하는 투명 망토. 케론 기술과 닌자 기술이 합쳐진 장비.'),
    ('Mois Cellphone', '모아 핸드폰', 'gadget', 'Angol Mois',
     '앙골 모아가 사용하는 핸드폰. 외형은 평범하지만 우주 통신이 가능하다.'),
    ('Weather Controller', '날씨 조절기', 'gadget', 'Kururu',
     '특정 지역의 날씨를 조작할 수 있는 장치. 케로 볼의 기능 중 하나를 독립시킨 것.'),
    ('Gunpla Battle System', '건프라 배틀 시스템', 'gadget', 'Keroro',
     '건프라를 실제 크기로 구현하여 전투시킬 수 있는 시스템. 케로로의 꿈의 발명품.'),
    ('Nishizawa Submarine', '니시자와 잠수함', 'vehicle', 'Momoka Nishizawa',
     '니시자와 가의 개인 잠수함. 수중 탐사나 비밀 이동에 사용된다.'),
    ('Age Ray Gun', '나이 변환 광선총', 'gadget', 'Kururu',
     '대상의 나이를 자유자재로 변환시키는 광선총. 어린아이나 노인으로 변할 수 있다.'),
    ('Keronian Spaceship Parts', '케론인 우주선 부품', 'other', 'Keroro Platoon',
     '케로로 소대가 지구에 올 때 타고 온 우주선의 부품. 각지에 흩어져 수집이 필요하다.'),
    ('Dream Viewer', '꿈 관찰기', 'gadget', 'Kururu',
     '타인의 꿈속을 관찰하거나 진입할 수 있는 장치. 프라이버시 침해의 대명사.'),
    ('Clone Machine', '클론 머신', 'gadget', 'Kururu',
     '대상의 복제본을 만들 수 있는 장치. 케로로가 분신을 만들어 일하려다 대혼란이 일어났다.'),
    ('Giroro Camping Set', '기로로 캠핑 세트', 'other', 'Giroro',
     '기로로가 항상 가지고 다니는 야외 생존 장비. 텐트, 취사도구 등 군용 사양이다.'),
    ('Power Suit Alpha', '파워 수트 알파', 'gadget', 'Garuru Platoon',
     '가루루 소대가 사용하는 고성능 전투 강화복. 케로로 소대의 장비보다 한 세대 앞선다.'),
    ('Alien Detector', '외계인 탐지기', 'gadget', 'Fuyuki Hinata',
     '후유키가 만든(혹은 쿠루루에게 받은) 외계인 탐지 장치. 오컬트 연구의 필수품.'),
    ('Keron Star Crystal', '케론 스타 크리스탈', 'other', 'Keron Army',
     '케론성의 에너지를 결정화한 보석. 케론 군의 최고 기밀 중 하나이다.'),
    ('Transformation Ray', '변신 광선', 'gadget', 'Kururu',
     '대상의 외모를 다른 모습으로 변환시키는 광선. 동물이나 물건으로도 변신할 수 있다.'),
    ('556 Detective Kit', '556 탐정 키트', 'other', 'Kogoro (556)',
     '556이 자칭 우주 탐정으로 활동할 때 사용하는 도구 세트. 성능은 의문.'),
    ('Natsumi Power Band', '나츠미 파워 밴드', 'other', 'Natsumi Hinata',
     '나츠미의 괴력을 상징하는 아이템. 운동 실력과 결합되면 케론인도 두려워한다.'),
    ('Hologram Projector', '홀로그램 프로젝터', 'gadget', 'Kururu',
     '실물과 구분이 어려운 고급 홀로그램을 투영하는 장치. 침략 작전에 자주 활용된다.'),
]


# ============================================================
# 4. CHARACTER RELATIONS (45 new relations)
# ============================================================
NEW_RELATIONS = [
    # ---- Keroro relations ----
    (1, 14, 'friend', '케로로와 모아는 "아저씨-조카" 같은 관계. 모아는 케로로를 맹목적으로 따른다.'),
    (1, 15, 'friend', '케로로와 모모카는 직접적 관계는 적지만, 후유키를 통해 연결된다.'),
    (1, 13, 'subordinate', '케로로는 아키에게 머리가 올라가지 않는다. 아키의 관대함 덕에 히나타 가에 거주.'),
    (1, 6, 'rival', '케로로와 가루루는 라이벌 관계. 가루루는 케로로 소대의 교체를 명받고 지구에 온다.'),
    (1, 33, 'family', '신 케로로는 케로로의 복제체. 케로로는 아버지 같은 존재이다.'),
    (1, 44, 'subordinate', '케론 군 사령관은 케로로의 상관. 침략 성과가 없어 늘 질책받는다.'),

    # ---- Giroro relations ----
    (2, 12, 'crush', '기로로는 나츠미에게 연심을 품고 있지만 절대 직접 고백하지 못한다.'),
    (2, 6, 'family', '기로로와 가루루는 형제. 가루루는 형으로 기로로보다 계급이 높다.'),
    (2, 61, 'friend', '기로로와 고양이는 돈독한 사이. 기로로의 유일한 위안처이다.'),
    (2, 16, 'ally', '기로로와 코유키는 전투 스타일이 비슷하여 서로를 인정하는 관계.'),
    (2, 4, 'rival', '기로로와 쿠루루는 성격 차이가 크지만 소대원으로서 협력한다.'),
    (2, 9, 'rival', '기로로와 조루루는 가루루 소대전에서 대결하는 맞수 관계이다.'),

    # ---- Tamama relations ----
    (3, 14, 'enemy', '타마마는 모아를 질투하여 적대시한다. 케로로의 관심을 빼앗기기 때문.'),
    (3, 15, 'friend', '타마마와 모모카는 함께 생활하며 주종 관계이자 동료.'),
    (3, 7, 'rival', '타마마와 타루루는 가루루 소대전에서 대결. 타루루는 타마마의 라이벌이다.'),
    (3, 52, 'subordinate', '타마마는 니시자와 바이오의 경호대에 소속. 바이오의 명령도 따른다.'),

    # ---- Kururu relations ----
    (4, 17, 'friend', '쿠루루와 사부로는 기술적 교류가 있는 사이. 서로의 능력을 인정한다.'),
    (4, 8, 'rival', '쿠루루와 토로로는 해커 대 해커의 라이벌 관계. 토로로는 쿠루루를 넘으려 한다.'),
    (4, 12, 'enemy', '쿠루루는 나츠미에게 종종 실험을 하려다 통쾌하게 당한다.'),
    (4, 13, 'ally', '쿠루루는 아키의 만화 원고 작업을 기술적으로 도와주기도 한다.'),

    # ---- Dororo relations ----
    (5, 16, 'ally', '도로로와 코유키는 같은 닌자로서 깊은 유대감. 함께 수련하며 의지한다.'),
    (5, 36, 'enemy', '도로로와 카게게는 가루루 소대전에서 대결하는 닌자 대 그림자 관계.'),
    (5, 71, 'family', '도로로와 어머니의 관계. 도로로의 트라우마 중 상당수가 어머니와 관련.'),
    (5, 1, 'friend', '도로로는 케로로를 어린 시절부터의 친구로 여기지만, 케로로는 자주 잊는다.'),

    # ---- Human relations ----
    (11, 14, 'friend', '후유키와 모아는 서로를 좋아하는 관계. 모아는 후유키에게 특별한 감정이 있다.'),
    (12, 16, 'friend', '나츠미와 코유키는 가장 친한 친구. 코유키가 전학 온 이후 깊은 우정을 쌓았다.'),
    (12, 17, 'crush', '나츠미는 사부로에게 관심이 있지만 좀처럼 표현하지 못한다.'),
    (11, 12, 'family', '후유키와 나츠미는 남매. 성격은 다르지만 서로를 아끼는 사이.'),
    (13, 12, 'family', '아키와 나츠미는 모녀 관계. 아키는 바쁜 업무 중에도 아이들을 걱정한다.'),
    (13, 11, 'family', '아키와 후유키는 모자 관계. 후유키의 오컬트 취미를 이해해주는 편.'),
    (15, 11, 'crush', '모모카는 후유키를 짝사랑한다. 매번 고백하려다 실패하는 게 일상.'),
    (14, 11, 'crush', '모아는 후유키에게 호감을 가지고 있으며, 지구에 머무는 이유 중 하나.'),

    # ---- Garuru Platoon relations ----
    (6, 9, 'subordinate', '가루루는 조루루의 소대장. 조루루는 가루루의 명령에 충실히 따른다.'),
    (6, 7, 'subordinate', '가루루는 타루루의 소대장. 타루루는 전투력을 인정받아 발탁되었다.'),
    (6, 8, 'subordinate', '가루루는 토로로의 소대장. 토로로는 기술 담당으로 소대에 합류.'),
    (6, 10, 'subordinate', '가루루는 푸루루의 소대장. 푸루루는 의료 담당이다.'),
    (7, 3, 'rival', '타루루와 타마마는 이등병 대 이등병의 라이벌. 타루루가 약간 우세.'),
    (8, 4, 'rival', '토로로와 쿠루루는 천재 해커 대결. 쿠루루가 한 수 위이다.'),
    (9, 5, 'rival', '조루루와 도로로는 암살자 대 닌자의 대결. 과거에 인연이 있다.'),
    (10, 2, 'friend', '푸루루와 기로로는 어린 시절 친구. 기로로의 가루루 소대 시절을 알고 있다.'),

    # ---- Shurara Corps ----
    (31, 1, 'enemy', '슈라라는 케로로에 대한 복수를 위해 군단을 조직한 적 캐릭터.'),
    (31, 36, 'superior', '슈라라는 카게게의 상관. 카게게는 슈라라 군단의 일원이다.'),
    (31, 37, 'superior', '슈라라는 로보보의 상관. 로보보는 슈라라 군단의 로봇 전투원.'),
    (31, 38, 'superior', '슈라라는 메케케의 상관. 메케케는 슈라라 군단의 인형 조종사.'),

    # ---- Misc ----
    (18, 19, 'family', '556(코고로)와 라비는 남매. 라비는 항상 오빠의 뒤처리를 한다.'),
]


def insert_quotes(conn):
    """Insert new quotes."""
    c = conn.cursor()
    c.execute("SELECT MAX(id) FROM quotes")
    max_id = c.fetchone()[0] or 0

    inserted = 0
    for char_id, content, content_kr, episode_id, context in NEW_QUOTES:
        max_id += 1
        c.execute(
            "INSERT INTO quotes (id, character_id, content, content_kr, episode_id, context) VALUES (?, ?, ?, ?, ?, ?)",
            (max_id, char_id, content, content_kr, episode_id, context)
        )
        inserted += 1

    conn.commit()
    print(f"[OK] Quotes inserted: {inserted}")
    return inserted


def create_and_insert_trivia(conn):
    """Create trivia table and insert data."""
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS trivia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fact TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            source TEXT DEFAULT ''
        )
    """)

    inserted = 0
    for fact, category, source in TRIVIA_DATA:
        c.execute(
            "INSERT INTO trivia (fact, category, source) VALUES (?, ?, ?)",
            (fact, category, source)
        )
        inserted += 1

    conn.commit()
    print(f"[OK] Trivia inserted: {inserted}")
    return inserted


def insert_items(conn):
    """Insert new items."""
    c = conn.cursor()
    c.execute("SELECT MAX(id) FROM items")
    max_id = c.fetchone()[0] or 0

    inserted = 0
    for name, name_kr, category, owner, description in NEW_ITEMS:
        max_id += 1
        c.execute(
            "INSERT INTO items (id, name, name_kr, category, owner, description, image_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (max_id, name, name_kr, category, owner, description, '')
        )
        inserted += 1

    conn.commit()
    print(f"[OK] Items inserted: {inserted}")
    return inserted


def insert_relations(conn):
    """Insert new character relations, skipping duplicates."""
    c = conn.cursor()
    c.execute("SELECT MAX(id) FROM character_relations")
    max_id = c.fetchone()[0] or 0

    inserted = 0
    skipped = 0
    for char_from, char_to, relation_type, description in NEW_RELATIONS:
        # Check for existing duplicate
        c.execute(
            "SELECT id FROM character_relations WHERE char_from=? AND char_to=? AND relation_type=?",
            (char_from, char_to, relation_type)
        )
        if c.fetchone():
            skipped += 1
            continue
        max_id += 1
        c.execute(
            "INSERT INTO character_relations (id, char_from, char_to, relation_type, description) VALUES (?, ?, ?, ?, ?)",
            (max_id, char_from, char_to, relation_type, description)
        )
        inserted += 1

    conn.commit()
    print(f"[OK] Character relations inserted: {inserted} (skipped {skipped} duplicates)")
    return inserted


def rebuild_fts(conn):
    """Rebuild FTS indexes for updated tables."""
    c = conn.cursor()

    # Rebuild quotes FTS
    try:
        c.execute("DELETE FROM quotes_fts")
        c.execute("INSERT INTO quotes_fts (rowid, content, content_kr, context) SELECT id, content, content_kr, context FROM quotes")
        print("[OK] quotes_fts rebuilt")
    except Exception as e:
        print(f"[WARN] quotes_fts rebuild failed: {e}")

    # Rebuild items FTS
    try:
        c.execute("DELETE FROM items_fts")
        c.execute("INSERT INTO items_fts (rowid, name, name_kr, description) SELECT id, name, name_kr, description FROM items")
        print("[OK] items_fts rebuilt")
    except Exception as e:
        print(f"[WARN] items_fts rebuild failed: {e}")

    conn.commit()


def print_summary(conn):
    """Print final table counts."""
    c = conn.cursor()
    print("\n========== FINAL TABLE COUNTS ==========")
    tables = ['characters', 'quotes', 'items', 'character_relations', 'trivia',
              'episodes', 'invasion_plans', 'abilities', 'ost', 'voice_actors',
              'military_ranks', 'guestbook', 'board']
    for table in tables:
        try:
            c.execute(f"SELECT COUNT(*) FROM {table}")
            count = c.fetchone()[0]
            print(f"  {table:25s}: {count:>5} rows")
        except Exception:
            pass

    # Trivia breakdown by category
    print("\n========== TRIVIA BY CATEGORY ==========")
    c.execute("SELECT category, COUNT(*) as cnt FROM trivia GROUP BY category ORDER BY cnt DESC")
    for row in c.fetchall():
        print(f"  {row[0]:15s}: {row[1]:>3} entries")

    # Quotes breakdown by character
    print("\n========== QUOTES BY CHARACTER (top 10) ==========")
    c.execute("""
        SELECT c.name, COUNT(q.id) as cnt
        FROM quotes q
        JOIN characters c ON q.character_id = c.id
        GROUP BY q.character_id
        ORDER BY cnt DESC
        LIMIT 10
    """)
    for row in c.fetchall():
        print(f"  {row[0]:20s}: {row[1]:>3} quotes")

    # Relation types breakdown
    print("\n========== RELATIONS BY TYPE ==========")
    c.execute("SELECT relation_type, COUNT(*) as cnt FROM character_relations GROUP BY relation_type ORDER BY cnt DESC")
    for row in c.fetchall():
        print(f"  {row[0]:15s}: {row[1]:>3} relations")

    # Item categories breakdown
    print("\n========== ITEMS BY CATEGORY ==========")
    c.execute("SELECT category, COUNT(*) as cnt FROM items GROUP BY category ORDER BY cnt DESC")
    for row in c.fetchall():
        print(f"  {row[0]:15s}: {row[1]:>3} items")


def main():
    print("=" * 50)
    print("Keroro Archive - Bulk Data Insertion")
    print("=" * 50)
    print()

    conn = get_connection()

    try:
        q = insert_quotes(conn)
        t = create_and_insert_trivia(conn)
        i = insert_items(conn)
        r = insert_relations(conn)

        print(f"\n--- Total new records: {q + t + i + r} ---")

        rebuild_fts(conn)
        print_summary(conn)

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        conn.close()

    print("\n[DONE] All data inserted successfully.")


if __name__ == '__main__':
    main()
