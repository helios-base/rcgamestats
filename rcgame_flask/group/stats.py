import os
import numpy as np
import scipy.stats as stats
from collections import Counter
from rcgame_flask.group.models import Group, Match, MatchStatus


def compute_confidence_interval(data, confidence=0.95):
    """
    Compute confidence interval for a given data set
    """
    if len(data) < 2:
        mean = np.mean(data) if data else 0.0
        return mean, (mean, mean)

    mean = np.mean(data)
    se = stats.sem(data)
    # if the standard error of the mean is 0, return mean as the confidence interval boundaries
    if se == 0:
        return mean, (mean, mean)

    interval = stats.t.interval(confidence, len(data) - 1, loc=mean, scale=se)
    return mean, interval


class GroupStats():
    """
    GroupStats class is used to store the statistics of a group.
    """
    def __init__(self, group_id):
        self.group_id = group_id
        self.group = Group.query.get(group_id)
        self.completed_count = 0
        self.left_win = 0
        self.right_win = 0
        self.draw = 0
        self.left_sum_of_scores = 0
        self.right_sum_of_scores = 0
        self.left_win_rate = 0.0
        self.right_win_rate = 0.0
        self.draw_rate = 0.0
        self.left_max_score = 0
        self.right_max_score = 0
        self.left_scored_games = 0
        self.right_scored_games = 0
        self.left_scored_games_rate = 0.0
        self.right_scored_games_rate = 0.0
        self.left_score_counts = {i: 0 for i in range(6)}
        self.right_score_counts = {i: 0 for i in range(6)}
        self.left_mean_score = 0.0
        self.right_mean_score = 0.0
        # self.left_score_confidence_interval = (0.0, 0.0)
        # self.right_score_confidence_interval = (0.0, 0.0)
        self.host_counts = {}

        self.__calculate()

    def __calculate(self):
        """
        Calculate the statistics of the group.
        """
        if self.group is None:
            return

        matches = Match.query.filter_by(group_id=self.group_id, processed=MatchStatus.COMPLETED).all()
        self.completed_count = len(matches)

        if self.completed_count == 0:
            return

        left_scores = np.array([match.left_score for match in matches if match.left_score >= 0])
        right_scores = np.array([match.right_score for match in matches if match.right_score >= 0])

        self.left_win = np.sum(left_scores > right_scores)
        self.right_win = np.sum(left_scores < right_scores)
        self.draw = np.sum(left_scores == right_scores)
        self.left_sum_of_scores = np.sum(left_scores)
        self.right_sum_of_scores = np.sum(right_scores)
        self.left_win_rate = self.left_win / self.completed_count
        self.right_win_rate = self.right_win / self.completed_count
        self.draw_rate = self.draw / self.completed_count
        self.left_max_score = np.max(left_scores)
        self.right_max_score = np.max(right_scores)
        self.left_scored_games = np.sum(left_scores > 0)
        self.right_scored_games = np.sum(right_scores > 0)
        self.left_scored_games_rate = self.left_scored_games / self.completed_count
        self.right_scored_games_rate = self.right_scored_games / self.completed_count

        self.left_score_counts = {i: int(count) for i, count in enumerate(np.bincount(left_scores, minlength=6))}
        self.right_score_counts = {i: int(count) for i, count in enumerate(np.bincount(right_scores, minlength=6))}

        self.left_mean_score = np.mean(left_scores)
        self.right_mean_score = np.mean(right_scores)
        # self.left_mean_score, self.left_score_confidence_interval = compute_confidence_interval(left_scores)
        # self.right_mean_score, self.right_score_confidence_interval = compute_confidence_interval(right_scores)

        self.host_counts = Counter(match.host_name for match in matches)

    def compute_confidence_intervals(self):
        """
        Compute confidence interval for the mean scores of left and right teams.
        """
        if self.completed_count == 0:
            return

        matches = Match.query.filter_by(group_id=self.group_id, processed=MatchStatus.COMPLETED).all()

        left_scores = np.array([match.left_score for match in matches if match.left_score >= 0])
        right_scores = np.array([match.right_score for match in matches if match.right_score >= 0])

        self.left_mean_score, self.left_score_confidence_interval = compute_confidence_interval(left_scores)
        self.right_mean_score, self.right_score_confidence_interval = compute_confidence_interval(right_scores)

        return self.left_score_confidence_interval, self.right_score_confidence_interval


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
    return name


def plot_confidence_intervals(image_dir, stats_list):
    """
    Plot the confidence intervals of the mean scores of left and right teams for the given group ids.
    """
    import matplotlib
    matplotlib.use('Agg')  # Must be called before importing matplotlib.pyplot to avoid interactive mode
    import matplotlib.pyplot as plt

    # fig, axes = plt.subplots(1, 2, figsize=(16, 9), gridspec_kw={'wspace': 0})
    fig, axes = plt.subplots(1, 2, figsize=(12, 6), gridspec_kw={'wspace': 0})
    for i, st in enumerate(stats_list):
        left_ci, right_ci = st.compute_confidence_intervals()
        y = i
        __plot_confidence_interval(axes[0], st.left_mean_score, left_ci, y, 'blue')
        __plot_confidence_interval(axes[1], st.right_mean_score, right_ci, y, 'red')

    # draw horizontal lines
    for ax in axes:
        for i in range(len(stats_list)):
            ax.axhline(y=i, color='gray', linestyle='--', linewidth=0.5)

    plt.subplots_adjust(wspace=0.0)
    axes[0].set_ylabel('Group')
    axes[0].set_yticks(np.arange(len(stats_list)))
    axes[0].set_yticklabels([__split_group_name(st.group.name) for st in stats_list])
    axes[0].set_xlabel('Left')
    axes[0].set_title('95% Confidence Interval of Left Scores')
    axes[0].set_ylim(-1, len(stats_list))

    axes[1].set_yticks([])  # hide y-axis
    axes[1].set_xlabel('Right')
    axes[1].set_title('95% Confidence Interval of Right Scores')
    axes[1].set_ylim(-1, len(stats_list))

    plt.tight_layout()
    filename = 'confidence_intervals.png'
    filepath = os.path.join(image_dir, filename)
    plt.savefig(filepath)

    return filepath
