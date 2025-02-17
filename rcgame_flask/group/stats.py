import numpy as np
import scipy.stats as stats
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
        self.left_goals = 0
        self.right_goals = 0
        self.left_win_rate = 0.0
        self.right_win_rate = 0.0
        self.draw_rate = 0.0
        self.left_ave_goal = 0.0
        self.right_ave_goal = 0.0
        self.left_max_goal = 0
        self.right_max_goal = 0
        self.left_scored_count = 0
        self.right_scored_count = 0
        self.left_score_rate = 0.0
        self.right_score_rate = 0.0
        self.left_score_counts = {i: 0 for i in range(11)}
        self.right_score_counts = {i: 0 for i in range(11)}
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
        left_max_score = 10
        right_max_score = 10
        for match in matches:
            if match.left_score > match.right_score:
                self.left_win += 1
            elif match.left_score < match.right_score:
                self.right_win += 1
            else:
                self.draw += 1
            self.left_goals += match.left_score
            self.right_goals += match.right_score
            self.left_scored_count += 1 if match.left_score > 0 else 0
            self.right_scored_count += 1 if match.right_score > 0 else 0
            self.left_max_goal = max(self.left_max_goal, match.left_score)
            self.right_max_goal = max(self.right_max_goal, match.right_score)

            if match.left_score not in self.left_score_counts:
                if match.left_score > left_max_score:
                    for i in range(left_max_score+1, match.left_score+1):
                        self.left_score_counts[i] = 0
                    left_max_score = match.left_score
                self.left_score_counts[match.left_score] = 1
            else:
                self.left_score_counts[match.left_score] += 1

            if match.right_score not in self.right_score_counts:
                if match.right_score > right_max_score:
                    for i in range(right_max_score+1, match.right_score+1):
                        self.right_score_counts[i] = 0
                    right_max_score = match.right_score
                self.right_score_counts[match.right_score] = 1
            else:
                self.right_score_counts[match.right_score] += 1

            if match.host_name not in self.host_counts:
                self.host_counts[match.host_name] = 1
            else:
                self.host_counts[match.host_name] += 1

        if self.completed_count > 0:
            self.left_win_rate = self.left_win / self.completed_count
            self.right_win_rate = self.right_win / self.completed_count
            self.draw_rate = self.draw / self.completed_count
            self.left_ave_goals = self.left_goals / self.completed_count
            self.right_ave_goals = self.right_goals / self.completed_count
            self.left_score_rate = self.left_scored_count / self.completed_count
            self.right_score_rate = self.right_scored_count / self.completed_count

        left_scores = [match.left_score for match in matches]
        right_scores = [match.right_score for match in matches]
        self.left_mean_score, self.left_score_confidence_interval = compute_confidence_interval(left_scores)
        self.right_mean_score, self.right_score_confidence_interval = compute_confidence_interval(right_scores)
