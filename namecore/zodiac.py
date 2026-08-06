#!/usr/bin/env python3
"""星座识别 — 人名级+字符级双层贝叶斯"""
from .core import BayesGuesser

ZODIACS = ['摩羯座', '水瓶座', '双鱼座', '白羊座', '金牛座', '双子座',
           '巨蟹座', '狮子座', '处女座', '天秤座', '天蝎座', '射手座']


class ZodiacGuesser(BayesGuesser):
    CLASSES = ZODIACS
    PRIORS = {
        '白羊座': 0.069, '金牛座': 0.073, '双子座': 0.077, '巨蟹座': 0.079,
        '狮子座': 0.083, '处女座': 0.088, '天秤座': 0.101, '天蝎座': 0.099,
        '射手座': 0.087, '摩羯座': 0.084, '水瓶座': 0.079, '双鱼座': 0.081,
    }
    CHAR_CSV = 'zodiac_char.csv'
    NAME_CSV = 'zodiac_name.csv'


_guesser = ZodiacGuesser()


def guess(name, mode='auto'):
    return _guesser.guess(name, mode)


if __name__ == '__main__':
    for n in ['王伟', '刘亦菲', '李建国']:
        z, p, _ = guess(n)
        print(f'  {n}: {z} ({p:.4f})')
