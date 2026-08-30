#!/usr/bin/env python3
"""导出性别回退表 gender_guess.csv — 消灭 name_nlp 对 namecore 的运行时 import。

name_nlp s12 性别回填原方式: gender_name.csv 直查 + 跨仓 `from namecore import guess_gender`
回退(52万次/轮, "王"+名 拼万能姓)。本脚本把回退结果预计算成文件契约:
对 name_nlp 的 NameC 修正表全集, 凡性别人名表(gender_name.csv)未覆盖的名,
用 guess_gender("王"+名) 预算好男孩概率落盘。

产物: namecore/tables/gender_guess.csv  (name,boy_prob  utf-8-sig)
用法: python3 scripts/export_gender_guess.py
"""
import csv
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from namecore import guess_gender

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMEC_FIX = "/Users/wainshine/newAI/name_nlp/output/freq/NameC词频-修正.csv"  # 文件契约, 跨仓只读
OUT = os.path.join(BASE_DIR, 'namecore', 'tables', 'gender_guess.csv')
GENDER_NAME = os.path.join(BASE_DIR, 'namecore', 'tables', 'gender_name.csv')

t0 = time.time()
for path, hint in [(GENDER_NAME, '请先运行 scripts/train.py 生成频率表'),
                   (NAMEC_FIX, '请确认 name_nlp 已生成 NameC词频-修正.csv')]:
    if not os.path.isfile(path):
        print(f'错误: 依赖文件不存在: {path}\n  {hint}')
        sys.exit(1)

direct = set()
with open(GENDER_NAME, encoding='utf-8') as f:
    r = csv.reader(f)
    next(r)
    for row in r:
        direct.add(row[0])
print(f'人名级表 {len(direct):,} ({time.time()-t0:.0f}s)', flush=True)

n = n_fallback = 0
with open(NAMEC_FIX, encoding='utf-8-sig') as f, \
        open(OUT + '.tmp', 'w', encoding='utf-8-sig', newline='') as fo:
    r = csv.reader(f)
    next(r)
    w = csv.writer(fo)
    w.writerow(['name', 'boy_prob'])
    for row in r:
        nc = row[0]
        n += 1
        if nc in direct:
            continue
        gender, prob = guess_gender('王' + nc)  # 与 name_nlp s12 原调用方式逐字一致
        boy = prob if gender == '男' else 1 - prob
        w.writerow([nc, f'{boy:.4f}'])
        n_fallback += 1
        if n_fallback % 500000 == 0:
            print(f'  {n_fallback:,} ({(time.time()-t0)/60:.1f}分)', flush=True)
os.replace(OUT + '.tmp', OUT)
print(f'✔ 完成: NameC全集 {n:,}, 回退导出 {n_fallback:,} → {OUT} ({(time.time()-t0)/60:.1f}分)')
