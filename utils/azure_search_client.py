"""
Azure AI Search 클라이언트 모듈
레시피 검색을 위한 Azure Cognitive Search 연결 및 검색 기능
"""

import os
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from typing import List, Dict, Any
import streamlit as st

class AzureSearchClient:
    """Azure AI Search 클라이언트 클래스"""
    
    def __init__(self):
        """Azure Search 클라이언트 초기화"""
        # 환경변수에서 Azure Search 설정 가져오기
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = os.getenv("AZURE_SEARCH_KEY",)
        self.index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
        
        if not self.search_endpoint or not self.search_key:
            raise ValueError("Azure Search 설정이 없습니다. 환경변수 또는 Streamlit secrets를 확인해주세요.")
        
        # SearchClient 생성
        self.client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_name,
            credential=AzureKeyCredential(self.search_key)
        )
    
    def search_recipes_by_ingredients(self, ingredients: List[str], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        재료 목록을 기반으로 레시피 검색
        
        Args:
            ingredients: 재료명 리스트
            top_k: 반환할 레시피 개수 (기본값: 3)
            
        Returns:
            검색된 레시피 리스트
        """
        try:
            # 재료를 포함하는 검색 쿼리 생성 (유연한 검색)
            # 재료명들을 OR 조건으로 연결하여 점수가 낮아도 결과 반환
            search_query = " OR ".join([ingredient for ingredient in ingredients])
            
            # 검색 실행
            results = self.client.search(
                search_text=search_query,
                top=top_k,
                search_mode="any",  # 일부 조건만 만족해도 결과 반환 (점수 낮아도 결과 나옴)
                query_type="simple",  # 단순 쿼리로 변경
                select=["title","url","ingredients","steps"],
                highlight_fields="ingredients",  # searchable 필드만 하이라이트
                order_by=["search.score() desc"]
            )
            
            recipes = []
            for result in results:
                recipe = {
                    "id": result.get("id", ""),
                    "title": result.get("title", "제목 없음"),
                    "ingredients": result.get("ingredients", []),
                    "steps": result.get("steps", []),
                    "url": result.get("url", ""),
                    "score": result.get("@search.score", 0.0),
                    "highlights": result.get("@search.highlights", {})
                }
                recipes.append(recipe)
            
            return recipes
            
        except Exception as e:
            st.error(f"Azure Search 검색 중 오류 발생: {str(e)}")
            return []
    
    def search_recipes_flexible(self, ingredients: List[str], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        재료를 부분적으로 포함하는 유연한 레시피 검색
        
        Args:
            ingredients: 재료명 리스트
            top_k: 반환할 레시피 개수 (기본값: 3)
            
        Returns:
            검색된 레시피 리스트
        """
        try:
            # 재료명들을 OR 조건으로 연결 (더 유연한 검색)
            search_query = " OR ".join([ingredient for ingredient in ingredients])
            
            # 검색 실행
            results = self.client.search(
                search_text=search_query,
                top=top_k,
                search_mode="any",  # 일부 조건만 만족해도 결과 반환
                query_type="simple",
                select=["title","url","ingredients","steps"],
                highlight_fields="ingredients",
                order_by=["search.score() desc"]
            )
            
            recipes = []
            for result in results:
                recipe = {
                    "id": result.get("id", ""),
                    "title": result.get("title", "제목 없음"),
                    "ingredients": result.get("ingredients", []),
                    "steps": result.get("steps", []),
                    "url": result.get("url", ""),
                    "score": result.get("@search.score", 0.0),
                    "highlights": result.get("@search.highlights", {})
                }
                recipes.append(recipe)
            
            return recipes
            
        except Exception as e:
            st.error(f"Azure Search 유연한 검색 중 오류 발생: {str(e)}")
            return []

# 전역 클라이언트 인스턴스
_search_client = None

def get_search_client() -> AzureSearchClient:
    """Azure Search 클라이언트 싱글톤 인스턴스 반환"""
    global _search_client
    if _search_client is None:
        _search_client = AzureSearchClient()
    return _search_client
