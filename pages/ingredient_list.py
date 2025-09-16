"""
재료 리스트 페이지 모듈
현재 등록된 재료 목록을 확인하고 관리하는 기능
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from utils.blob_storage_manager import BlobStorageManager

def get_status_and_color(expiration_date):
    """유통기한을 기준으로 상태와 색상을 반환"""
    try:
        # 문자열을 datetime 객체로 변환
        exp_date = datetime.strptime(expiration_date, '%Y-%m-%d').date()
        today = datetime.now().date()
        days_remaining = (exp_date - today).days
        
        if days_remaining < 0:
            return "폐기", "🔴"
        elif days_remaining < 4:
            return "위험", "🟡"
        else:
            return "양호", "🟢"
    except:
        return "알 수 없음", "⚪"

def ingredient_list_page():
    """재료 리스트 보기 페이지"""
    # 뒤로가기 버튼
    if st.button("🏠 메인으로 돌아가기", type="secondary"):
        st.session_state.current_page = "메인 페이지"
        st.rerun()
    
    st.title("📋 재료 리스트")
    st.markdown("현재 등록된 재료 목록을 확인하세요.")
    st.markdown("---")
    
    # # CSV 파일 경로
    # csv_path = "./pages/data/ingredients_data.csv"
    
    # if not os.path.exists(csv_path):
    #     st.info("📝 아직 등록된 재료가 없습니다. '재료 등록하기'에서 재료를 추가해보세요!")
    #     return
    
    try:
        
        blob_name = "data/ingredients_data.csv"
        blob_manager = BlobStorageManager()
        df = blob_manager.download_csv_to_dataframe(blob_name)
        
        
        if df.empty:
            st.info("📝 아직 등록된 재료가 없습니다. '재료 등록하기'에서 재료를 추가해보세요!")
            return
        
        # 데이터 처리
        display_data = []
        for _, row in df.iterrows():
            # 상태 계산
            status, color_icon = get_status_and_color(row['expiration_date'])
            
            # 날짜 형식 변환 (시간 제거)
            date_added = row['date_added'].split(' ')[0] if ' ' in str(row['date_added']) else str(row['date_added'])
            
            display_data.append({
                "재료명": row['name'],
                "수량": f"{row['quantity']} {row['unit']}",
                "등록일": date_added,
                "유통기한": row['expiration_date'],
                "상태": f"{color_icon} {status}"
            })
        
        # 데이터프레임으로 변환
        display_df = pd.DataFrame(display_data)
        
        # 통계 정보 표시
        total_count = len(display_df)
        good_count = len([d for d in display_data if "양호" in d["상태"]])
        warning_count = len([d for d in display_data if "위험" in d["상태"]])
        expired_count = len([d for d in display_data if "폐기" in d["상태"]])
        
        # 통계 컬럼
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("전체 재료", total_count)
        with col2:
            st.metric("양호", good_count, delta=None)
        with col3:
            st.metric("위험", warning_count, delta=None)
        with col4:
            st.metric("폐기", expired_count, delta=None)
        
        st.markdown("---")
        
        # 필터 옵션
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox(
                "상태별 필터",
                ["전체", "양호", "위험", "폐기"],
                key="status_filter"
            )
        
        with col2:
            sort_option = st.selectbox(
                "정렬 기준",
                ["유통기한 순", "등록일 순", "재료명 순"],
                key="sort_option"
            )
        
        # 필터링
        filtered_df = display_df.copy()
        if status_filter != "전체":
            filtered_df = filtered_df[filtered_df["상태"].str.contains(status_filter)]
        
        # 정렬
        if sort_option == "유통기한 순":
            # 유통기한으로 정렬 (날짜 형식으로 변환 후 정렬)
            filtered_df['유통기한_날짜'] = pd.to_datetime(filtered_df['유통기한'])
            filtered_df = filtered_df.sort_values('유통기한_날짜').drop('유통기한_날짜', axis=1)
        elif sort_option == "등록일 순":
            filtered_df['등록일_날짜'] = pd.to_datetime(filtered_df['등록일'])
            filtered_df = filtered_df.sort_values('등록일_날짜', ascending=False).drop('등록일_날짜', axis=1)
        elif sort_option == "재료명 순":
            filtered_df = filtered_df.sort_values('재료명')
        
        # 테이블 표시
        if filtered_df.empty:
            st.info(f"'{status_filter}' 상태의 재료가 없습니다.")
        else:
            st.subheader(f"재료 목록 ({len(filtered_df)}개)")
            
            # 데이터프레임 표시 (인덱스 숨김)
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True
            )
        
        # 새로고침 버튼
        if st.button("🔄 새로고침", type="secondary"):
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ 데이터를 불러오는 중 오류가 발생했습니다: {e}")
        st.info("CSV 파일이 손상되었을 수 있습니다. '재료 등록하기'에서 새로운 재료를 추가해보세요.")
