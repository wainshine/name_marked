#!/usr/bin/env python3
"""
namecore — 中文姓名属性识别

用法:
    from namecore import guess_gender, guess_decade, guess_zodiac, guess_season, guess_solar

    guess_gender('王伟')          # → ('男', 0.99)
    guess_decade('张宇轩')        # → ('2000s', 0.86, {...})
    guess_zodiac('刘亦菲')        # → ('天秤座', 0.10, {...})
    guess_season('王伟')          # → ('秋', 0.30, {...})
    guess_solar('王伟')           # → ('寒露', 0.06, {...})

输入模式: auto/namea(完整姓名) namec(名) named/namee/namef(单字/首字/末字)
"""

__version__ = '2.0.0'

from .gender import guess as guess_gender
from .decade import guess as guess_decade
from .zodiac import guess as guess_zodiac
from .season import guess as guess_season
from .solar import guess as guess_solar
from .utils import given_name, pos_keys, to_simplified

__all__ = [
    'guess_gender', 'guess_decade', 'guess_zodiac', 'guess_season', 'guess_solar',
    'given_name', 'pos_keys', 'to_simplified',
]
