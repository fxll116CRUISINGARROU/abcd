import streamlit as st
import random
import json
import os
from pathlib import Path
import hashlib
from datetime import datetime

st.set_page_config(page_title="찍기 실력 테스트", layout="centered")
st.title("🎯 찍기 실력 테스트")

# 데이터 폴더 설정 (절대경로)
DATA_DIR = Path(__file__).parent / "user_data"
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"
SCORES_FILE = DATA_DIR / "scores.json"

# 디버그 정보 (개발용)
with st.sidebar:
    with st.expander("📊 데이터 저장 상태", expanded=False):
        st.write(f"**데이터 폴더:**")
        st.code(str(DATA_DIR))
        if USERS_FILE.exists():
            st.write("✅ 사용자 데이터 파일 존재")
        if SCORES_FILE.exists():
            st.write("✅ 점수 데이터 파일 존재")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    try:
        if USERS_FILE.exists():
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"사용자 데이터 로드 오류: {e}")
    return {}

def save_users(users):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"사용자 데이터 저장 오류: {e}")

def load_scores():
    try:
        if SCORES_FILE.exists():
            with open(SCORES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"점수 데이터 로드 오류: {e}")
    return {}

def save_scores(scores):
    try:
        with open(SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(scores, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"점수 데이터 저장 오류: {e}")

def register_user(username, password):
    users = load_users()
    if username in users:
        return False, "이미 존재하는 닉네임입니다."
    users[username] = hash_password(password)
    save_users(users)
    return True, "회원가입 성공!"

def login_user(username, password):
    users = load_users()
    if username not in users:
        return False, "존재하지 않는 닉네임입니다."
    if users[username] != hash_password(password):
        return False, "비밀번호가 틀렸습니다."
    return True, "로그인 성공!"

def save_score(username, score, accuracy):
    try:
        scores = load_scores()
        if username not in scores:
            scores[username] = []
        scores[username].append({
            "score": score,
            "accuracy": accuracy,
            "timestamp": datetime.now().isoformat()
        })
        save_scores(scores)
        return True
    except Exception as e:
        st.error(f"점수 저장 오류: {e}")
        return False

def get_ranking():
    scores = load_scores()
    ranking = []
    for username, score_list in scores.items():
        if score_list:
            best_score = max([s["score"] for s in score_list])
            avg_accuracy = sum([s["accuracy"] for s in score_list]) / len(score_list)
            # 첫 시도 시간 (가장 오래된 시도)
            first_attempt_time = score_list[0].get("timestamp", "")
            ranking.append({
                "username": username,
                "best_score": best_score,
                "avg_accuracy": avg_accuracy,
                "attempts": len(score_list),
                "first_attempt_time": first_attempt_time
            })
    # 정렬 기준: 1) 최고점 (높음), 2) 평균정확도 (높음), 3) 첫시도시간 (빠름)
    return sorted(
        ranking,
        key=lambda x: (-x["best_score"], -x["avg_accuracy"], x["first_attempt_time"])
    )

def display_ranking():
    """랭킹 표시"""
    st.subheader("🏆 전체 랭킹")
    ranking = get_ranking()
    if ranking:
        for idx, rank in enumerate(ranking, 1):
            if idx == 1:
                medal = "🥇"
            elif idx == 2:
                medal = "🥈"
            elif idx == 3:
                medal = "🥉"
            else:
                medal = f"{idx}."

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.write(f"{medal} {rank['username']}")
            with col2:
                st.write(f"최고점: {rank['best_score']}")
            with col3:
                st.write(f"평균정확도: {rank['avg_accuracy']:.1f}%")
            with col4:
                st.write(f"시도: {rank['attempts']}회")
    else:
        st.info("아직 기록이 없습니다.")

# 초기화
if "questions" not in st.session_state:
    st.session_state.questions = []
    st.session_state.answers = [None] * 10
    st.session_state.score = 0
    st.session_state.combo = 0
    st.session_state.test_started = False
    st.session_state.test_finished = False
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.current_question_index = 0
    st.session_state.answered_questions = set()
    st.session_state.score_saved = False

def generate_questions():
    """10개의 랜덤 문제 생성"""
    questions = []
    for i in range(10):
        correct_index = random.randint(0, 9)
        choices = [f"{j+1}번" for j in range(10)]
        questions.append({
            "number": i + 1,
            "correct_answer": correct_index,
            "choices": choices
        })
    return questions

# 로그인/회원가입 UI
if not st.session_state.logged_in:
    tab1, tab2, tab3 = st.tabs(["🔐 로그인", "✍️ 회원가입", "🏆 랭킹"])

    with tab1:
        st.subheader("로그인")
        login_username = st.text_input("닉네임", key="login_username")
        login_password = st.text_input("비밀번호", type="password", key="login_password")
        if st.button("로그인", use_container_width=True):
            success, msg = login_user(login_username, login_password)
            if success:
                st.session_state.logged_in = True
                st.session_state.username = login_username
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    with tab2:
        st.subheader("회원가입")
        reg_username = st.text_input("닉네임", key="reg_username")
        reg_password = st.text_input("비밀번호", type="password", key="reg_password")
        reg_password_confirm = st.text_input("비밀번호 확인", type="password", key="reg_password_confirm")
        if st.button("가입하기", use_container_width=True):
            if not reg_username:
                st.error("닉네임을 입력해주세요.")
            elif not reg_password:
                st.error("비밀번호를 입력해주세요.")
            elif reg_password != reg_password_confirm:
                st.error("비밀번호가 일치하지 않습니다.")
            else:
                success, msg = register_user(reg_username, reg_password)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

    with tab3:
        display_ranking()

# 로그인 후 콘텐츠
else:
    # 로그인 후 사이드바
    with st.sidebar:
        st.write(f"**👤 {st.session_state.username}**")

        st.divider()

        tab_rank, tab_logout = st.tabs(["🏆 랭킹", "🚪 로그아웃"])

        with tab_rank:
            display_ranking()

        with tab_logout:
            st.write("정말 로그아웃하시겠습니까?")
            if st.button("로그아웃 확인", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.test_started = False
                st.session_state.test_finished = False
                st.rerun()

    # 테스트 시작 또는 진행
    if not st.session_state.test_started:
        st.subheader("테스트 시작")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("테스트 시작", use_container_width=True):
                st.session_state.questions = generate_questions()
                st.session_state.test_started = True
                st.session_state.answers = [None] * 10
                st.session_state.score = 0
                st.session_state.combo = 0
                st.session_state.current_question_index = 0
                st.session_state.answered_questions = set()
                st.rerun()
    elif not st.session_state.test_finished:
        # 테스트 진행 중 - 한 문제씩 표시
        current_q_idx = st.session_state.current_question_index
        q = st.session_state.questions[current_q_idx]

        # 진행 상황 표시
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("현재 점수", st.session_state.score)
        with col2:
            st.metric("연속 정답", st.session_state.combo)
        with col3:
            st.metric("점수 배수", f"x{2**st.session_state.combo}")
        with col4:
            st.metric("진행도", f"{current_q_idx + 1}/10")

        st.divider()

        # 문제 표시
        st.markdown(f"### 📌 문제 {q['number']}/10")

        # 이미 답변한 경우
        if current_q_idx in st.session_state.answered_questions:
            st.info(f"✅ 이미 답변했습니다: {q['choices'][st.session_state.answers[current_q_idx]]}")
            selected = st.session_state.answers[current_q_idx]
            can_select = False
        else:
            # 선택지 표시
            selected = st.radio(
                "정답을 선택하세요:",
                options=range(10),
                format_func=lambda x: q['choices'][x],
                key=f"q_{current_q_idx}",
                horizontal=True,
                label_visibility="collapsed"
            )
            can_select = True

        st.divider()

        # 버튼
        col1, col2, col3 = st.columns(3)

        with col1:
            if current_q_idx > 0:
                if st.button("◀ 이전", use_container_width=True):
                    st.session_state.current_question_index -= 1
                    st.rerun()

        with col2:
            if can_select:
                if st.button("답변 및 다음 →", use_container_width=True):
                    # 답변 저장
                    st.session_state.answers[current_q_idx] = selected
                    st.session_state.answered_questions.add(current_q_idx)

                    # 점수 계산 (실시간)
                    is_correct = selected == q['correct_answer']
                    if is_correct:
                        st.session_state.combo += 1
                        points = 1 * (2 ** (st.session_state.combo - 1))
                        st.session_state.score += points
                    else:
                        st.session_state.combo = 0

                    # 다음 문제로 이동 또는 완료
                    if current_q_idx < 9:
                        st.session_state.current_question_index += 1
                    else:
                        st.session_state.test_finished = True

                    st.rerun()
            else:
                if st.button("다음 →", use_container_width=True):
                    if current_q_idx < 9:
                        st.session_state.current_question_index += 1
                    else:
                        st.session_state.test_finished = True
                    st.rerun()

        with col3:
            if st.button("테스트 종료", use_container_width=True):
                st.session_state.test_finished = True
                st.rerun()

    # 결과 표시
    if st.session_state.test_finished:
        st.success("🎉 테스트 완료!")

        correct_count = sum(
            1 for i, q in enumerate(st.session_state.questions)
            if st.session_state.answers[i] == q['correct_answer']
        )
        accuracy = (correct_count / 10) * 100

        # 점수 저장 (한 번만)
        if not st.session_state.score_saved:
            save_score(st.session_state.username, st.session_state.score, accuracy)
            st.session_state.score_saved = True
            st.rerun()  # 저장 후 재실행해서 랭킹 즉시 업데이트

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("최종 점수", st.session_state.score)
        with col2:
            st.metric("정답 개수", f"{correct_count}/10")
        with col3:
            st.metric("정확도", f"{accuracy:.1f}%")

        st.divider()

        # 상세 결과
        st.subheader("📋 상세 결과")
        for i, q in enumerate(st.session_state.questions):
            is_correct = st.session_state.answers[i] == q['correct_answer']
            status = "✅ 정답" if is_correct else "❌ 오답"

            col1, col2, col3 = st.columns([1, 3, 3])
            with col1:
                st.write(f"문제 {q['number']}")
            with col2:
                st.write(f"선택: {q['choices'][st.session_state.answers[i]]}")
            with col3:
                st.write(f"정답: {q['choices'][q['correct_answer']]} {status}")

        st.divider()

        # 버튼
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("다시 시작", use_container_width=True):
                st.session_state.questions = []
                st.session_state.answers = [None] * 10
                st.session_state.score = 0
                st.session_state.combo = 0
                st.session_state.test_started = False
                st.session_state.test_finished = False
                st.session_state.current_question_index = 0
                st.session_state.answered_questions = set()
                st.session_state.score_saved = False
                st.rerun()
        with col2:
            if st.button("로그아웃", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.test_started = False
                st.session_state.test_finished = False
                st.session_state.score_saved = False
                st.rerun()
