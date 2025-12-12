import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

file_path = 'only_games.csv'
df = pd.read_csv(file_path)

# 데이터 집계
genre_counts = df['genres'].dropna().str.split(',').explode().str.strip().value_counts()

# 시각화 
# 데이터 정렬 (오름차순)
genre_counts_sorted = genre_counts.sort_values(ascending=True)

# 색상 설정 (Blue -> Red)
cmap = mcolors.LinearSegmentedColormap.from_list("BlueRed", ["blue", "red"])
norm = plt.Normalize(genre_counts_sorted.min(), genre_counts_sorted.max())
colors = cmap(norm(genre_counts_sorted.values))

# 그래프 그리기
plt.figure(figsize=(14, 10))
bars = plt.barh(genre_counts_sorted.index, genre_counts_sorted.values, color=colors, edgecolor='black', alpha=0.9)

# Total Games 표시 (오른쪽 하단)
total_games = len(df)
plt.text(0.95, 0.05, 
         f'Total Games: {total_games:,}', 
         fontsize=16, fontweight='bold', color='black',
         bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.5', alpha=0.9),
         ha='right', va='bottom', transform=plt.gca().transAxes)

# 디자인 및 숫자 표시
plt.title('Steam Game Count by Genre', fontsize=18, fontweight='bold', pad=20)
plt.xlabel('Number of Games', fontsize=12)
plt.grid(axis='x', linestyle='--', alpha=0.3)

for bar in bars:
    width = bar.get_width()
    plt.text(width + (genre_counts.max() * 0.01), bar.get_y() + bar.get_height()/2,
             f'{int(width):,}', va='center', fontsize=10)

plt.tight_layout()
plt.savefig('RedAndBlueOcean.png', dpi=300)