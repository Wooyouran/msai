"""
Streamlit ChatGPT-5 멀티모달 분석기
냉장고 재료 관리 및 레시피 추천 시스템

메인 애플리케이션 파일 - 각 페이지 모듈을 import하여 사용
"""

import streamlit as st
import os

# 페이지 모듈들 import
from pages.main_page import show_main_menu
from pages.ingredient_registration import ingredient_registration_page
from pages.ingredient_list import ingredient_list_page
from pages.ingredient_usage import ingredient_usage_page
from pages.recipe_recommendation import recipe_recommendation_page


# 페이지 설정
st.set_page_config(
    page_title="냉장고 식재료 관리 어시스턴트",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 사이드바만 숨기기
st.markdown("""
<style>
    section[data-testid="stSidebar"] {display: none;}
    section[data-testid="stSidebar"] > div {display: none;}
    .stApp > div > div:first-child {display: none;}
    .css-1d391kg {display: none;}
    .css-1rs6os {display: none;}
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'ingredients' not in st.session_state:
    st.session_state.ingredients = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = "메인 페이지"

def main():
    """메인 애플리케이션 함수"""
    # 현재 페이지에 따라 다른 함수 호출
    if st.session_state.current_page == "메인 페이지":
        show_main_menu()
    elif st.session_state.current_page == "재료 등록하기":
        ingredient_registration_page()
    elif st.session_state.current_page == "재료 리스트 보기":
        ingredient_list_page()
    elif st.session_state.current_page == "재료 사용하기":
        ingredient_usage_page()
    elif st.session_state.current_page == "레시피 추천 받기":
        recipe_recommendation_page()

if __name__ == "__main__":
    main()