#!/usr/bin/env python3
"""四季识别 — 人名级+字符级双层贝叶斯"""
from .core import BayesGuesser

SEASONS = ['春', '夏', '秋', '冬']


class SeasonGuesser(BayesGuesser):
    CLASSES = SEASONS
    PRIORS = {'春': 0.21, '夏': 0.24, '秋': 0.30, '冬': 0.25}
    CHAR_CSV = 'season_char.csv'
    NAME_CSV = 'season_name.csv'


_guesser = SeasonGuesser()


def guess(name, mode='auto'):
    return _guesser.guess(name, mode)


if __name__ == '__main__':
    for n in ['王伟', '刘亦菲', '李建国']:
        s, p, _ = guess(n)
        print(f'  {n}: {s} ({p:.4f})')
