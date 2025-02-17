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
        self.left_score_confidence_interval = (0.0, 0.0)
        self.right_score_confidence_interval = (0.0, 0.0)
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

        left_scores = np.array([match.left_score for match in matches])
        right_scores = np.array([match.right_score for match in matches])

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

        self.left_mean_score, self.left_score_confidence_interval = compute_confidence_interval(left_scores)
        self.right_mean_score, self.right_score_confidence_interval = compute_confidence_interval(right_scores)

        self.host_counts = Counter(match.host_name for match in matches)
