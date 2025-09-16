"""
재료 사용 페이지 모듈
사용한 재료를 선택하여 수량을 차감하고 CSV에 저장하는 기능
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime

def save_updated_ingredients(df, csv_path):
    """수정된 재료 데이터를 CSV 파일에 저장"""
    try:
        # 수량이 0 이하인 재료는 제거
        df = df[df['quantity'] > 0]
        
        # CSV 파일로 저장
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        return True, len(df)
    except Exception as e:
        st.error(f"CSV 저장 중 오류 발생: {e}")
        return False, 0

def ingredient_usage_page():
    """재료 사용하기 페이지"""
    # 뒤로가기 버튼
    if st.button("🏠 메인으로 돌아가기", type="secondary"):
        st.session_state.current_page = "메인 페이지"
        st.rerun()
    
    st.title("🍳 재료 사용하기")
    st.markdown("사용한 재료의 수량을 입력하여 재고에서 차감하세요.")
    st.markdown("---")
    
    # CSV 파일 경로
    csv_path = "./pages/data/ingredients_data.csv"
    
    if not os.path.exists(csv_path):
        st.info("📝 사용할 재료가 없습니다. 먼저 재료를 등록해주세요!")
        return
    
    try:
        # CSV 파일 읽기
        df = pd.read_csv(csv_path)
        
        if df.empty:
            st.info("📝 사용할 재료가 없습니다. 먼저 재료를 등록해주세요!")
            return
        
        # 세션 상태 초기화
        if 'usage_data' not in st.session_state:
            st.session_state.usage_data = {}
        
        st.subheader("📦 현재 재료 목록")
        
        # 재료 목록과 사용량 입력
        usage_inputs = {}
        
        for idx, row in df.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                with col1:
                    st.write(f"**{row['name']}**")
                
                with col2:
                    st.write(f"보유: {row['quantity']} {row['unit']}")
                
                with col3:
                    st.write(f"유통기한: {row['expiration_date']}")
                
                with col4:
                    # 사용량 입력
                    max_quantity = float(row['quantity'])
                    used_quantity = st.number_input(
                        f"사용량",
                        min_value=0.0,
                        max_value=max_quantity,
                        value=0.0,
                        step=0.1 if max_quantity < 1 else 1.0,
                        key=f"usage_{idx}",
                        help=f"최대 {max_quantity} {row['unit']} 까지 입력 가능"
                    )
                    
                    if used_quantity > 0:
                        usage_inputs[idx] = {
                            'name': row['name'],
                            'used_quantity': used_quantity,
                            'unit': row['unit'],
                            'remaining': max_quantity - used_quantity
                        }
                
                st.divider()
        
        # 사용 요약 표시
        if usage_inputs:
            st.markdown("---")
            st.subheader("📝 사용 요약")
            
            summary_data = []
            total_used_items = 0
            
            for idx, usage_info in usage_inputs.items():
                summary_data.append({
                    "재료명": usage_info['name'],
                    "사용량": f"{usage_info['used_quantity']} {usage_info['unit']}",
                    "잔여량": f"{usage_info['remaining']} {usage_info['unit']}"
                })
                total_used_items += 1
            
            # 요약 테이블 표시
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            # 확인 및 저장 버튼
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ 사용 확정", type="primary", use_container_width=True):
                    with st.spinner("재료 사용량을 업데이트하는 중..."):
                        # 데이터프레임 업데이트
                        updated_df = df.copy()
                        removed_items = []
                        
                        for idx, usage_info in usage_inputs.items():
                            original_quantity = float(updated_df.loc[idx, 'quantity'])
                            new_quantity = original_quantity - usage_info['used_quantity']
                            
                            if new_quantity <= 0:
                                # 수량이 0 이하가 되면 제거 대상으로 표시
                                removed_items.append(usage_info['name'])
                                updated_df.loc[idx, 'quantity'] = 0
                            else:
                                updated_df.loc[idx, 'quantity'] = new_quantity
                        
                        # CSV 파일 저장
                        success, remaining_count = save_updated_ingredients(updated_df, csv_path)
                        
                        if success:
                            st.success(f"✅ {total_used_items}개 재료 사용이 완료되었습니다!")
                            
                            if removed_items:
                                st.warning(f"📦 다음 재료들이 모두 소진되어 목록에서 제거되었습니다: {', '.join(removed_items)}")
                            
                            st.info(f"📋 현재 {remaining_count}개의 재료가 남아있습니다.")
                            
                            # 세션 상태 초기화
                            st.session_state.usage_data = {}
                            
                            # 페이지 새로고침
                            st.rerun()
                        else:
                            st.error("❌ 재료 사용 처리 중 오류가 발생했습니다.")
            
            with col2:
                if st.button("🔄 초기화", type="secondary", use_container_width=True):
                    st.session_state.usage_data = {}
                    st.rerun()
        
        else:
            st.info("👆 사용할 재료의 수량을 입력해주세요.")
        
        # 새로고침 버튼
        st.markdown("---")
        if st.button("🔄 재료 목록 새로고침", type="secondary"):
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ 데이터를 불러오는 중 오류가 발생했습니다: {e}")
        st.info("CSV 파일이 손상되었을 수 있습니다. '재료 등록하기'에서 새로운 재료를 추가해보세요.")
