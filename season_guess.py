#!/usr/bin/env python3
"""
四季识别模块 — 人名级别查找（贝叶斯）

模式: auto / namec
"""
import os
from utils import given_name, to_simplified

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_FREQ_FILE = os.path.join(_BASE_DIR, 'tables', 'seasonfreq.csv')

SEASONS = ['春', '夏', '秋', '冬']


class SeasonGuesser:
    PRIORS = {'春': 0.21, '夏': 0.24, '秋': 0.30, '冬': 0.25}

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
                    if len(parts) < len(SEASONS) + 1: continue
                    gn = parts[0]
                    try:
                        cnts = {s: int(c) for s, c in zip(SEASONS, parts[1:])}
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
        for s in SEASONS:
            probs[s] = self.PRIORS.get(s, 0.25) * raw.get(s, 0)
        t = sum(probs.values())
        if t == 0: return ('未知', 0.0, {})
        norm = {s: p / t for s, p in probs.items()}
        best = max(norm, key=norm.get)
        return (best, norm[best], norm)


_guesser = SeasonGuesser()


def guess(name, mode='auto'):
    return _guesser.guess(name, mode)


if __name__ == '__main__':
    for n in ['伟','建国','宇轩']:
        s, p, _ = guess(n, 'namec')
        print(f'{n}: {s} ({p:.4f})')
