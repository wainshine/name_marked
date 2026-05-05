#!/usr/bin/env python3
"""
星座识别模块 — 人名级别查找（贝叶斯）

模式: auto(姓名) / namec(名)
"""
import os
from utils import given_name, to_simplified

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_FREQ_FILE = os.path.join(_BASE_DIR, 'tables', 'zodiacfreq.csv')

ZODIACS = ['摩羯座','水瓶座','双鱼座','白羊座','金牛座','双子座',
           '巨蟹座','狮子座','处女座','天秤座','天蝎座','射手座']


class ZodiacGuesser:
    PRIORS = {
        '白羊座':0.069,'金牛座':0.073,'双子座':0.077,'巨蟹座':0.079,
        '狮子座':0.083,'处女座':0.088,'天秤座':0.101,'天蝎座':0.099,
        '射手座':0.087,'摩羯座':0.084,'水瓶座':0.079,'双鱼座':0.081,
    }

    def __init__(self):
        self._loaded = False

    def _load_model(self):
        if self._loaded: return
        self.lookup = {}
        try:
            with open(_FREQ_FILE, 'r', encoding='utf-8') as f:
                next(f)
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) < len(ZODIACS) + 1: continue
                    gn = parts[0]
                    try:
                        cnts = {z: int(c) for z, c in zip(ZODIACS, parts[1:])}
                    except ValueError:
                        continue
                    total = sum(cnts.values())
                    if total > 0:
                        self.lookup[gn] = {z: c / total for z, c in cnts.items()}
        except (FileNotFoundError, StopIteration):
            pass
        self._loaded = True

    def guess(self, name, mode='auto'):
        self._load_model()
        name = to_simplified(name)
        if mode in ('named', 'namee', 'namef'):
            return ('未知', 0.0, {})  # 人名级别不支持单字查找

        if mode == 'auto':
            gn = given_name(name)
        elif mode == 'namec':
            gn = name
        else:
            raise ValueError(f"Unknown mode: {mode}, expected auto/namec")

        if not gn: return ('未知', 0.0, {})
        raw = self.lookup.get(gn)
        if not raw: return ('未知', 0.0, {})

        probs = {}
        for z in ZODIACS:
            probs[z] = self.PRIORS.get(z, 1/12) * raw.get(z, 0)
        t = sum(probs.values())
        if t == 0: return ('未知', 0.0, {})
        norm = {z: p / t for z, p in probs.items()}
        best = max(norm, key=norm.get)
        return (best, norm[best], norm)


_guesser = ZodiacGuesser()


def guess(name, mode='auto'):
    return _guesser.guess(name, mode)


if __name__ == '__main__':
    for n, m in [('王伟','auto'),('王伟','namec')]:
        z, p, _ = guess(n, m)
        print(f'{n} ({m}): {z} ({p:.4f})')
