#!/usr/bin/env python3
"""
贝叶斯推理引擎 — 统一加载/平滑/对数概率/回退

双层特征:
  人名级: P(class|name) = (n_c + β·π_c) / (N + β)     人名频次>=NAME_MIN时启用
  字符级: log P(class|name) = log π_c + Σ log P(key_i|class)   Lidstone平滑, 永远有解
"""
import os, math, pickle

from .utils import given_name, pos_keys, to_simplified

_TABLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tables')


class BayesGuesser:
    CLASSES = []
    PRIORS = {}
    CHAR_CSV = None
    NAME_CSV = None
    ALPHA = 1.0        # 字符级 Lidstone 平滑
    BETA = 3.0         # 人名级先验伪计数强度
    NAME_MIN = 10      # 人名级启用最低频次
    RETURN_DIST = True

    def __init__(self):
        self._loaded = False

    # ---------- 加载 ----------

    def _load_csv(self, path):
        table = {}
        with open(path, 'r', encoding='utf-8') as f:
            next(f)
            for line in f:
                parts = line.rstrip('\n').split(',')
                if len(parts) < len(self.CLASSES) + 1:
                    continue
                try:
                    cnts = tuple(int(x) for x in parts[1:len(self.CLASSES) + 1])
                except ValueError:
                    continue
                table[parts[0]] = cnts
        return table

    def _load_table(self, csv_name):
        """优先读 .pkl 缓存；CSV 存在且更新时重建缓存。CSV 缺失时信任 pkl"""
        csv_path = os.path.join(_TABLES_DIR, csv_name)
        pkl_path = csv_path + '.pkl'
        pkl_ok = os.path.exists(pkl_path) and (
            not os.path.exists(csv_path) or
            os.path.getmtime(pkl_path) >= os.path.getmtime(csv_path))
        if pkl_ok:
            with open(pkl_path, 'rb') as f:
                return pickle.load(f)
        if not os.path.exists(csv_path):
            return {}
        table = self._load_csv(csv_path)
        try:
            with open(pkl_path, 'wb') as f:
                pickle.dump(table, f, protocol=pickle.HIGHEST_PROTOCOL)
        except OSError:
            pass
        return table

    def _load_model(self):
        if self._loaded:
            return
        self.char_counts = {}
        self.char_totals = [0] * len(self.CLASSES)
        self.name_counts = {}
        if self.CHAR_CSV:
            self.char_counts = self._load_table(self.CHAR_CSV)
            for cnts in self.char_counts.values():
                for i, c in enumerate(cnts):
                    self.char_totals[i] += c
        if self.NAME_CSV:
            self.name_counts = self._load_table(self.NAME_CSV)
        self._vocab = max(1, len(self.char_counts))
        self._loaded = True

    # ---------- 推理 ----------

    def _name_level(self, gn):
        cnts = self.name_counts.get(gn)
        if not cnts:
            return None
        total = sum(cnts)
        if total < self.NAME_MIN:
            return None
        denom = total + self.BETA
        dist = {}
        for i, c in enumerate(self.CLASSES):
            dist[c] = (cnts[i] + self.BETA * self.PRIORS.get(c, 1.0 / len(self.CLASSES))) / denom
        return dist

    def _char_level(self, keys):
        n = len(self.CLASSES)
        vocab = self._vocab
        known = [(k, self.char_counts[k]) for k in keys if k in self.char_counts]
        if not known:
            return dict(self.PRIORS) if self.PRIORS else {c: 1.0 / n for c in self.CLASSES}
        logs = []
        for i, c in enumerate(self.CLASSES):
            prior = self.PRIORS.get(c, 1.0 / n)
            lp = math.log(prior)
            denom = self.char_totals[i] + self.ALPHA * vocab
            for _, cnts in known:
                lp += math.log((cnts[i] + self.ALPHA) / denom)
            logs.append(lp)
        m = max(logs)
        exps = [math.exp(x - m) for x in logs]
        t = sum(exps)
        return {c: e / t for c, e in zip(self.CLASSES, exps)}

    def guess(self, name, mode='auto'):
        self._load_model()
        name = to_simplified(name.strip())
        if not name:
            return self._result('未知', 0.0, {})

        if mode in ('auto', 'namea'):
            gn = given_name(name)
        elif mode in ('namec', 'named', 'namee', 'namef'):
            gn = name
        else:
            raise ValueError(f"Unknown mode: {mode}, expected auto/namec/named/namee/namef")

        # 人名级优先
        if mode in ('auto', 'namea', 'namec') and self.NAME_CSV and gn:
            dist = self._name_level(gn)
            if dist:
                best = max(dist, key=dist.get)
                return self._result(best, dist[best], dist)

        # 字符级回退
        if mode == 'named':
            keys = [f'{gn}_p0'] if gn else []
        elif mode == 'namee':
            keys = [f'{gn}_p1'] if gn else []
        elif mode == 'namef':
            keys = [f'{gn}_p2'] if gn else []
        else:
            keys = pos_keys(gn)
        if not keys:
            return self._result('未知', 0.0, {})
        dist = self._char_level(keys)
        best = max(dist, key=dist.get)
        return self._result(best, dist[best], dist)

    def _result(self, label, prob, dist):
        if self.RETURN_DIST:
            return (label, prob, dist)
        return (label, prob)
