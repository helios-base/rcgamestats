import io
import numpy as np


def __plot_confidence_interval(ax, mean_scores, ci_scores, y, color):
    """
    Plot the confidence interval of the mean score
    """
    ax.errorbar(x=mean_scores, y=y, xerr=[[mean_scores - ci_scores[0]], [ci_scores[1] - mean_scores]], fmt='o', color=color, elinewidth=2, capsize=5)
    # ax.errorbar(x=mean_scores, y=y, xerr=[[mean_scores - ci_scores[0]], [ci_scores[1] - mean_scores]],
    #             fmt='|', markersize=20, markeredgewidth=3,
    #             color=color, elinewidth=2, capsize=5)
    ax.text(mean_scores, y+0.2, f'{mean_scores:.3f}', color=color, fontsize=10, ha='center')
    ax.text(ci_scores[0], y+0.1, f'{ci_scores[0]:.3f}', color=color, fontsize=10, ha='center')
    ax.text(ci_scores[1], y+0.1, f'{ci_scores[1]:.3f}', color=color, fontsize=10, ha='center')


def __split_group_name(name):
    """
    Split group name into two lines
    """
    parts = name.split('-') # split by '-'
    if len(parts) == 4:  # if there are 4 parts, split into two lines
        return "{}-{}\n{}-{}".format(parts[0], parts[1], parts[2], parts[3])
    elif len(parts) > 4:
        return "{}-{}\n{}".format(parts[0], parts[1], '-'.join(parts[2:]))
    return name


def plot_confidence_intervals(stats_list):
    """
    Plot the confidence intervals of the mean scores of left and right teams for the given group ids.
    """
    import matplotlib
    matplotlib.use('Agg')  # Must be called before importing matplotlib.pyplot to avoid interactive mode
    import matplotlib.pyplot as plt

    # fig, axes = plt.subplots(1, 2, figsize=(16, 9), gridspec_kw={'wspace': 0})
    # fig, axes = plt.subplots(1, 2, figsize=(12, 6), gridspec_kw={'wspace': 0})
    fig_height = min(max(6, len(stats_list) * 0.4), 12)
    fig_width = 12  # min(max(12, fig_height*2), 19)
    fig, axes = plt.subplots(1, 2, figsize=(fig_width, fig_height), gridspec_kw={'wspace': 0})
    for i, st in enumerate(stats_list):
        left_ci = st.left_score_confidence_interval_lower, st.left_score_confidence_interval_upper
        right_ci = st.right_score_confidence_interval_lower, st.right_score_confidence_interval_upper
        y = i
        __plot_confidence_interval(axes[0], st.left_mean_score, left_ci, y, 'blue')
        __plot_confidence_interval(axes[1], st.right_mean_score, right_ci, y, 'red')

    # draw horizontal lines
    for ax in axes:
        for i in range(len(stats_list)):
            ax.axhline(y=i, color='gray', linestyle='--', linewidth=0.5)

    # plt.subplots_adjust(wspace=0.0)
    plt.subplots_adjust(left=0.3, wspace=0.0)
    axes[0].set_ylabel('Group')
    axes[0].set_yticks(np.arange(len(stats_list)))
    axes[0].set_yticklabels([__split_group_name(st.group.name) for st in stats_list], fontsize=8)
    # axes[0].set_yticklabels([st.group.name for st in stats_list])
    axes[0].set_xlabel('Left')
    axes[0].set_title('95% Confidence Interval of Left Scores')
    axes[0].set_ylim(-1, len(stats_list))

    axes[1].set_yticks([])  # hide y-axis
    axes[1].set_xlabel('Right')
    axes[1].set_title('95% Confidence Interval of Right Scores')
    axes[1].set_ylim(-1, len(stats_list))
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)

    return buf
