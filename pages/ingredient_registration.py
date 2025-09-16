"""
재료 등록 페이지 모듈
냉장고 사진을 업로드하여 재료를 자동으로 등록하는 기능
"""

import streamlit as st
import os
import tempfile
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import List
from utils.chatgpt_analyzer import analyze_image_with_chatgpt5
from utils.blob_storage_manager import BlobStorageManager


def save_data_to_blob(ingredients_data:List[dict]):
    """재료 데이터를 Blob Storage에 저장"""
    try:
        blob_name = "data/ingredients_data.csv"
        blob_manager = BlobStorageManager()
        existing_df = blob_manager.download_csv_to_dataframe(blob_name)
        
        if existing_df.empty or len(existing_df.columns) == 0:
            combined_df = pd.DataFrame(ingredients_data)
        else:
            new_df = pd.DataFrame(ingredients_data)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        blob_manager.upload_csv_from_dataframe(combined_df, blob_name)
        
        return True
        
    except Exception as e:
        st.error(f"Blob Storage 저장 중 오류 발생: {e}")
        return False


def save_ingredients_to_csv(ingredients_data, filename="ingredients_data.csv"):
    """재료 데이터를 CSV 파일에 저장"""
    try:
        # 새 데이터가 비어있으면 오류
        if not ingredients_data:
            st.error("저장할 데이터가 없습니다.")
            return False
        
        # 기존 CSV 파일이 있는지 확인
        if os.path.exists(filename):
            try:
                # 기존 데이터 읽기 시도
                existing_df = pd.read_csv(filename)
                # 파일이 비어있거나 컬럼이 없는 경우 처리
                if existing_df.empty or len(existing_df.columns) == 0:
                    # 새 데이터로 파일 생성
                    combined_df = pd.DataFrame(ingredients_data)
                else:
                    # 새 데이터 추가
                    new_df = pd.DataFrame(ingredients_data)
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            except (pd.errors.EmptyDataError, pd.errors.ParserError):
                # 파일이 비어있거나 파싱할 수 없는 경우 새로 생성
                # st.warning("기존 CSV 파일에 문제가 있어 새로 생성합니다.")
                combined_df = pd.DataFrame(ingredients_data)
        else:
            # 새 파일 생성
            combined_df = pd.DataFrame(ingredients_data)
        
        # CSV 파일로 저장
        combined_df.to_csv(filename, index=False, encoding='utf-8-sig')
        return True
    except Exception as e:
        st.error(f"CSV 저장 중 오류 발생: {e}")
        return False

def parse_json_result(result_text):
    """JSON 형식의 분석 결과를 파싱"""
    try:
        # JSON 부분만 추출 (```json ... ``` 형태일 수 있음)
        if "```json" in result_text:
            json_start = result_text.find("```json") + 7
            json_end = result_text.find("```", json_start)
            json_text = result_text[json_start:json_end].strip()
        elif "```" in result_text:
            json_start = result_text.find("```") + 3
            json_end = result_text.find("```", json_start)
            json_text = result_text[json_start:json_end].strip()
        else:
            # JSON 객체 찾기
            start_idx = result_text.find('{')
            end_idx = result_text.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_text = result_text[start_idx:end_idx]
            else:
                json_text = result_text
        
        # JSON 파싱
        data = json.loads(json_text)
        return data.get('ingredients', [])
    except json.JSONDecodeError as e:
        st.warning(f"JSON 파싱 오류: {e}")
        return None
    except Exception as e:
        st.warning(f"결과 파싱 오류: {e}")
        return None

def ingredient_registration_page():
    """재료 등록하기 페이지 (기존 이미지 분석 기능)"""
    # 세션 상태 초기화
    if 'ingredient_table_data' not in st.session_state:
        st.session_state.ingredient_table_data = []
    
    # 뒤로가기 버튼
    if st.button("🏠 메인으로 돌아가기", type="secondary"):
        st.session_state.current_page = "메인 페이지"
        st.rerun()
    
    st.title("🍅 식재료 등록하기")
    st.markdown("장바구니 사진을 업로드하여 재료를 자동으로 등록하세요.")
    st.markdown("---")
    
    # 메인 컨텐츠
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📸 이미지 업로드")
        
        # 이미지 업로드
        uploaded_file = st.file_uploader(
            "장바구니 사진을 업로드하세요",
            type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
            help="PNG, JPG, JPEG, GIF, BMP 형식의 이미지를 업로드할 수 있습니다."
        )
        
        if uploaded_file is not None:
            # 이미지 표시
            st.image(uploaded_file, caption="업로드된 이미지", use_container_width=True)
            
            # 이미지 정보
            st.success(f"✅ 이미지 업로드 완료!")
            
            # 파일 정보 표시
            file_size_mb = uploaded_file.size / (1024 * 1024)
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.info(f"📁 파일명: {uploaded_file.name}")
            with col_info2:
                st.info(f"📏 크기: {file_size_mb:.2f} MB")
            
            # 파일 형식 및 크기 경고
            if file_size_mb > 20:
                st.error("⚠️ 파일이 너무 큽니다. 20MB 이하의 파일을 권장합니다.")
            elif file_size_mb > 10:
                st.warning("⚠️ 파일이 큽니다. 분석에 시간이 걸릴 수 있습니다.")
            
            if file_extension not in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                st.warning(f"⚠️ {file_extension} 형식은 최적화되지 않을 수 있습니다.")
    
    with col2:
        st.subheader("💬 분석 요청")
        
        if uploaded_file is not None:
            
            system_prompt = """
            You are the manager of the refrigerator's food inventory.
            Given an image of a shopping cart, you must analyze the image to extract the ingredients.
                1. Extract the ingredients to be stored in the refrigerator.
                2. Extract the quantity of the extracted ingredients. Also extract the unit of measure for counting the quantity.
                3. Select a typical storage period for the ingredients.
            """
            
            user_prompt = """
            이미지를 분석하여, 냉장고에 보관할 식재료를 아래와 같은 JSON 형식으로 정리해주세요.
            - 예시: 
            {
            "ingredients": [
                {
                "name": "사과",
                "quantity": 3,
                "unit": "개",
                "expiry_days": 14,
                },
                {
                "name": "파프리카", 
                "quantity": 2,
                "unit": "개",
                "expiry_days": 10,
                }
            ]
            }
            
            재료를 정리할 때는 다음과 같은 조건을 충족하세요. 
            - 재료는 냉장고에 보관할 재료만 추출하세요.
            - name: 한글로 표시하고, 일반적인 표현을 사용하세요. 재료의 색상이나 브랜드 등 상세한 정보는 name에 포함하지 않습니다.
            - expiry_days: 일 단위로 표시하세요.
            - unit: 재료에 대한 일반적인 단위를 사용하세요.
            - quantity: 수량을 표시하세요. 수량은 정수 및 소수점 표시가 가능합니다. 예) 2.5, 3, 4.5, 5 등
            
            """
            
            # 분석 버튼
            if st.button("🔍 분석 시작", type="primary", use_container_width=True):
                with st.spinner("분석 중입니다..."):
                    # 임시 파일로 저장
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    try:
                        # 파일 정보 표시
                        # file_size = os.path.getsize(tmp_file_path)
                        # st.info(f"🔍 분석 중...")
                        
                        result = analyze_image_with_chatgpt5(
                            image_path=tmp_file_path,
                            system_prompt=system_prompt,
                            user_prompt=user_prompt
                        )
                        
                        
                        # 결과 표시 (테이블 형태)
                        st.markdown("---")
                        # st.subheader("📋 분석 결과")
                        
                        # 결과가 비어있는지 확인
                        if result and result.strip():
                            st.success("✅ 분석 완료!")
                            
                            # JSON 형식 결과 파싱 시도
                            parsed_ingredients = parse_json_result(result)
                            
                            if parsed_ingredients:
                                # JSON 형식으로 파싱된 경우
                                st.subheader("📋 분석 결과")
                                
                                # 테이블 데이터 생성
                                table_data = []
                                for ingredient in parsed_ingredients:
                                    table_data.append({
                                        "재료명": ingredient.get('name', ''),
                                        "수량": ingredient.get('quantity', ''),
                                        "단위": ingredient.get('unit', ''),
                                        "유통기한(일)": ingredient.get('expiry_days', ''),
                                    })
                                
                                # 세션 상태에 데이터 저장
                                st.session_state.ingredient_table_data = table_data
                                
                                # 테이블 표시
                                df = pd.DataFrame(table_data)
                                st.dataframe(df, use_container_width=True)
                                   
                                
                            else:
                                # JSON 파싱 실패 시 기존 방식으로 처리
                                st.warning("⚠️ JSON 형식으로 파싱할 수 없습니다. 원본 결과를 표시합니다.")
                                st.markdown("**분석 결과:**")
                                st.markdown(result)
                                
                                # # 재료 등록 버튼
                                # if st.button("📝 재료 목록에 추가", type="secondary"):
                                #     st.session_state.ingredients.append({
                                #         'name': f"분석된 재료 ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
                                #         'details': result,
                                #         'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                #     })
                                #     st.success("✅ 재료가 목록에 추가되었습니다!")
                                #     st.rerun()
                        
                        
                    except Exception as e:
                        st.error(f"❌ 오류 발생: {e}")
                    
                    finally:
                        # 임시 파일 삭제
                        if os.path.exists(tmp_file_path):
                            os.unlink(tmp_file_path)
        
             # 저장 버튼
            if st.session_state.ingredient_table_data and len(st.session_state.ingredient_table_data) > 0:
             
                if st.button("📝 재료 목록에 추가", type="primary", use_container_width=True):
                    with st.spinner("재료를 저장하는 중..."):
                        # 데이터 유효성 검사
                        if not st.session_state.ingredient_table_data:
                            st.error("❌ 저장할 재료 데이터가 없습니다.")
                        else:
                            #TODO: 기존 데이터와 확인 비교하여 넣기 (PK: name, expiration_date)
                            csv_data = []
                            for item in st.session_state.ingredient_table_data:

                                expiry_days = int(item['유통기한(일)'])
                                expiration_date = datetime.now() + timedelta(days=expiry_days)
                                
                                csv_data.append({
                                    'name': item['재료명'],
                                    'quantity': item['수량'],
                                    'unit': item['단위'],
                                    'expiry_days': expiry_days,
                                    'expiration_date': expiration_date.strftime('%Y-%m-%d'),
                                    'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
                            
                            # # data 디렉토리가 없으면 생성
                            # data_dir = "./pages/data"
                            # if not os.path.exists(data_dir):
                            #     os.makedirs(data_dir)
                            
                            # path = os.path.join(data_dir, "ingredients_data.csv")
                            
                            # # 저장 전 데이터 확인
                            # st.info(f"저장할 데이터: {len(csv_data)}개 재료")
                            
                            # if save_ingredients_to_csv(csv_data, path):
                            #     st.success(f"✅ 재료 목록에 성공적으로 추가되었습니다.")
                                
                            if save_data_to_blob(csv_data):
                                st.success(f"✅ 재료 목록에 성공적으로 추가되었습니다.")
                                
                                
                            else:
                                st.error("❌ CSV 저장에 실패했습니다.")
            else:
                st.info("📸 먼저 이미지를 분석하여 재료를 추출해주세요.")
        
        
        else:
            st.info("👆 먼저 이미지를 업로드해주세요!")
            
            
            
    