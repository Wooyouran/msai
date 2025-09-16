"""
ChatGPT-5 이미지 분석 유틸리티 모듈
냉장고 이미지를 분석하여 재료를 인식하는 기능
"""

import os
import base64
from openai import AzureOpenAI
from dotenv import load_dotenv

def analyze_image_with_chatgpt5(image_path: str, system_prompt: str, user_prompt: str) -> str:
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
    
    load_dotenv()

    ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    try:
        # Azure OpenAI 클라이언트 초기화
        client = AzureOpenAI(
            azure_endpoint=ENDPOINT,
            api_key=API_KEY,
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
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_prompt
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
                model=DEPLOYMENT_NAME,
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

def get_recipe_recommendations(ingredients_list: list) -> str:
    """
    보유 재료를 기반으로 레시피를 추천받습니다.
    
    Args:
        ingredients_list: 보유 재료 목록
    
    Returns:
        str: 레시피 추천 결과
    """
    
    load_dotenv()

    ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    try:
        # Azure OpenAI 클라이언트 초기화
        client = AzureOpenAI(
            azure_endpoint=ENDPOINT,
            api_key=API_KEY,
            api_version="2024-12-01-preview"
        )
        
        # 재료 목록과 선호사항 분리
        actual_ingredients = []
        preference_info = ""
        
        for item in ingredients_list:
            if item['name'] == 'preference_info':
                preference_info = item['quantity']
            else:
                actual_ingredients.append(f"{item['name']} {item['quantity']}{item['unit']}")
        
        ingredients_str = ", ".join(actual_ingredients)
        
        system_prompt = """
        당신은 전문 요리사입니다. 주어진 재료를 활용하여 실용적이고 맛있는 레시피를 추천해주세요.
        """
        
        user_prompt = f"""
        보유 재료: {ingredients_str}
        {preference_info}

        위 재료로 만들 수 있는 레시피 2개를 간단히 추천해주세요.

        ## 레시피 1: [요리명]
        **추가 재료:** [필요시 추가 재료]
        **조리법:**
        1. [핵심 단계만 간단히]
        **시간:** [조리시간]

        ---

        ## 레시피 2: [요리명]
        **추가 재료:** [필요시 추가 재료]
        **조리법:**
        1. [핵심 단계만 간단히]
        **시간:** [조리시간]

        - 보유 재료를 최대한 활용하세요
        - 간단하고 실용적인 레시피로 추천하세요
        """
        
        # 메시지 구성
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
        
        # ChatGPT API 호출 (재시도 로직 포함)
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=DEPLOYMENT_NAME,
                    messages=messages,
                    max_completion_tokens=2000,  # 토큰 수 줄임
                    timeout=30.0  # 타임아웃 줄임
                )
                break  # 성공하면 루프 종료
            except Exception as api_error: 
                if attempt < max_retries - 1:  # 마지막 시도가 아니면
                    continue  # 다시 시도
                else:
                    return f"❌ API 호출 오류: {str(api_error)}\n\n💡 가능한 해결방법:\n1. 잠시 후 다시 시도\n2. 재료 개수를 줄여서 시도\n3. 추가 요청사항을 간단히 작성"
        
        # 응답 확인
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            if content and content.strip():
                return content
            else:
                return "❌ API 응답이 비어있습니다. 다시 시도해주세요."
        else:
            return "❌ API 응답에 문제가 있습니다."
        
    except Exception as e:
        return f"❌ 오류 발생: {str(e)}"
