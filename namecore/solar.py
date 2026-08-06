#!/usr/bin/env python3
"""节气识别 — 人名级+字符级双层贝叶斯"""
from .core import BayesGuesser

SOLAR_TERMS = [
    '小寒', '大寒', '立春', '雨水', '惊蛰', '春分',
    '清明', '谷雨', '立夏', '小满', '芒种', '夏至',
    '小暑', '大暑', '立秋', '处暑', '白露', '秋分',
    '寒露', '霜降', '立冬', '小雪', '大雪', '冬至',
]


class SolarGuesser(BayesGuesser):
    CLASSES = SOLAR_TERMS
    PRIORS = {
        '小寒': 0.038, '大寒': 0.039, '立春': 0.043, '雨水': 0.040,
        '惊蛰': 0.039, '春分': 0.033, '清明': 0.037, '谷雨': 0.037,
        '立夏': 0.036, '小满': 0.034, '芒种': 0.040, '夏至': 0.036,
        '小暑': 0.042, '大暑': 0.036, '立秋': 0.048, '处暑': 0.043,
        '白露': 0.048, '秋分': 0.050, '寒露': 0.054, '霜降': 0.048,
        '立冬': 0.049, '小雪': 0.043, '大雪': 0.043, '冬至': 0.044,
    }
    CHAR_CSV = 'solar_char.csv'
    NAME_CSV = 'solar_name.csv'


_guesser = SolarGuesser()


def guess(name, mode='auto'):
    return _guesser.guess(name, mode)


if __name__ == '__main__':
    for n in ['王伟', '刘亦菲', '李建国']:
        s, p, _ = guess(n)
        print(f'  {n}: {s} ({p:.4f})')
