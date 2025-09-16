import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

BASE_URL = "https://www.10000recipe.com"

def get_recipe_links_from_page(base_url, page=1):
    """특정 페이지에서 레시피 링크 추출"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 페이지 번호가 1이면 기본 URL, 아니면 page 파라미터 추가
    if page == 1:
        page_url = base_url
    else:
        page_url = f"{base_url}&page={page}"
    
    try:
        res = requests.get(page_url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        print(f"페이지 {page} 로딩 성공: {page_url}")
        
        # 다양한 셀렉터로 레시피 링크 찾기
        links = []
        
        # 방법 1: 만개의레시피 특화 셀렉터들
        selectors_to_try = [
            "a[href*='/recipe/']",
            ".common_sp_link",
            ".thumbnail a",
            ".recipe_link",
            ".list_recipe a"
        ]
        
        for selector in selectors_to_try:
            for a in soup.select(selector):
                href = a.get("href")
                if href and "/recipe/" in href:
                    if href.startswith("/"):
                        full_url = BASE_URL + href
                    else:
                        full_url = href
                    if full_url not in links:
                        links.append(full_url)
        
        # 방법 2: 일반적인 레시피 링크 패턴 (백업)
        if not links:
            for a in soup.find_all("a", href=True):
                href = a.get("href")
                if href and "/recipe/" in href:
                    if href.startswith("/"):
                        full_url = BASE_URL + href
                    else:
                        full_url = href
                    if full_url not in links:
                        links.append(full_url)
        
        print(f"페이지 {page}에서 발견된 레시피 링크 수: {len(links)}")
        return links
        
    except requests.RequestException as e:
        print(f"페이지 {page} 요청 오류: {e}")
        return []
    except Exception as e:
        print(f"페이지 {page} 파싱 오류: {e}")
        return []


def get_all_recipe_links(base_url, max_recipes=100):
    """여러 페이지에서 최대 max_recipes개의 레시피 링크 수집"""
    all_links = []
    page = 1
    
    while len(all_links) < max_recipes:
        print(f"\n📄 페이지 {page} 처리 중...")
        page_links = get_recipe_links_from_page(base_url, page)
        
        if not page_links:
            print(f"페이지 {page}에서 더 이상 레시피를 찾을 수 없습니다. 크롤링 종료.")
            break
        
        # 중복 제거하면서 추가
        new_links = [link for link in page_links if link not in all_links]
        all_links.extend(new_links)
        
        print(f"페이지 {page}에서 {len(new_links)}개 새로운 링크 추가 (총 {len(all_links)}개)")
        
        # 목표 개수에 도달하면 종료
        if len(all_links) >= max_recipes:
            all_links = all_links[:max_recipes]
            break
            
        page += 1
        
        # 무한 루프 방지 (최대 50페이지까지만)
        if page > 50:
            print("최대 페이지 수에 도달했습니다.")
            break
            
        # 페이지 간 대기시간
        time.sleep(0.5)
    
    print(f"\n총 {len(all_links)}개의 레시피 링크 수집 완료")
    return all_links


def get_recipe_detail(recipe_url):
    """레시피 상세 페이지에서 제목, 재료, 조리순서 크롤링"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        res = requests.get(recipe_url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        # 제목 추출 (다양한 셀렉터 시도)
        title = None
        title_selectors = [
            ".view2_summary h3",
            "h1.recipe-title",
            ".recipe_title",
            "h1",
            ".title"
        ]
        
        for selector in title_selectors:
            title_tag = soup.select_one(selector)
            if title_tag:
                title = title_tag.get_text(strip=True)
                break
        
        if not title:
            # 페이지 타이틀에서 추출 시도
            page_title = soup.find("title")
            if page_title:
                title = page_title.get_text(strip=True).replace("만개의레시피", "").strip()
            else:
                raise ValueError("제목을 찾을 수 없음")

        # 재료 추출 (다양한 셀렉터 시도)
        ingredients = []
        ingredient_selectors = [
            ".ready_ingre3 li",
            ".recipe_ingredient li", 
            ".ingredient-list li",
            ".ingre_list li",
            ".ready_ingre li",
            ".view2_ingre li",
            ".ingre_box li"
        ]
        
        for selector in ingredient_selectors:
            ingredient_elements = soup.select(selector)
            if ingredient_elements:
                print(f"🔍 재료 셀렉터 '{selector}' 사용 - {len(ingredient_elements)}개 발견")
                for ing in ingredient_elements:
                    txt = ing.get_text(" ", strip=True)
                    if txt and len(txt) > 1 and txt not in ingredients:  # 최소 2글자 이상
                        ingredients.append(txt)
                break
        
        # 재료가 없으면 다른 방법 시도
        if not ingredients:
            print("🔍 대체 재료 추출 방법 시도...")
            for ing in soup.select("*"):
                if ing.name and "ingre" in ing.get("class", []):
                    txt = ing.get_text(" ", strip=True)
                    if txt and len(txt) > 1:
                        ingredients.append(txt)

        # 조리순서 추출 (다양한 셀렉터 시도)
        steps = []
        step_selectors = [
            ".view_step_cont",
            ".recipe_step",
            ".cooking-step", 
            ".step_cont",
            ".view_step .step_txt",
            ".manual_txt",
            ".step_list li"
        ]
        
        for selector in step_selectors:
            step_elements = soup.select(selector)
            if step_elements:
                print(f"🔍 조리순서 셀렉터 '{selector}' 사용 - {len(step_elements)}개 발견")
                for step in step_elements:
                    txt = step.get_text(" ", strip=True)
                    if txt and len(txt) > 5 and txt not in steps:  # 최소 5글자 이상
                        steps.append(txt)
                break
        
        # 조리순서가 없으면 다른 방법 시도
        if not steps:
            print("🔍 대체 조리순서 추출 방법 시도...")
            for step in soup.select("*"):
                if step.name and any(word in step.get("class", []) for word in ["step", "manual", "cook"]):
                    txt = step.get_text(" ", strip=True)
                    if txt and len(txt) > 5:
                        steps.append(txt)

        # 조리순서에 번호 추가
        numbered_steps = []
        if steps:
            for i, step in enumerate(steps, 1):
                numbered_steps.append(f"{i}. {step}")
        
        # 디버깅 정보 출력
        print(f"🔍 디버깅 - 제목: {title[:50] if title else 'None'}...")
        print(f"🔍 디버깅 - 재료 수: {len(ingredients)}")
        print(f"🔍 디버깅 - 조리순서 수: {len(steps)}")
        
        # 모든 필수 데이터가 있는지 확인
        if not title or not ingredients or not steps:
            print(f"⚠️ 필수 데이터 누락 - 제목: {bool(title)}, 재료: {bool(ingredients)}, 조리순서: {bool(steps)}")
            return None
            
        return {
            "title": title,
            "url": recipe_url,
            "ingredients": "; ".join(ingredients),
            "steps": " | ".join(numbered_steps)
        }
        
    except requests.RequestException as e:
        print(f"페이지 요청 오류 ({recipe_url}): {e}")
        return None
    except Exception as e:
        print(f"파싱 오류 ({recipe_url}): {e}")
        return None


if __name__ == "__main__":
    # 타겟 사이트 URL 수정
    base_url = "https://www.10000recipe.com/issue/view.html?cid=9999scrap"
    target_count = 200
    
    print("🚀 만개의레시피 크롤링 시작...")
    print(f"타겟 URL: {base_url}")
    print(f"목표 레시피 수: {target_count}개")
    
    # 여러 페이지에서 레시피 링크 수집
    recipe_links = get_all_recipe_links(base_url, target_count)

    if not recipe_links:
        print("❌ 레시피 링크를 찾을 수 없습니다. URL이나 셀렉터를 확인해주세요.")
        exit(1)

    # 데이터 수집
    data = []
    success_count = 0
    skip_count = 0  # 데이터 누락으로 건너뛴 수
    
    print(f"\n📊 {len(recipe_links)}개 레시피 상세 정보 수집 중...")
    
    for i, link in enumerate(recipe_links):
        if success_count >= target_count:  # 목표 개수 달성시 종료
            break
            
        print(f"[{i+1}/{len(recipe_links)}] 처리 중: {link}")
        
        detail = get_recipe_detail(link)
        if detail:
            data.append(detail)
            success_count += 1
            print(f"✅ {success_count}개 완료: {detail['title']}")
        else:
            # detail이 None이면 데이터 누락 또는 오류
            skip_count += 1
            print(f"⏭️ 데이터 누락 또는 오류로 건너뜀 ({skip_count}개)")
            
        # 서버 부하 방지 (1초 대기)
        time.sleep(1)

    print(f"\n📈 수집 완료:")
    print(f"✅ 성공: {success_count}개")
    print(f"⏭️ 건너뜀: {skip_count}개")

    if data:
        # 데이터 폴더 생성
        data_dir = "./crawling/data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        # CSV 저장 (완전한 데이터만)
        df = pd.DataFrame(data, columns=["title", "url", "ingredients", "steps"])
        output_file = os.path.join(data_dir, "recipes.csv")
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"📂 {output_file} 파일 저장 완료!")
        print(f"📊 총 {len(data)}개 완전한 레시피 데이터 수집됨")
        
        # 샘플 데이터 출력
        print("\n🔍 수집된 데이터 샘플:")
        for i, recipe in enumerate(data[:3]):
            print(f"\n[{i+1}] {recipe['title']}")
            print(f"URL: {recipe['url']}")
            print(f"재료: {recipe['ingredients'][:100]}...")
            print(f"조리법: {recipe['steps'][:100]}...")
    else:
        print("❌ 수집된 완전한 데이터가 없습니다.")