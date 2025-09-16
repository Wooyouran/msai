"""
레시피 추천 페이지 모듈
현재 보유한 재료로 만들 수 있는 레시피를 추천받는 기능
"""

import streamlit as st
import pandas as pd
import os
from utils.chatgpt_analyzer import get_recipe_recommendations

def recipe_recommendation_page():
    """레시피 추천 받기 페이지"""
    # 뒤로가기 버튼
    if st.button("🏠 메인으로 돌아가기", type="secondary"):
        st.session_state.current_page = "메인 페이지"
        st.rerun()
    
    st.title("🍽️ 레시피 추천")
    st.markdown("현재 보유한 재료로 만들 수 있는 레시피를 추천받으세요.")
    st.markdown("---")
    
    # CSV 파일 경로
    csv_path = "./pages/data/ingredients_data.csv"
    
    if not os.path.exists(csv_path):
        st.info("📝 먼저 재료를 등록해주세요!")
        return
    
    try:
        # CSV 파일 읽기
        df = pd.read_csv(csv_path)
        
        if df.empty:
            st.info("📝 먼저 재료를 등록해주세요!")
            return
        
        ingredients_for_api = []
        for _, row in df.iterrows():
            ingredients_for_api.append({
                "name": row['name'],
                "quantity": row['quantity'],
                "unit": row['unit']
            })

        # 레시피 추천 옵션
        col1, col2 = st.columns(2)
        
        with col1:
            recipe_type = st.selectbox(
                "선호하는 요리 종류",
                ["한식", "중식", "일식", "양식", "아무거나"],
                key="recipe_type"
            )
        
        with col2:
            difficulty = st.selectbox(
                "요리 난이도",
                ["쉬움", "보통", "어려움", "상관없음"],
                key="difficulty"
            )
        
        # 추가 요청사항
        additional_request = st.text_area(
            "추가 요청사항 (선택사항)",
            placeholder="예: 매운 음식, 간단한 요리, 특정 재료 제외 등",
            height=80
        )
        
        # 레시피 추천 버튼
        if st.button("🍳 레시피 추천 받기", type="primary", use_container_width=True):
            if len(ingredients_for_api) == 0:
                st.error("❌ 추천받을 재료가 없습니다.")
                return
            
            with st.spinner("🤖 AI가 맞춤 레시피를 생성하는 중입니다..."):
                # 사용자 선택사항을 프롬프트에 추가
                enhanced_ingredients = ingredients_for_api.copy()
                
                # 추가 요청사항이 있으면 API 호출 전에 처리
                if recipe_type != "아무거나" or difficulty != "상관없음" or additional_request.strip():
                    preference_text = f"\n\n추가 요청사항:\n"
                    if recipe_type != "아무거나":
                        preference_text += f"- 요리 종류: {recipe_type}\n"
                    if difficulty != "상관없음":
                        preference_text += f"- 난이도: {difficulty}\n"
                    if additional_request.strip():
                        preference_text += f"- 기타: {additional_request}\n"
                    
                    # 임시로 첫 번째 재료에 preference 정보 추가 (API 함수 수정 필요)
                    enhanced_ingredients.append({
                        "name": "preference_info",
                        "quantity": preference_text,
                        "unit": ""
                    })
                
                try:
                    # API 호출
                    recipe_result = get_recipe_recommendations(enhanced_ingredients)
                    
                    if recipe_result and not recipe_result.startswith("❌"):
                        st.markdown("---")
                        st.subheader("🍳 추천 레시피")
                        
                        # 결과를 마크다운으로 표시
                        st.markdown(recipe_result)
                        
                        # 저장 옵션
                        st.markdown("---")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("💾 레시피 저장", type="secondary"):
                                # 세션 상태에 레시피 저장
                                if 'saved_recipes' not in st.session_state:
                                    st.session_state.saved_recipes = []
                                
                                recipe_data = {
                                    "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                                    "ingredients_used": [ing["name"] for ing in ingredients_for_api if ing["name"] != "preference_info"],
                                    "recipe_content": recipe_result
                                }
                                
                                st.session_state.saved_recipes.append(recipe_data)
                                st.success("✅ 레시피가 저장되었습니다!")
                        
                        with col2:
                            if st.button("🔄 다른 레시피 추천", type="secondary"):
                                st.rerun()
                    
                    else:
                        st.error(f"레시피 추천 중 오류가 발생했습니다:\n{recipe_result}")
                        
                except Exception as e:
                    st.error(f"❌ 레시피 추천 중 오류가 발생했습니다: {str(e)}")
        
        # 저장된 레시피 표시
        if hasattr(st.session_state, 'saved_recipes') and st.session_state.saved_recipes:
            st.markdown("---")
            st.subheader("📚 저장된 레시피")
            
            for i, saved_recipe in enumerate(reversed(st.session_state.saved_recipes)):
                with st.expander(f"📝 레시피 #{len(st.session_state.saved_recipes)-i} ({saved_recipe['timestamp']})"):
                    st.markdown(f"**사용된 재료:** {', '.join(saved_recipe['ingredients_used'])}")
                    st.markdown("---")
                    st.markdown(saved_recipe['recipe_content'])
                    
                    if st.button(f"🗑️ 삭제", key=f"delete_recipe_{i}"):
                        st.session_state.saved_recipes.remove(saved_recipe)
                        st.rerun()
        
        # 새로고침 버튼
        st.markdown("---")
        if st.button("🔄 재료 목록 새로고침", type="secondary"):
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ 데이터를 불러오는 중 오류가 발생했습니다: {e}")
        st.info("CSV 파일이 손상되었을 수 있습니다. '재료 등록하기'에서 새로운 재료를 추가해보세요.")
