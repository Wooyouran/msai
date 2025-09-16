"""
Streamlit ChatGPT-5 멀티모달 분석기
냉장고 재료 관리 및 레시피 추천 시스템
"""

import streamlit as st
import os
import base64
import tempfile
import json
from datetime import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="냉장고 재료 관리 시스템",
    page_icon="🥬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Azure OpenAI 설정 (환경변수에서 로드)
ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# 세션 상태 초기화
if 'ingredients' not in st.session_state:
    st.session_state.ingredients = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = "재료 등록하기"

def analyze_image_with_chatgpt5(image_path: str, prompt: str, endpoint: str, api_key: str, deployment_name: str) -> str:
    """
    ChatGPT-5로 이미지와 텍스트를 함께 분석합니다.
    
    Args:
        image_path: 이미지 파일 경로
        prompt: 분석 요청 텍스트
        endpoint: Azure OpenAI 엔드포인트
        api_key: Azure OpenAI API 키
        deployment_name: 배포된 ChatGPT-5 모델 이름
    
    Returns:
        str: 분석 결과
    """
    try:
        # Azure OpenAI 클라이언트 초기화
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-12-01-preview"
        )
        
        # 이미지 파일 크기 확인 (20MB 제한)
        file_size = os.path.getsize(image_path)
        if file_size > 20 * 1024 * 1024:  # 20MB
            return "❌ 이미지 파일이 너무 큽니다. 20MB 이하의 파일을 사용해주세요."
        
        # 이미지를 base64로 인코딩
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # 파일 확장자에 따라 MIME 타입 결정
        file_extension = image_path.lower().split('.')[-1]
        mime_type_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'bmp': 'image/bmp',
            'webp': 'image/webp'
        }
        mime_type = mime_type_map.get(file_extension, 'image/jpeg')
        
        # 이미지 URL 형식으로 변환
        image_url = f"data:{mime_type};base64,{base64_image}"
        
        # 메시지 구성
        messages = [
            {
                "role": "system",
                "content": "You are the manager who manages the food supplies in your refrigerator.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                            "detail": "auto"
                        }
                    }
                ]
            }
        ]
        
        # ChatGPT-5 API 호출 (timeout 설정)
        try:
            response = client.chat.completions.create(
                model=deployment_name,
                messages=messages,
                max_completion_tokens=2000,
                timeout=60.0  # 60초 timeout
            )
        except Exception as api_error:
            return f"❌ API 호출 오류: {str(api_error)}\n\n💡 가능한 원인:\n1. 네트워크 연결 문제\n2. API 서비스 일시적 장애\n3. 요청 시간 초과\n\n잠시 후 다시 시도해주세요."
        
        # 디버깅 정보 출력
        print(f"🔍 API 응답 디버깅:")
        print(f"  - 응답 타입: {type(response)}")
        print(f"  - choices 개수: {len(response.choices) if response.choices else 0}")
        
        if response.choices:
            choice = response.choices[0]
            print(f"  - choice 타입: {type(choice)}")
            print(f"  - message 타입: {type(choice.message)}")
            print(f"  - content 타입: {type(choice.message.content)}")
            print(f"  - content 길이: {len(choice.message.content) if choice.message.content else 0}")
        
        # 응답 확인
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            if content and content.strip():
                return content
            else:
                return f"❌ API 응답이 비어있습니다.\n\n🔍 디버깅 정보:\n- 응답 타입: {type(response)}\n- choices 개수: {len(response.choices)}\n- content: '{content}'\n\n💡 가능한 원인:\n1. 이미지가 너무 복잡하거나 인식하기 어려운 경우\n2. 프롬프트가 모호한 경우\n3. API 모델의 제한사항\n\n다른 프롬프트를 시도해보세요."
        else:
            return f"❌ API 응답에 선택지가 없습니다.\n\n🔍 디버깅 정보:\n- 응답 타입: {type(response)}\n- choices: {response.choices}"
        
    except Exception as e:
        # 더 자세한 에러 정보 제공
        error_msg = f"오류 발생: {str(e)}"
        if "image" in str(e).lower():
            error_msg += "\n💡 이미지 형식이나 크기를 확인해주세요."
        elif "api" in str(e).lower():
            error_msg += "\n💡 API 설정을 확인해주세요."
        return error_msg

def show_menu():
    """메뉴 표시"""
    st.sidebar.title("🥬 냉장고 관리")
    st.sidebar.markdown("---")
    
    menu_options = [
        "재료 등록하기",
        "재료 리스트 보기", 
        "재료 사용하기",
        "레시피 추천 받기"
    ]
    
    for option in menu_options:
        if st.sidebar.button(option, use_container_width=True):
            st.session_state.current_page = option
            st.rerun()

def ingredient_registration_page():
    """재료 등록하기 페이지 (기존 이미지 분석 기능)"""
    st.title("📸 재료 등록하기")
    st.markdown("냉장고 사진을 업로드하여 재료를 자동으로 등록하세요.")
    st.markdown("---")
    
    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ API 설정")
        
        # API 설정 (사용자가 변경 가능)
        endpoint = st.text_input("엔드포인트", value=ENDPOINT, type="password")
        api_key = st.text_input("API 키", value=API_KEY, type="password")
        deployment_name = st.text_input("배포 이름", value=DEPLOYMENT_NAME)
        st.markdown("---")
        
        # 사용 예시
        st.subheader("💡 사용 예시")
        st.markdown("""
        - **재료 목록**: "밀가루 500g, 파프리카 2개, 오이 2개 형식으로 재료 목록 만들어줘"
        - **개수 세기**: "이 이미지에서 당근 개수 세줘"
        - **음식 확인**: "우유가 있나요?"
        - **설명**: "이 이미지를 자세히 설명해줘"
        """)
    
    # 메인 컨텐츠
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📸 이미지 업로드")
        
        # 이미지 업로드
        uploaded_file = st.file_uploader(
            "냉장고 사진을 업로드하세요",
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
            # 프롬프트 입력
            prompt = st.text_area(
                "분석하고 싶은 내용을 입력하세요:",
                placeholder="예: 밀가루 500g, 파프리카 2개, 오이 2개 형식으로 재료 목록 만들어줘",
                height=100
            )
            
            # 분석 버튼
            if st.button("🔍 분석 시작", type="primary", use_container_width=True):
                if prompt.strip():
                    with st.spinner("분석 중입니다..."):
                        # 임시 파일로 저장
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_file_path = tmp_file.name
                        
                        try:
                            # 파일 정보 표시
                            file_size = os.path.getsize(tmp_file_path)
                            st.info(f"🔍 분석 중... (파일 크기: {file_size / 1024:.1f} KB)")
                            
                            # ChatGPT-5로 분석
                            result = analyze_image_with_chatgpt5(
                                image_path=tmp_file_path,
                                prompt=prompt,
                                endpoint=endpoint,
                                api_key=api_key,
                                deployment_name=deployment_name
                            )
                            
                            # 결과 표시
                            st.subheader("📋 분석 결과")
                            
                            # 결과가 비어있는지 확인
                            if result and result.strip():
                                st.success("✅ 분석 완료!")
                                st.markdown("---")
                                st.markdown(result)
                                
                                # 재료 등록 버튼
                                if st.button("📝 재료 목록에 추가", type="secondary"):
                                    # 간단한 재료 파싱 (실제로는 더 정교한 파싱이 필요)
                                    ingredients_text = result
                                    st.session_state.ingredients.append({
                                        'name': f"분석된 재료 ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
                                        'details': ingredients_text,
                                        'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    })
                                    st.success("✅ 재료가 목록에 추가되었습니다!")
                                    st.rerun()
                            else:
                                st.error("❌ 분석 결과가 비어있습니다.")
                                st.info("💡 다른 프롬프트를 시도해보거나 이미지를 다시 확인해주세요.")
                            
                        except Exception as e:
                            st.error(f"❌ 오류 발생: {e}")
                        
                        finally:
                            # 임시 파일 삭제
                            if os.path.exists(tmp_file_path):
                                os.unlink(tmp_file_path)
                else:
                    st.warning("⚠️ 분석할 내용을 입력해주세요!")
        else:
            st.info("👆 먼저 이미지를 업로드해주세요!")

def ingredient_list_page():
    """재료 리스트 보기 페이지"""
    st.title("📋 재료 리스트")
    st.markdown("현재 등록된 재료 목록을 확인하세요.")
    st.markdown("---")
    
    if not st.session_state.ingredients:
        st.info("📝 아직 등록된 재료가 없습니다. '재료 등록하기'에서 재료를 추가해보세요!")
    else:
        for i, ingredient in enumerate(st.session_state.ingredients):
            with st.expander(f"📦 {ingredient['name']} (등록일: {ingredient['date_added']})"):
                st.markdown(ingredient['details'])
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"🗑️ 삭제", key=f"delete_{i}"):
                        st.session_state.ingredients.pop(i)
                        st.rerun()
                with col2:
                    if st.button(f"✏️ 수정", key=f"edit_{i}"):
                        st.session_state[f"editing_{i}"] = True
                        st.rerun()

def ingredient_usage_page():
    """재료 사용하기 페이지"""
    st.title("🍳 재료 사용하기")
    st.markdown("사용한 재료를 선택하여 목록에서 제거하세요.")
    st.markdown("---")
    
    if not st.session_state.ingredients:
        st.info("📝 사용할 재료가 없습니다. 먼저 재료를 등록해주세요!")
    else:
        st.subheader("사용한 재료 선택")
        
        selected_ingredients = []
        for i, ingredient in enumerate(st.session_state.ingredients):
            if st.checkbox(f"📦 {ingredient['name']}", key=f"use_{i}"):
                selected_ingredients.append(i)
        
        if selected_ingredients:
            if st.button("✅ 선택한 재료 사용 완료", type="primary"):
                # 역순으로 삭제 (인덱스 변경 방지)
                for i in sorted(selected_ingredients, reverse=True):
                    st.session_state.ingredients.pop(i)
                st.success(f"✅ {len(selected_ingredients)}개의 재료를 사용 완료 처리했습니다!")
                st.rerun()

def recipe_recommendation_page():
    """레시피 추천 받기 페이지"""
    st.title("🍽️ 레시피 추천")
    st.markdown("현재 보유한 재료로 만들 수 있는 레시피를 추천받으세요.")
    st.markdown("---")
    
    if not st.session_state.ingredients:
        st.info("📝 먼저 재료를 등록해주세요!")
    else:
        st.subheader("현재 보유 재료")
        ingredients_text = ""
        for ingredient in st.session_state.ingredients:
            ingredients_text += f"- {ingredient['name']}\n"
        
        st.text_area("보유 재료 목록:", value=ingredients_text, height=150, disabled=True)
        
        if st.button("🍳 레시피 추천 받기", type="primary"):
            st.info("💡 레시피 추천 기능은 추후 구현 예정입니다!")
            st.markdown("""
            **구현 예정 기능:**
            - 보유 재료 기반 레시피 추천
            - ChatGPT-5를 활용한 맞춤형 레시피 생성ㄴ
            - 영양 정보 및 조리 시간 제공
            """)

def main():
    """
    메인 Streamlit 애플리케이션
    """
    # 메뉴 표시
    show_menu()
    
    # 현재 페이지에 따라 다른 컨텐츠 표시
    if st.session_state.current_page == "재료 등록하기":
        ingredient_registration_page()
    elif st.session_state.current_page == "재료 리스트 보기":
        ingredient_list_page()
    elif st.session_state.current_page == "재료 사용하기":
        ingredient_usage_page()
    elif st.session_state.current_page == "레시피 추천 받기":
        recipe_recommendation_page()
    
    # 하단 정보
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>🥬 냉장고 재료 관리 시스템 | ChatGPT-5 멀티모달 분석기</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
