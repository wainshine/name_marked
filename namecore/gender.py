#!/usr/bin/env python3
"""性别识别 — 人名级+字符级双层贝叶斯"""
from .core import BayesGuesser


class GenderGuesser(BayesGuesser):
    CLASSES = ['女', '男']
    PRIORS = {'男': 0.5124, '女': 0.4876}
    CHAR_CSV = 'gender_char.csv'
    NAME_CSV = 'gender_name.csv'
    RETURN_DIST = False


_guesser = GenderGuesser()


def guess(name, mode='auto'):
    return _guesser.guess(name, mode)


if __name__ == '__main__':
    for n in ['王伟', '刘亦菲', '李建国', '张宇轩', '易烊千玺', '黄婷婷']:
        g, p = guess(n)
        print(f'  {n}: {g} ({p:.4f})')
