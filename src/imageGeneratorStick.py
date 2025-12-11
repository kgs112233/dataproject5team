import os
import pandas as pd
import matplotlib.pyplot as plt


plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


def plot_top5_bar(ax, ratio_dict, title, color):
    sorted_items = sorted(ratio_dict.items(), key=lambda x: -x[1])[:5]
    labels, values = zip(*sorted_items)

    ax.barh(labels, values, color=color, alpha=0.85)
    ax.invert_yaxis()
    ax.set_title(title, fontsize=14)
    ax.set_xlabel("Ratio 값", fontsize=11)

    xmax = max(values) * 1.25
    ax.set_xlim(0, xmax)

    for i, v in enumerate(values):
        ax.text(v + xmax * 0.02, i, f"{v:.3f}",
                va="center", fontsize=10)


def make_bar_panel(genre, success_ratios, failure_ratios, output_path):

    delta_dict = {
        cat: success_ratios[cat] - failure_ratios[cat]
        for cat in success_ratios
    }

    top_factor, top_delta = sorted(
        delta_dict.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )[0]

    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    fig.suptitle(f"{genre} — SUCCESS / FAILURE 주요 요인", fontsize=18)

    plot_top5_bar(
        axes[0],
        success_ratios,
        "SUCCESS Top 5",
        color="steelblue"
    )

    plot_top5_bar(
        axes[1],
        failure_ratios,
        "FAILURE Top 5",
        color="indianred"
    )

    insight_text = (
        f"가장 영향을 많이 준 요인: {top_factor} "
        f"(SUCCESS - FAILURE = {top_delta:+.3f})"
    )

    plt.figtext(0.5, 0.02, insight_text, ha="center", fontsize=13)

    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    plt.subplots_adjust(right=0.92)

    plt.savefig(output_path, dpi=200)
    plt.close()


def generate_all_bar_panels(csv_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_csv(csv_path)
    genres = df["Selected_Genre"].unique()

    for genre in genres:

        row = df[df["Selected_Genre"] == genre].iloc[0]

        success_ratios = {}
        failure_ratios = {}

        for col in df.columns:
            if col.startswith(f"{genre}_SUCCESS_"):
                category = col.replace(f"{genre}_SUCCESS_", "").replace("_Ratio", "")
                success_ratios[category] = row[col]

            if col.startswith(f"{genre}_FAILURE_"):
                category = col.replace(f"{genre}_FAILURE_", "").replace("_Ratio", "")
                failure_ratios[category] = row[col]

        save_path = os.path.join(output_dir, f"{genre}_bar.png")
        make_bar_panel(genre, success_ratios, failure_ratios, save_path)

        print(f"완료 → {save_path}")


if __name__ == "__main__":
    generate_all_bar_panels(
        csv_path="genre_category_maximums.csv",
        output_dir="genre_final_bar_panels"
    )
