import os
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


def add_other(ratios):
    total = sum(ratios.values())
    if total < 1:
        ratios["Other"] = round(1 - total, 5)
    return ratios


def get_color_map(categories):
    base_colors = plt.cm.tab20.colors
    return {cat: base_colors[i % len(base_colors)] for i, cat in enumerate(categories)}


def make_pie(ax, ratios, title, color_map, label_limit=3):
    labels = list(ratios.keys())
    values = list(ratios.values())
    colors = [color_map[l] for l in labels]

    sorted_items = sorted(ratios.items(), key=lambda x: x[1], reverse=True)
    show_labels = {item[0] for item in sorted_items[:label_limit]}

    display_labels = [
        f"{lbl} ({values[i]*100:.1f}%)" if lbl in show_labels else ""
        for i, lbl in enumerate(labels)
    ]

    wedges, texts, autotexts = ax.pie(
        values,
        labels=display_labels,
        autopct=lambda pct: f"{pct:.1f}%" if pct >= 5 else "",
        startangle=90,
        textprops={'fontsize': 13},
        labeldistance=1.15,
        pctdistance=0.75,
        wedgeprops={'linewidth': 1, 'edgecolor': 'white'},
        colors=colors
    )

    ax.set_title(title, fontsize=22)

    for t in autotexts:
        t.set_color("white")
        t.set_fontweight("bold")


def make_panel(genre, success_ratios, failure_ratios, output_path):

    success_ratios = add_other(success_ratios)
    failure_ratios = add_other(failure_ratios)

    all_cats = sorted(set(success_ratios) | set(failure_ratios))
    color_map = get_color_map(all_cats)

    fig, axes = plt.subplots(1, 2, figsize=(18, 10))
    fig.suptitle(f"{genre} – SUCCESS / FAILURE 비율", fontsize=26)

    make_pie(axes[0], success_ratios, "SUCCESS", color_map)
    make_pie(axes[1], failure_ratios, "FAILURE", color_map)

    handles = [
        plt.Line2D([0], [0], marker='o', color='w',
                   markerfacecolor=color_map[c], markersize=12)
        for c in all_cats
    ]

    fig.legend(handles, all_cats, loc='lower center', fontsize=13, ncol=4)

    plt.tight_layout(rect=[0, 0.08, 1, 0.95])
    plt.savefig(output_path, dpi=220)
    plt.close()


def generate_all(csv_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_csv(csv_path)
    genres = df["Selected_Genre"].unique()

    for genre in genres:
        row = df[df["Selected_Genre"] == genre].iloc[0]

        success = {
            col.replace(f"{genre}_SUCCESS_", "").replace("_Ratio", ""): row[col]
            for col in df.columns if col.startswith(f"{genre}_SUCCESS_")
        }
        failure = {
            col.replace(f"{genre}_FAILURE_", "").replace("_Ratio", ""): row[col]
            for col in df.columns if col.startswith(f"{genre}_FAILURE_")
        }

        output_path = os.path.join(output_dir, f"{genre}_pie.png")
        make_panel(genre, success, failure, output_path)
        print("완료:", output_path)


if __name__ == "__main__":
    generate_all(
        csv_path="genre_category_maximums.csv",
        output_dir="genre_pie"
    )
