#!/usr/bin/env python3
"""
年代识别模块 — 位置感知朴素贝叶斯

模式: auto / namec / named / namee / namef
"""
import os
from utils import mode_keys, to_simplified

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_FREQ_FILE = os.path.join(_BASE_DIR, 'tables', 'decadefreq.csv')

_DECADE_CLASSES = ['1950s前', '1960s', '1970s', '1980s', '1990s', '2000s']


class DecadeGuesser:
    PRIORS = {
        '1950s前': 0.14, '1960s': 0.16,
        '1970s': 0.18, '1980s': 0.20, '1990s': 0.17,
        '2000s': 0.15,
    }

    def __init__(self):
        self._loaded = False

    def _load_model(self):
        if self._loaded: return
        self.freq = {}
        lines = []
        totals = {d: 0 for d in _DECADE_CLASSES}
        try:
            with open(_FREQ_FILE, 'r', encoding='utf-8') as f:
                next(f)
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) < len(_DECADE_CLASSES) + 1: continue
                    try:
                        cnts = [int(x) for x in parts[1:]]
                    except ValueError:
                        continue
                    for d, c in zip(_DECADE_CLASSES, cnts):
                        totals[d] += c
                    lines.append((parts[0], cnts))
        except (FileNotFoundError, StopIteration):
            pass

        for d in _DECADE_CLASSES:
            if totals[d] == 0:
                totals[d] = 1

        for key, cnts in lines:
            self.freq[key] = {}
            for d, c in zip(_DECADE_CLASSES, cnts):
                self.freq[key][d] = c / totals[d]

        self._loaded = True

    def guess(self, name, mode='auto'):
        self._load_model()
        name = to_simplified(name)
        keys = mode_keys(name, mode)
        if not keys: return ('未知', 0.0, {})

        probs = {}
        for d in _DECADE_CLASSES:
            p = self.PRIORS.get(d, 0)
            for k in keys:
                p *= self.freq.get(k, {}).get(d, 0)
            probs[d] = p
        t = sum(probs.values())
        if t == 0: return ('未知', 0.0, {})
        norm = {d: v / t for d, v in probs.items()}
        best = max(norm, key=norm.get)
        return (best, norm[best], norm)


_guesser = DecadeGuesser()


def guess(name, mode='auto'):
    return _guesser.guess(name, mode)


if __name__ == '__main__':
    print('=== auto ===')
    for n in ['王伟','刘亦菲','张宇轩','李建国']:
        d, p, _ = guess(n)
        print(f'  {n}: {d} ({p:.4f})')
    print('=== namec ===')
    for n in ['伟','亦菲','宇轩','建国']:
        d, p, _ = guess(n, 'namec')
        print(f'  {n}: {d} ({p:.4f})')
    print('=== namee/namef ===')
    for e, f in [('宇','轩'),('亦','菲'),('建','国')]:
        de, _, _ = guess(e, 'namee')
        df, _, _ = guess(f, 'namef')
        print(f'  {e}={de}  {f}={df}')
