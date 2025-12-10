import pandas as pd
import numpy as np

# 1. 예시를 위해 가상의 게임 데이터 100개를 생성
np.random.seed(42)
data = {
    '게임명': [f'Game_{i}' for i in range(1, 101)],
    '게임수익': np.random.randint(1000, 100000000, 100),     #각 종류마다 임의의 범위로 값 생성
    '최대동접자': np.random.randint(100, 500000, 100),       
    '다운로드수': np.random.randint(100, 1000000, 100),    
    '스팀평점': np.random.randint(40, 100, 100),           
    '배급사수익': np.random.randint(5000, 500000000, 100),  
    '리뷰수': np.random.randint(10, 5000, 100)              
}
df = pd.DataFrame(data)


# 2. 전처리: 리뷰 50개 미만 필터링
df = df[df['리뷰수'] >= 50].copy()


# 3. 로그 변환 (데이터 스케일 줄이기)
# 평점을 제외한 나머지 4개 지표는 단위가 크고 편차가 심하므로 로그 씌우기.
# 평점은 단위가 작기 때문에 로그 변환 없이 바로 정규화
df['log_게임수익'] = np.log1p(df['게임수익'])
df['log_최대동접자'] = np.log1p(df['최대동접자'])
df['log_다운로드수'] = np.log1p(df['다운로드수'])
df['log_배급사수익'] = np.log1p(df['배급사수익'])


# 4. Min-Max 정규화 (0~1 사이 값으로 변환)
def min_max_scale(series):
    return (series - series.min()) / (series.max() - series.min())

# 로그 변환된 값들을 0~1로 만들기.(4개의 지표만)
df['norm_게임수익'] = min_max_scale(df['log_게임수익'])
df['norm_최대동접자'] = min_max_scale(df['log_최대동접자'])
df['norm_다운로드수'] = min_max_scale(df['log_다운로드수'])
df['norm_배급사수익'] = min_max_scale(df['log_배급사수익'])
df['norm_스팀평점'] = min_max_scale(df['스팀평점'])



# 5. 가중치 적용 및 최종 점수 계산
# 가중치: 게임수익(30%), 동접자(30%), 다운로드(20%), 평점(10%), 배급사수익(10%)
df['종합점수'] = (
    (df['norm_게임수익'] * 0.3) +
    (df['norm_최대동접자'] * 0.3) +
    (df['norm_다운로드수'] * 0.2) +
    (df['norm_스팀평점'] * 0.1) +
    (df['norm_배급사수익'] * 0.1)
)


# 6. 순위 산정 및 그룹 분류 (상위 20%, 하위 20%) 내림차순 정렬
df_sorted = df.sort_values(by='종합점수', ascending=False)

n = len(df_sorted)
top_cut = int(n * 0.2)
bottom_cut = int(n * 0.8) 

top_group = df_sorted[:top_cut]
bottom_group = df_sorted[bottom_cut:]


# 7. 결과 출력
print(f"분석 결과 (총 {n}개 게임)")
print(f"상위 20% (흥행): {len(top_group)}개")
print(f"하위 20% (실패): {len(bottom_group)}개")
print("\n")

print("[Top 10 흥행 게임 예시]")
print(top_group[['게임명', '종합점수', '게임수익', '최대동접자', '다운로드수', '스팀평점', '배급사수익']].head(10))
print("\n")

print("[Bottom 10 실패 게임 예시]")
print(bottom_group[['게임명', '종합점수', '게임수익', '최대동접자', '다운로드수', '스팀평점', '배급사수익']].tail(10))