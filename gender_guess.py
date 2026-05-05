#!/usr/bin/env python3
"""
性别识别模块 — 位置感知朴素贝叶斯

模式:
  'auto'  姓名，自动提取名部分（默认）
  'namec' 名（已去除姓氏）
  'named' 单字名
  'namee' 双字名首字
  'namef' 双字名末字
"""
import os
from utils import mode_keys, to_simplified

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_FREQ_FILE = os.path.join(_BASE_DIR, 'tables', 'charfreq.csv')


class GenderGuesser:
    PRIOR_MALE = 0.5124
    PRIOR_FEMALE = 0.4876

    def __init__(self):
        self._loaded = False

    def _load_model(self):
        if self._loaded: return
        self.freq = {}
        try:
            with open(_FREQ_FILE, 'r', encoding='utf-8') as f:
                next(f)
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) < 3: continue
                    try:
                        self.freq[parts[0]] = (int(parts[1]), int(parts[2]))
                    except ValueError:
                        continue
        except (FileNotFoundError, StopIteration):
            pass
        self._loaded = True

    def guess(self, name, mode='auto'):
        self._load_model()
        name = to_simplified(name)
        keys = mode_keys(name, mode)
        if not keys: return ('未知', 0.0)

        pf = self.PRIOR_FEMALE
        pm = self.PRIOR_MALE
        for k in keys:
            f_c, m_c = self.freq.get(k, (0, 0))
            pf *= f_c
            pm *= m_c

        if pm > pf: return ('男', pm / (pm + pf))
        elif pf > pm: return ('女', pf / (pm + pf))
        return ('未知', 0.0)


_guesser = GenderGuesser()


def guess(name, mode='auto'):
    return _guesser.guess(name, mode)


if __name__ == '__main__':
    names = ['王伟','刘亦菲','李建国','张宇轩','刘星宇','黄自强','杨洋','欧阳芳菲']
    print('=== auto (姓名) ===')
    for n in names:
        g, p = guess(n)
        print(f'  {n}: {g} ({p:.4f})')
    print('=== namec (名) ===')
    for n in ['伟','亦菲','建国','宇轩','星宇','自强','洋','芳菲']:
        g, p = guess(n, 'namec')
        print(f'  {n}: {g} ({p:.4f})')
    print('=== namee/namef (拆字) ===')
    for e, f in [('建','国'),('宇','轩'),('星','宇'),('芳','菲')]:
        ge, _ = guess(e, 'namee')
        gf, _ = guess(f, 'namef')
        print(f'  {e}={ge}  {f}={gf}')
