#!/usr/bin/env python3
"""
二十四节气识别模块 — 人名级别查找（贝叶斯）

模式: auto / namec
"""
import os
from utils import given_name, to_simplified

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_FREQ_FILE = os.path.join(_BASE_DIR, 'tables', 'solarfreq.csv')

SOLAR_TERMS = [
    '小寒','大寒','立春','雨水','惊蛰','春分',
    '清明','谷雨','立夏','小满','芒种','夏至',
    '小暑','大暑','立秋','处暑','白露','秋分',
    '寒露','霜降','立冬','小雪','大雪','冬至',
]

SOLAR_PRIORS = {
    '小寒':0.038,'大寒':0.039,'立春':0.043,'雨水':0.040,
    '惊蛰':0.039,'春分':0.033,'清明':0.037,'谷雨':0.037,
    '立夏':0.036,'小满':0.034,'芒种':0.040,'夏至':0.036,
    '小暑':0.042,'大暑':0.036,'立秋':0.048,'处暑':0.043,
    '白露':0.048,'秋分':0.050,'寒露':0.054,'霜降':0.048,
    '立冬':0.049,'小雪':0.043,'大雪':0.043,'冬至':0.044,
}


class SolarGuesser:
    PRIORS = SOLAR_PRIORS

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
                    if len(parts) < len(SOLAR_TERMS) + 1: continue
                    gn = parts[0]
                    try:
                        cnts = {s: int(c) for s, c in zip(SOLAR_TERMS, parts[1:])}
                    except ValueError:
                        continue
                    total = sum(cnts.values())
                    if total > 0:
                        self.lookup[gn] = {s: c / total for s, c in cnts.items()}
        except (FileNotFoundError, StopIteration):
            pass
        self._loaded = True

    def guess(self, name, mode='auto'):
        self._load_model()
        name = to_simplified(name)
        if mode in ('named', 'namee', 'namef'):
            return ('未知', 0.0, {})
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
        for s in SOLAR_TERMS:
            probs[s] = self.PRIORS.get(s, 1/24) * raw.get(s, 0)
        t = sum(probs.values())
        if t == 0: return ('未知', 0.0, {})
        norm = {s: p / t for s, p in probs.items()}
        best = max(norm, key=norm.get)
        return (best, norm[best], norm)


_guesser = SolarGuesser()


def guess(name, mode='auto'):
    return _guesser.guess(name, mode)


if __name__ == '__main__':
    for n in ['伟','建国','宇轩']:
        s, p, _ = guess(n, 'namec')
        print(f'{n}: {s} ({p:.4f})')
