"""
Azure Blob Storage를 사용하여 CSV 파일을 읽고 쓰는 유틸리티 모듈
"""

import pandas as pd
import io
from azure.storage.blob import BlobServiceClient, BlobClient
from typing import Optional
import os
from datetime import datetime
from dotenv import load_dotenv


class BlobStorageManager:
    def __init__(self, connection_string: Optional[str] = None, container_name: Optional[str] = None):
        """
        Azure Blob Storage 매니저 초기화
        
        Args:
            connection_string: Azure Storage Account 연결 문자열 (None이면 환경변수에서 가져옴)
            container_name: 사용할 컨테이너 이름 (None이면 환경변수에서 가져옴, 기본값: "ingredients")
        """
        
        load_dotenv()
        
        # 연결 문자열 설정
        if connection_string is None:
            connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
            if not connection_string:
                raise ValueError("AZURE_STORAGE_CONNECTION_STRING 환경변수가 설정되지 않았습니다.")
        
        # 컨테이너 이름 설정
        if container_name is None:
            container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
        
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_name = container_name
        
    
    def upload_csv_from_dataframe(self, df: pd.DataFrame, blob_name: str) -> bool:
        """
        DataFrame을 CSV 형태로 Blob Storage에 업로드
        
        Args:
            df: 업로드할 DataFrame
            blob_name: Blob 이름 (예: "ingredients_data.csv")
            
        Returns:
            bool: 업로드 성공 여부
        """
        try:
            # DataFrame을 CSV 문자열로 변환
            csv_string = df.to_csv(index=False, encoding='utf-8-sig')
            
            # Blob 클라이언트 생성
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, 
                blob=blob_name
            )
            
            # CSV 데이터 업로드d
            blob_client.upload_blob(csv_string, overwrite=True)
            print(f"'{blob_name}' 파일이 성공적으로 업로드되었습니다.")
            return True
            
        except Exception as e:
            print(f"업로드 중 오류 발생: {str(e)}")
            return False
    
    
    def download_csv_to_dataframe(self, blob_name: str) -> Optional[pd.DataFrame]:
        """
        Blob Storage에서 CSV 파일을 다운로드하여 DataFrame으로 반환
        
        Args:
            blob_name: 다운로드할 Blob 이름
            
        Returns:
            pd.DataFrame: CSV 데이터가 포함된 DataFrame (실패시 None)
        """
        try:
            # Blob 클라이언트 생성
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, 
                blob=blob_name
            )
            
            # Blob 데이터 다운로드
            blob_data = blob_client.download_blob()
            csv_string = blob_data.readall().decode('utf-8')
            
            # CSV 문자열을 DataFrame으로 변환
            df = pd.read_csv(io.StringIO(csv_string))
            print(f"'{blob_name}' 파일을 성공적으로 다운로드했습니다.")
            return df
            
        except Exception as e:
            print(f"다운로드 중 오류 발생: {str(e)}")
            return None