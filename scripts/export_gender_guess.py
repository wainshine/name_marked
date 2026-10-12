#!/usr/bin/env python3
"""导出性别回退表 gender_guess.csv — 消灭 name_nlp 对 namecore 的运行时 import。

name_nlp s12 性别回填方式: gender_name.csv 直查 + gender_guess.csv 回退(跨仓 import 已消灭)。
本脚本把回退结果预计算成文件契约: 对 name_nlp 的 NameC 修正表全集,
凡性别人名表(gender_name.csv)已覆盖的名跳过, 其余预算男孩概率落盘
(两表因此构成**互补分割**: gender_guess == NameC − gender_name)。

调用口径(拼万能姓等 4 条隐含约定)的书写处是 name_nlp `docs/CONTRACTS.md` §1 注 3, 本脚本不复述。
收尾做"关系自证": 读回三张表断言并打印集合关系与 sha256(对端 run_docchecks C6 亦守同三条关系)。

产物: namecore/tables/gender_guess.csv  (name,boy_prob  utf-8-sig)
用法: python3 scripts/export_gender_guess.py
"""
import csv
import hashlib
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from namecore import guess_gender

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMEC_FIX = "/Users/wainshine/newAI/name_nlp/output/freq/NameC词频-修正.csv"  # 文件契约, 跨仓只读
OUT = os.path.join(BASE_DIR, 'namecore', 'tables', 'gender_guess.csv')
GENDER_NAME = os.path.join(BASE_DIR, 'namecore', 'tables', 'gender_name.csv')
UY = os.path.join(BASE_DIR, 'namecore', 'tables', 'unihan_year.csv')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def key_set(path, enc):
    """读 CSV 第 0 列 → (键集合, 数据行数)。"""
    with open(path, encoding=enc, newline='') as f:
        r = csv.reader(f)
        next(r)
        rows = [row for row in r if row]
    return {row[0] for row in rows}, len(rows)


def self_prove():
    """关系自证：断言并打印 gender_guess 与 gender_name 的互补分割关系。

    守的是这条不变量（README「对外契约」/ HANDOVER §9 第 5 条）：
        gender_guess == NameC − gender_name  →  交集必空 + 并集必覆盖 NameC
    违反任一条 ⇒ 对端 s12 对查不到的名静默兜底 0.5（无报警），故在源头可见。
    """
    print('\n== 关系自证（读回三张表）==', flush=True)
    gn, n_gn = key_set(GENDER_NAME, 'utf-8')
    gg, n_gg = key_set(OUT, 'utf-8-sig')
    nc, n_nc = key_set(NAMEC_FIX, 'utf-8-sig')
    nc.discard('NameC')                      # 表头行已被 next() 跳过, 这里防列名同时是键
    inter = gg & gn
    gap = nc - (gg | gn)
    extra = (gg | gn) - nc                   # 预期 = 仅属直查表的上游名(非 NameC 覆盖范围)
    print(f'  gender_name  {n_gn:>10,} 键')
    print(f'  gender_guess {n_gg:>10,} 键')
    print(f'  NameC全集    {n_nc:>10,} 键')
    print(f'  交集             {len(inter):>7,}  ← 必须 0')
    print(f'  NameC 覆盖缺口   {len(gap):>7,}  ← 必须 0')
    print(f'  两表并集−NameC   {len(extra):>7,}  （预期=仅属直查表的上游名, 非缺口）')
    print(f'  sha256 gender_guess {sha256(OUT)}')
    print(f'  sha256 gender_name  {sha256(GENDER_NAME)}')
    if os.path.isfile(UY):
        with open(UY, encoding='utf-8-sig', newline='') as f:
            r = csv.reader(f)
            next(r)
            uy = [row for row in r if row]
        print(f'  unihan_year     {len(uy):>10,} 行 / {len({x[0] for x in uy}):,} 字'
              f'  sha256 {sha256(UY)}')
    else:
        print('  （unihan_year.csv 不在场, 跳过）')
    if inter or gap:
        if inter:
            print(f'✗ 关系自证失败: 两表重叠 {len(inter):,} 个键（直查/回退口径互相覆盖）')
        if gap:
            print(f'✗ 关系自证失败: NameC 有 {len(gap):,} 个键两张性别表都查不到 → 对端 s12 静默兜底 0.5')
        print('  先补齐数据再交付；勿在关系不成立时通知对端验收。')
        return False
    print('✔ 关系自证通过: gender_guess ∩ gender_name = ∅ 且 (gender_guess ∪ gender_name) ⊇ NameC')
    return True


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
        gender, prob = guess_gender('王' + nc)  # 拼万能姓; 口径出处见模块 docstring
        boy = prob if gender == '男' else 1 - prob
        w.writerow([nc, f'{boy:.4f}'])
        n_fallback += 1
        if n_fallback % 500000 == 0:
            print(f'  {n_fallback:,} ({(time.time()-t0)/60:.1f}分)', flush=True)
os.replace(OUT + '.tmp', OUT)
print(f'✔ 完成: NameC全集 {n:,}, 回退导出 {n_fallback:,} → {OUT} ({(time.time()-t0)/60:.1f}分)')

# 收尾：关系自证（对端 s12 的零缺失保证依赖它；不成立即非零退出，避免静默坏件交付）
sys.exit(0 if self_prove() else 1)
