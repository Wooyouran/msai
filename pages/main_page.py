"""
메인 페이지 모듈
냉장고 재료 관리 시스템의 메인 메뉴 페이지
"""

import streamlit as st

def show_main_menu():
    """메인 페이지 메뉴 표시 - 새로운 디자인"""
    
    # 강력한 CSS 스타일링
    st.markdown("""
    <style>
    /* 전체 페이지 연한 노란색 배경 */
    .stApp {
        background-color: #FFF9C4 !important;
    }
    
    .main {
        background-color: #FFF9C4 !important;
        min-height: 100vh !important;
    }
    
    .main .block-container {
        background-color: #FFF9C4 !important;
        padding: 2rem !important;
        max-width: 700px !important;
    }
    
    /* 버튼 스타일링 */
    .stButton > button {
        width: 100% !important;
        max-width: 350px !important;
        height: 70px !important;
        border-radius: 15px !important;
        border: 2px solid #e0e0e0 !important;
        background: linear-gradient(145deg, #ffffff, #f8f9fa) !important;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1) !important;
        transition: all 0.3s ease !important;
        font-size: 1.3rem !important;
        font-weight: bold !important;
        color: #333 !important;
        text-align: center !important;
        white-space: pre-line !important;
        line-height: 1.2 !important;
        margin: 8px auto !important;
        display: block !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(0,0,0,0.15) !important;
        border-color: #4CAF50 !important;
        background: linear-gradient(145deg, #f0f8ff, #e6f3ff) !important;
    }
    
    /* 컬럼 스타일링 */
    .stColumns {
        gap: 0 !important;
    }
    
    div[data-testid="column"] {
        padding: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 제목과 부제목
    st.markdown("""
    <div style="
        background-color: white;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 2rem;
    ">
        <h1 style="font-size: 2.2rem; font-weight: bold; color: #333; margin-bottom: 1rem;">
            🥬 냉장고 재료 관리 시스템
        </h1>
        <p style="font-size: 1.1rem; color: #666; margin: 0;">
            ChatGPT-5 멀티모달 분석기를 활용한 스마트 냉장고 관리
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 버튼들을 세로로 배치
    if st.button("📸\n\n재료 등록하기", use_container_width=True, key="register_btn"):
        st.session_state.current_page = "재료 등록하기"
        st.rerun()
    
    if st.button("📋\n\n재료 리스트 보기", use_container_width=True, key="list_btn"):
        st.session_state.current_page = "재료 리스트 보기"
        st.rerun()
    
    if st.button("🍳\n\n재료 사용하기", use_container_width=True, key="use_btn"):
        st.session_state.current_page = "재료 사용하기"
        st.rerun()
    
    if st.button("🍽️\n\n레시피 추천 받기", use_container_width=True, key="recipe_btn"):
        st.session_state.current_page = "레시피 추천 받기"
        st.rerun()
    
    # URL 파라미터 처리
    if st.query_params.get("register"):
        st.session_state.current_page = "재료 등록하기"
        st.rerun()
    elif st.query_params.get("list"):
        st.session_state.current_page = "재료 리스트 보기"
        st.rerun()
    elif st.query_params.get("use"):
        st.session_state.current_page = "재료 사용하기"
        st.rerun()
    elif st.query_params.get("recipe"):
        st.session_state.current_page = "레시피 추천 받기"
        st.rerun()
    
    # 현재 페이지가 메인 페이지가 아닌 경우 뒤로가기 버튼 표시
    if st.session_state.current_page != "메인 페이지":
        st.markdown("---")
        if st.button("🏠 메인으로 돌아가기", use_container_width=True):
            st.session_state.current_page = "메인 페이지"
            st.rerun()
