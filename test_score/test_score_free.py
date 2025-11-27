import math

def score_free(ccu, ccu_max, downloads, downloads_max,
               rating, pub_rev, pub_rev_max):
    # 정규화 함수
    def norm_log(x, m):
        return math.log(1 + x) / math.log(1 + m) if m > 0 else 0

    # 무료 게임 전용 수익 점수 대체
    free_rev_score = (
        0.5 * norm_log(downloads, downloads_max) +
        0.5 * norm_log(ccu, ccu_max)
    )

    ccu_score = norm_log(ccu, ccu_max)
    down_score = norm_log(downloads, downloads_max)
    rating_score = rating / 100
    pub_score = norm_log(pub_rev, pub_rev_max)

    final = 10 * (
        0.3 * free_rev_score +  # 수익 30% 대체
        0.3 * ccu_score +
        0.2 * down_score +
        0.1 * rating_score +
        0.1 * pub_score
    )
    return final
