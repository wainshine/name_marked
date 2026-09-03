#!/usr/bin/env python3
"""
namecore — 中文姓名属性识别

用法:
    from namecore import guess_gender, guess_decade, guess_zodiac, guess_season, guess_solar

    guess_gender('王伟')          # → ('男', 概率)
    guess_decade('张宇轩')        # → ('2000s', 概率, {...})
    guess_zodiac('刘亦菲')        # → (星座, 概率, {...})
    guess_season('王伟')          # → (季节, 概率, {...})
    guess_solar('王伟')           # → (节气, 概率, {...})

    # 带准确示例数值的用法见 README「快速开始」（随版本验收，以实测为准）

输入模式: auto/namea(完整姓名) namec(名) named/namee/namef(单字/首字/末字)
"""

__version__ = '2.2.2'

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
