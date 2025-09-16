"""
레시피 추천 페이지 모듈
Azure AI Search를 사용하여 보유한 재료로 만들 수 있는 레시피를 검색
"""

import streamlit as st
import pandas as pd
import os
from utils.azure_search_client import get_search_client
from utils.blob_storage_manager import BlobStorageManager

def display_recipe_card(recipe, index):
    """레시피 카드를 보기좋게 표시하는 함수"""
    with st.container():
        # 전체 카드를 하나의 HTML 박스로 구성
        card_html = f"""
        <div style="
            border: 1px solid #e0e0e0; 
            border-radius: 10px; 
            padding: 20px; 
            margin: 10px 0; 
            background-color: #f9f9f9;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <h3 style="margin-top: 0; color: #2c3e50;">🍽️ {recipe['title']}</h3>
        """
        
        # URL이 있으면 링크 추가
        if recipe.get('url'):
            card_html += f'<p><a href="{recipe["url"]}" target="_blank">🔗 원본 레시피 보기</a></p>'
        
        # 재료와 조리방법 섹션
        card_html += """
            <div style="display: flex; gap: 20px; margin-top: 15px;">
                <div style="flex: 1;">
                    <h4 style="color: #34495e; margin-bottom: 10px;">📝 필요한 재료:</h4>
                    <div style="background-color: #ffffff; padding: 10px; border-radius: 5px; height: 200px; overflow-y: auto; border: 1px solid #ddd;">
        """
        
        # 재료 목록 추가
        if recipe.get('ingredients'):
            if isinstance(recipe['ingredients'], list):
                ingredients_text = ", ".join(recipe['ingredients'])
            else:
                ingredients_text = str(recipe['ingredients'])
            card_html += ingredients_text
        
        card_html += """
                    </div>
                </div>
                <div style="flex: 1;">
                    <h4 style="color: #34495e; margin-bottom: 10px;">📖 조리 방법:</h4>
                    <div style="background-color: #ffffff; padding: 10px; border-radius: 5px; height: 200px; overflow-y: auto; border: 1px solid #ddd;">
        """
        
        # 조리 방법 추가
        if recipe.get('steps'):
            if isinstance(recipe['steps'], list):
                for i, step in enumerate(recipe['steps'], 1):
                    step_formatted = step.replace("|", "<br>")
                    card_html += f"<p><strong>{i}.</strong> {step_formatted}</p>"
            else:
                steps_formatted = str(recipe['steps']).replace("|", "<br>")
                card_html += f"<p>{steps_formatted}</p>"
        
        card_html += """
                    </div>
                </div>
            </div>
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)

def recipe_recommendation_page():
    """Azure AI Search를 사용한 레시피 검색 페이지"""
    # 뒤로가기 버튼
    if st.button("🏠 메인으로 돌아가기", type="secondary"):
        st.session_state.current_page = "메인 페이지"
        st.rerun()
    
    st.title("🔍 레시피 추천")
    st.markdown("냉장고에 보관 중인 재료를 활용할 수 있는 레시피를 추천합니다.")
    st.markdown("---")
    
    try:

        blob_name = "data/ingredients_data.csv"
        blob_manager = BlobStorageManager()
        df = blob_manager.download_csv_to_dataframe(blob_name)
        
        if df.empty:
            st.info("📝 먼저 재료를 등록해주세요!")
            return
        
        # df에서 name만 추출
        ingredient_names = df['name'].tolist()
        
        # 현재 보유한 재료 표시 및 선택
        st.subheader("🍊 현재 보유한 재료")
        st.markdown("추천에 사용할 재료를 선택하세요:")
        
        # 체크박스로 재료 선택
        selected_ingredients = []
        
        
        # 각 재료별 체크박스
        for ingredient in ingredient_names:
            # 기본값은 True (모든 재료 선택)
            is_selected = st.checkbox(
                f"**{ingredient}**",
                value=st.session_state.get(f"ingredient_{ingredient}", True),
                key=f"ingredient_{ingredient}"
            )
            if is_selected:
                selected_ingredients.append(ingredient)
        
        # 선택된 재료 요약 표시
        if selected_ingredients:
            st.markdown(f"**선택된 재료 ({len(selected_ingredients)}개):** {', '.join(selected_ingredients)}")
        else:
            st.warning("⚠️ 검색할 재료를 선택해주세요!")
        
        st.markdown("---")
        
        # 레시피 검색 버튼
        if st.button("🔍 레시피 검색하기", type="primary", use_container_width=True):
            if len(selected_ingredients) == 0:
                st.error("❌ 검색할 재료를 선택해주세요!")
                return
            
            with st.spinner("🔍 Azure AI Search에서 레시피를 검색하는 중입니다..."):
                try:
                    # Azure Search 클라이언트 가져오기
                    search_client = get_search_client()
                    
                    # 엄격한 검색 (선택된 재료 포함) 사용 - 기본 3개 검색
                    recipes = search_client.search_recipes_by_ingredients(selected_ingredients, 3)
                    
                    if recipes:
                        st.markdown("---")
                        st.subheader(f"🍳 추천 결과")
                        
                        # 각 레시피를 카드 형태로 표시
                        for i, recipe in enumerate(recipes):
                            display_recipe_card(recipe, i)
                            
                        # 검색 결과가 적을 때 안내 메시지
                        if len(recipes) < 3:
                            st.info(f"💡 3개의 레시피를 요청했지만 {len(recipes)}개만 찾았습니다. 선택한 모든 재료가 포함된 레시피만 검색됩니다.")
                    
                    else:
                        st.warning("😅 검색 결과가 없습니다.")
                        st.markdown("""
                        **다음을 확인해보세요:**
                        - Azure AI Search 설정이 올바른지 확인
                        - 검색 인덱스에 데이터가 있는지 확인
                        - 선택한 모든 재료가 포함된 레시피가 인덱스에 있는지 확인
                        - 더 적은 재료를 선택해보세요
                        """)
                        
                except Exception as e:
                    st.error(f"❌ 레시피 검색 중 오류가 발생했습니다: {str(e)}")
                    st.markdown("""
                    **오류 해결 방법:**
                    - Azure Search 연결 설정을 확인해주세요
                    - 환경변수나 Streamlit secrets에서 다음 값들이 설정되어 있는지 확인:
                      - `AZURE_SEARCH_ENDPOINT`
                      - `AZURE_SEARCH_KEY`
                      - `AZURE_SEARCH_INDEX_NAME`
                    """)
        
        # 새로고침 버튼
        st.markdown("---")
        if st.button("🔄 재료 목록 새로고침", type="secondary"):
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ 데이터를 불러오는 중 오류가 발생했습니다: {e}")
        st.info("CSV 파일이 손상되었을 수 있습니다. '재료 등록하기'에서 새로운 재료를 추가해보세요.")