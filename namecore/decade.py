#!/usr/bin/env python3
"""年代识别 — 人名级+字符级双层贝叶斯"""
from .core import BayesGuesser

DECADE_CLASSES = ['1950s前', '1960s', '1970s', '1980s', '1990s', '2000s']


class DecadeGuesser(BayesGuesser):
    CLASSES = DECADE_CLASSES
    PRIORS = {
        '1950s前': 0.14, '1960s': 0.16, '1970s': 0.18,
        '1980s': 0.20, '1990s': 0.17, '2000s': 0.15,
    }
    CHAR_CSV = 'decade_char.csv'
    NAME_CSV = 'decade_name.csv'


_guesser = DecadeGuesser()


def guess(name, mode='auto'):
    return _guesser.guess(name, mode)


if __name__ == '__main__':
    for n in ['王伟', '刘亦菲', '李建国', '张宇轩', '易烊千玺']:
        d, p, _ = guess(n)
        print(f'  {n}: {d} ({p:.4f})')
