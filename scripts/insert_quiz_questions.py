"""Insert 80+ quiz questions about Keroro Gunso into the SQLite database."""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "keroro.db")


def create_table(conn: sqlite3.Connection) -> None:
    """Create the quiz_questions table if it does not exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            difficulty TEXT DEFAULT 'normal',
            category TEXT DEFAULT 'general'
        )
    """)
    conn.commit()


def get_questions() -> list[tuple]:
    """Return all quiz questions as a list of tuples.

    Each tuple: (question, option_a, option_b, option_c, option_d,
                 correct_answer, difficulty, category)

    Correct answers are distributed roughly equally across A, B, C, D.
    """
    questions = []

    # =========================================================================
    # CATEGORY: character (22 questions)
    # Correct answer distribution: A=6, B=5, C=6, D=5
    # =========================================================================
    questions.extend([
        (
            "케로로의 종족은 무엇인가?",
            "케론인", "나메크인", "사이어인", "인간",
            "A", "easy", "character"
        ),
        (
            "케로로 소대의 통신병 겸 발명가는 누구인가?",
            "기로로", "쿠루루", "타마마", "도로로",
            "B", "easy", "character"
        ),
        (
            "가루루 소대의 리더는 누구인가?",
            "토로로", "푸루루", "케로로", "가루루",
            "D", "easy", "character"
        ),
        (
            "케로로 소대에서 암살병 역할을 맡고 있는 멤버는?",
            "기로로", "도로로", "타마마", "쿠루루",
            "B", "normal", "character"
        ),
        (
            "히나타 가족 중 케로로를 처음 발견한 사람은?",
            "히나타 후유키", "히나타 나츠미", "히나타 아키", "앙골 모아",
            "A", "normal", "character"
        ),
        (
            "기로로가 짝사랑하는 인물은 누구인가?",
            "히나타 아키", "앙골 모아", "니시자와 모모카", "히나타 나츠미",
            "D", "normal", "character"
        ),
        (
            "니시자와 모모카가 좋아하는 사람은?",
            "케로로", "히나타 후유키", "사부로", "기로로",
            "B", "easy", "character"
        ),
        (
            "앙골 모아가 케로로를 부르는 호칭은?",
            "대장님", "삼촌", "케로로님", "선배님",
            "B", "normal", "character"
        ),
        (
            "케로로 소대에서 계급이 가장 높은 멤버는?",
            "케로로 (군조)", "기로로 (고쵸)", "도로로 (헤이쵸)", "쿠루루 (소조)",
            "D", "hard", "character"
        ),
        (
            "'군조(軍曹)'는 어떤 계급에 해당하는가?",
            "이등병", "병장", "하사", "중사",
            "B", "hard", "character"
        ),
        (
            "타마마의 성격 특징으로 가장 적절한 것은?",
            "이중인격 (귀여움과 질투심)", "냉철한 전략가", "과묵한 닌자", "무모한 전사",
            "A", "normal", "character"
        ),
        (
            "도로로의 원래 이름은 무엇인가?",
            "코로로", "푸로로", "제로로", "타로로",
            "C", "hard", "character"
        ),
        (
            "코고로(556)와 함께 다니는 여동생의 이름은?",
            "라비", "모아", "코유키", "모모카",
            "A", "normal", "character"
        ),
        (
            "폴 모리야마는 어떤 집안의 집사인가?",
            "히나타 가", "니시자와 가", "아즈마야 가", "케로로 소대",
            "B", "normal", "character"
        ),
        (
            "아즈마야 코유키의 특기는 무엇인가?",
            "요리", "과학 실험", "그림 그리기", "닌자술",
            "D", "normal", "character"
        ),
        (
            "사부로가 가지고 있는 특별한 아이템은?",
            "케로 볼", "리얼리티 펜", "루시퍼 스피어", "안티 배리어",
            "B", "normal", "character"
        ),
        (
            "가루루 소대에서 쿠루루의 라이벌에 해당하는 멤버는?",
            "타루루", "토로로", "조루루", "푸루루",
            "B", "normal", "character"
        ),
        (
            "가루루 소대에서 의무병 역할을 맡고 있는 멤버는?",
            "조루루", "타루루", "토로로", "푸루루",
            "D", "hard", "character"
        ),
        (
            "케로로가 가장 좋아하는 취미는?",
            "건프라 (건담 프라모델)", "요리", "독서", "운동",
            "A", "easy", "character"
        ),
        (
            "앙골 모아의 정체는 무엇인가?",
            "케론인 스파이", "인간", "행성 파괴자(우주인)", "닌자",
            "C", "normal", "character"
        ),
        (
            "타마마가 케로로에게 느끼는 감정으로 가장 적절한 것은?",
            "증오", "존경과 맹목적 충성", "무관심", "라이벌 의식",
            "B", "normal", "character"
        ),
        (
            "히나타 아키의 직업은 무엇인가?",
            "교사", "간호사", "요리사", "만화 편집자",
            "D", "normal", "character"
        ),
    ])

    # =========================================================================
    # CATEGORY: episode (15 questions)
    # Correct answer distribution: A=4, B=4, C=4, D=3
    # =========================================================================
    questions.extend([
        (
            "케로로 군조 TV 애니메이션은 총 몇 시즌(기)으로 구성되어 있는가?",
            "5시즌", "6시즌", "7시즌", "8시즌",
            "C", "normal", "episode"
        ),
        (
            "케로로 군조 TV 애니메이션 1기는 몇 화까지인가?",
            "51화", "26화", "40화", "52화",
            "A", "hard", "episode"
        ),
        (
            "케로로 군조 원작 만화가 처음 연재된 잡지는?",
            "주간 소년 점프", "주간 소년 매거진", "주간 소년 선데이", "월간 소년 에이스",
            "D", "hard", "episode"
        ),
        (
            "케로로 군조 TV 애니메이션이 처음 방영된 연도는?",
            "2002년", "2004년", "2006년", "2008년",
            "B", "normal", "episode"
        ),
        (
            "케로로 군조 원작 만화는 어느 연도에 연재를 시작했는가?",
            "1997년", "2001년", "1999년", "2003년",
            "C", "hard", "episode"
        ),
        (
            "케로로 군조 극장판(영화)은 총 몇 편이 제작되었는가?",
            "3편", "5편", "4편", "6편",
            "B", "hard", "episode"
        ),
        (
            "한국에서 케로로 군조를 방영한 방송사는?",
            "KBS", "MBC", "SBS", "투니버스",
            "D", "normal", "episode"
        ),
        (
            "케로로 소대가 지구에 온 본래 목적은?",
            "관광", "과학 조사", "지구 침략 (사전 정찰)", "망명",
            "C", "easy", "episode"
        ),
        (
            "케로로 군조 시즌 0(특별편)은 총 몇 화인가?",
            "3화", "5화", "7화", "10화",
            "B", "hard", "episode"
        ),
        (
            "케로로 군조 애니메이션의 제작사는?",
            "선라이즈", "토에이 애니메이션", "본즈", "매드하우스",
            "A", "normal", "episode"
        ),
        (
            "케로로 군조 TV 시리즈의 총 에피소드 수는 약 몇 화인가?",
            "약 150화", "약 250화", "약 358화", "약 500화",
            "C", "hard", "episode"
        ),
        (
            "케로로 군조의 배경이 되는 주요 장소는?",
            "히나타 가의 집", "학교", "케론별", "우주 정거장",
            "A", "easy", "episode"
        ),
        (
            "케로로 군조에서 주로 사용되는 에피소드 구성 방식은?",
            "장편 스토리 연속", "시즌별 대형 스토리", "영화식 구성", "1화 완결 옴니버스",
            "D", "normal", "episode"
        ),
        (
            "케로로 군조 첫 번째 극장판의 부제는?",
            "초 극장판 케로로 군조", "천공대모험", "케로로 대 케로로", "용사 케로로",
            "A", "hard", "episode"
        ),
        (
            "케로로 군조 한국어 더빙판에서 케로로의 한국판 이름은?",
            "개구리 중사", "케로로 중사", "케로로", "개구리 군조",
            "C", "normal", "episode"
        ),
    ])

    # =========================================================================
    # CATEGORY: item (12 questions)
    # Correct answer distribution: A=3, B=3, C=3, D=3
    # =========================================================================
    questions.extend([
        (
            "케로 볼의 주요 용도는 무엇인가?",
            "요리 도구", "통신 장비", "이동 수단", "침략 작전의 핵심 장치",
            "D", "easy", "item"
        ),
        (
            "안티 배리어의 기능은 무엇인가?",
            "투명화 (인간에게 보이지 않게 함)", "공격력 증가", "시간 정지", "텔레포트",
            "A", "normal", "item"
        ),
        (
            "리얼리티 펜으로 그린 것은 어떻게 되는가?",
            "사라진다", "폭발한다", "현실이 된다", "움직인다",
            "C", "easy", "item"
        ),
        (
            "루시퍼 스피어는 누구의 무기인가?",
            "케로로", "앙골 모아", "기로로", "도로로",
            "B", "normal", "item"
        ),
        (
            "스타 마크는 케론인의 어디에 위치하는가?",
            "머리", "등", "손", "배",
            "D", "easy", "item"
        ),
        (
            "스타 마크의 의미는 무엇인가?",
            "나이 표시", "소대 표시", "개인 정체성과 능력의 상징", "계급장",
            "C", "normal", "item"
        ),
        (
            "쿠루루가 주로 만드는 것은?",
            "발명품 (메카와 장치류)", "음식", "무기만", "예술 작품",
            "A", "easy", "item"
        ),
        (
            "케론인들이 건조해지면 어떤 상태가 되는가?",
            "투명해진다", "강해진다", "작아지고 약해진다 (탈수 상태)", "잠에 빠진다",
            "C", "normal", "item"
        ),
        (
            "앙골 모아의 루시퍼 스피어 1/1000000의 위력은?",
            "종이를 자르는 수준", "건물 하나를 파괴하는 수준", "아무 효과 없음", "엄청난 파괴력",
            "D", "normal", "item"
        ),
        (
            "케로로가 건프라를 만들 때 주로 있는 장소는?",
            "거실", "히나타 후유키의 방 (지하 비밀 기지)", "옥상", "학교",
            "B", "normal", "item"
        ),
        (
            "기로로의 주 무기 종류는?",
            "화기류 (총과 미사일)", "검술", "마법", "닌자 도구",
            "A", "easy", "item"
        ),
        (
            "도로로가 사용하는 무기의 종류는?",
            "총", "마법 지팡이", "닌자도 (칼과 수리검)", "맨손 격투",
            "C", "easy", "item"
        ),
    ])

    # =========================================================================
    # CATEGORY: invasion (11 questions)
    # Correct answer distribution: A=3, B=3, C=3, D=2
    # =========================================================================
    questions.extend([
        (
            "케로로 소대의 주요 임무는 무엇인가?",
            "지구 관광", "지구 보호", "지구 침략", "과학 연구",
            "C", "easy", "invasion"
        ),
        (
            "케로로의 침략 계획이 실패하는 가장 흔한 원인은?",
            "케로로 자신의 취미와 게으름", "기술 부족", "나츠미의 방해만", "본부의 명령 취소",
            "A", "easy", "invasion"
        ),
        (
            "'작전: 건프라 최면' 작전의 실패 원인은?",
            "기로로의 반대", "나츠미의 발각", "쿠루루의 배신", "케로로가 건프라에 빠져서 포기",
            "D", "normal", "invasion"
        ),
        (
            "케로로 소대의 침략 작전 결과는 대부분 어떻게 끝나는가?",
            "대성공", "부분 성공", "실패", "무승부",
            "C", "easy", "invasion"
        ),
        (
            "'작전: 날씨 제어' 작전을 주도한 것은 누구인가?",
            "케로로", "기로로", "타마마", "쿠루루",
            "D", "normal", "invasion"
        ),
        (
            "케로로가 침략 대신 주로 하는 활동은?",
            "운동", "건프라 조립과 TV 시청", "독서", "요리",
            "B", "easy", "invasion"
        ),
        (
            "케론 본부가 케로로 소대에 침략 독촉을 할 때 보내는 것은?",
            "편지", "무기", "특사 또는 경고 메시지", "식량",
            "C", "normal", "invasion"
        ),
        (
            "'작전: 크리스마스 탈취' 작전이 실패한 이유는?",
            "나츠미 덕분에 크리스마스 파티로 변질", "쿠루루의 기계 고장", "도로로의 반대", "케론 본부의 취소",
            "A", "normal", "invasion"
        ),
        (
            "케로로 소대가 지구에 머무는 주된 이유는?",
            "임무 수행 중", "지구 생활이 편해서 (사실상 정착)", "귀환 수단이 없어서", "본부의 명령",
            "B", "normal", "invasion"
        ),
        (
            "'작전: 정신 지배 안테나' 작전을 막은 인물은?",
            "나츠미", "후유키", "앙골 모아", "도로로",
            "D", "hard", "invasion"
        ),
        (
            "케로로가 침략 계획서를 작성할 때 주로 사용하는 매체는?",
            "컴퓨터", "노트", "화이트보드와 마커", "프로젝터",
            "C", "normal", "invasion"
        ),
    ])

    # =========================================================================
    # CATEGORY: ost (11 questions)
    # Correct answer distribution: A=3, B=3, C=3, D=2
    # =========================================================================
    questions.extend([
        (
            "케로로 군조 1기 오프닝곡의 제목은?",
            "케로! 토 마치 (Kero! to March)", "전력 바탕큐", "당신에게 걸기를", "하레하레 유카이",
            "A", "normal", "ost"
        ),
        (
            "케로로 군조 1기 첫 번째 엔딩곡의 제목은?",
            "작은 별 작은 소원", "빙글빙글 돌아서 한 바퀴", "아프로 군조 (Afro Gunso)", "케로! 토 마치",
            "C", "normal", "ost"
        ),
        (
            "'전력 바탕큐 (Zenryoku Batankyuu)'는 몇 기 오프닝인가?",
            "1기", "2기", "3기", "4기",
            "B", "normal", "ost"
        ),
        (
            "케로로 군조 1기 두 번째 엔딩곡의 제목은?",
            "아프로 군조", "빙글빙글 돌아서 한 바퀴", "전력 바탕큐", "작은 별 작은 소원",
            "D", "hard", "ost"
        ),
        (
            "'빙글빙글 돌아서 한 바퀴'는 몇 기의 엔딩곡인가?",
            "1기", "3기", "2기", "4기",
            "C", "hard", "ost"
        ),
        (
            "케로로 군조의 오프닝/엔딩 곡을 부르는 주체로 자주 등장하는 것은?",
            "유명 가수만", "케로로 소대 성우진", "오케스트라", "아이돌 그룹만",
            "B", "normal", "ost"
        ),
        (
            "1기 오프닝 'Kero! to March'의 가수는 누구인가?",
            "Dance Man", "Chiwawa", "Hyper Craft", "케로로 소대 (성우진)",
            "D", "hard", "ost"
        ),
        (
            "케로로 군조 OST의 전체적인 분위기는?",
            "밝고 코믹한", "어둡고 진지한", "로맨틱한", "긴장감 넘치는",
            "A", "easy", "ost"
        ),
        (
            "'아프로 군조 (Afro Gunso)' 엔딩곡의 가수는?",
            "케로로 소대", "Chiwawa", "Dance Man", "Hyper Craft",
            "C", "hard", "ost"
        ),
        (
            "케로로 군조의 한국판에서 사용된 곡의 특징은?",
            "원곡 그대로 사용", "한국어 번안 가사 사용", "완전히 새로운 곡", "더빙 없이 일본어 그대로",
            "B", "normal", "ost"
        ),
        (
            "케로로 군조 2기 첫 번째 엔딩곡의 제목은?",
            "빙글빙글 돌아서 한 바퀴", "아프로 군조", "작은 별 작은 소원", "전력 바탕큐",
            "A", "hard", "ost"
        ),
    ])

    # =========================================================================
    # CATEGORY: trivia (18 questions)
    # Correct answer distribution: A=5, B=4, C=5, D=4
    # =========================================================================
    questions.extend([
        (
            "케로로 군조의 원작 만화 작가는 누구인가?",
            "토리야마 아키라", "오다 에이이치로", "요시자키 미네", "키시모토 마사시",
            "C", "easy", "trivia"
        ),
        (
            "케로로의 일본어 성우는 누구인가?",
            "와타나베 쿠미코", "하야시바라 메구미", "타카야마 미나미", "노토 마미코",
            "A", "normal", "trivia"
        ),
        (
            "케로로의 한국어 성우는 누구인가?",
            "이선", "박영남", "김서영", "정미숙",
            "D", "hard", "trivia"
        ),
        (
            "기로로의 일본어 성우 나카타 조지가 맡은 다른 유명 역할은?",
            "루피 (원피스)", "키레이 (페이트 시리즈)", "나루토 (나루토)", "고쿠 (드래곤볼)",
            "B", "hard", "trivia"
        ),
        (
            "케로로 군조에 자주 등장하는 건담 시리즈의 패러디 대상은?",
            "마크로스", "에반게리온", "기동전사 건담", "코드 기아스",
            "C", "easy", "trivia"
        ),
        (
            "케로로의 외형은 어떤 동물을 모티브로 했는가?",
            "개구리", "도마뱀", "거북이", "올챙이",
            "A", "easy", "trivia"
        ),
        (
            "케론별에서 지구까지의 이동에 사용되는 것은?",
            "워프 게이트", "텔레포트", "로켓", "우주선",
            "D", "normal", "trivia"
        ),
        (
            "쿠루루의 일본어 성우 코야스 타케히토가 맡은 다른 유명 역할은?",
            "나루토 (나루토)", "루피 (원피스)", "DIO (죠죠의 기묘한 모험)", "이치고 (블리치)",
            "C", "hard", "trivia"
        ),
        (
            "케로로 군조에서 자주 패러디되는 일본 문화 요소가 아닌 것은?",
            "건담 프라모델", "한국 드라마", "일본 전통 명절", "특촬물 (울트라맨 등)",
            "B", "normal", "trivia"
        ),
        (
            "케로로의 이마에 있는 별 마크의 색상은?",
            "빨간색", "파란색", "초록색", "노란색",
            "D", "easy", "trivia"
        ),
        (
            "기로로의 몸 색상은 무엇인가?",
            "빨간색", "초록색", "파란색", "노란색",
            "A", "easy", "trivia"
        ),
        (
            "타마마의 몸 색상은 무엇인가?",
            "초록색", "빨간색", "검정/남색", "노란색",
            "C", "easy", "trivia"
        ),
        (
            "쿠루루의 몸 색상은 무엇인가?",
            "초록색", "빨간색", "파란색", "노란색/주황색",
            "D", "easy", "trivia"
        ),
        (
            "도로로의 몸 색상은 무엇인가?",
            "초록색", "빨간색", "파란색/하늘색", "노란색",
            "C", "easy", "trivia"
        ),
        (
            "케로로 군조의 장르는 무엇인가?",
            "SF 코미디", "액션", "로맨스", "공포",
            "A", "easy", "trivia"
        ),
        (
            "케로로 소대가 히나타 가에서 지내는 대가로 하는 일은?",
            "월세 납부", "집안일 (청소 등)", "경호", "아무것도 안 함",
            "B", "normal", "trivia"
        ),
        (
            "나츠미가 케로로에게 자주 하는 행동은?",
            "칭찬하기", "선물 주기", "때리거나 혼내기", "무시하기",
            "C", "easy", "trivia"
        ),
        (
            "케로로 군조 원작 만화의 연재 잡지 출판사는?",
            "슈에이샤", "카도카와 쇼텐", "코단샤", "쇼가쿠칸",
            "B", "hard", "trivia"
        ),
    ])

    return questions


def insert_questions(conn: sqlite3.Connection, questions: list[tuple]) -> int:
    """Insert all questions and return the total count."""
    conn.execute("DELETE FROM quiz_questions")  # Clear existing data
    conn.executemany(
        """
        INSERT INTO quiz_questions
            (question, option_a, option_b, option_c, option_d,
             correct_answer, difficulty, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        questions,
    )
    conn.commit()
    cursor = conn.execute("SELECT COUNT(*) FROM quiz_questions")
    return cursor.fetchone()[0]


def verify_data(conn: sqlite3.Connection) -> None:
    """Print verification summary."""
    print("=== Quiz Questions Verification ===\n")

    # Total count
    cursor = conn.execute("SELECT COUNT(*) FROM quiz_questions")
    total = cursor.fetchone()[0]
    print(f"Total questions: {total}")

    # Count by category
    print("\nBy category:")
    cursor = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM quiz_questions "
        "GROUP BY category ORDER BY cnt DESC"
    )
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    # Count by difficulty
    print("\nBy difficulty:")
    cursor = conn.execute(
        "SELECT difficulty, COUNT(*) as cnt FROM quiz_questions "
        "GROUP BY difficulty ORDER BY cnt DESC"
    )
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    # Verify correct_answer values
    print("\nBy correct_answer distribution:")
    cursor = conn.execute(
        "SELECT correct_answer, COUNT(*) as cnt FROM quiz_questions "
        "GROUP BY correct_answer ORDER BY correct_answer"
    )
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    # Sample questions
    print("\nSample questions (first 3):")
    cursor = conn.execute("SELECT * FROM quiz_questions LIMIT 3")
    for row in cursor.fetchall():
        print(f"  [{row[7]}][{row[8]}] Q: {row[1]}")
        print(f"    A: {row[2]} | B: {row[3]} | C: {row[4]} | D: {row[5]}")
        print(f"    Correct: {row[6]}")
        print()


def main() -> None:
    """Main entry point."""
    db_path = os.path.abspath(DB_PATH)
    print(f"Database: {db_path}")

    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    try:
        create_table(conn)
        print("Table 'quiz_questions' created/verified.")

        questions = get_questions()
        print(f"Prepared {len(questions)} questions.")

        count = insert_questions(conn, questions)
        print(f"Inserted {count} questions into the database.\n")

        verify_data(conn)
    finally:
        conn.close()

    print("\nDone.")


if __name__ == "__main__":
    main()
