#!/usr/bin/env python3
"""
锚点自检 — 对核心产物与公开接口的一组只读断言（秒级）

测什么:
  1. 产物存在性: 10 张模型表 pkl + 2 张导出契约 CSV
  2. 契约格式: unihan_year.csv / gender_guess.csv 的编码/表头/排序/取值域
  3. 接口锚点: guess_* 返回形状与典型姓名方向
  4. 一致性: train_stats.json 记录的行数 vs CSV 实际行数

前提: CSV 模型表/契约表不入库（仅 pkl 入库），全新克隆环境 §2/§4 会报产物缺失 FAIL，
属预期——本脚本需在训练机/产物齐备环境运行。

什么算过: 全部断言 PASS，退出码 0；任一 FAIL 退出码 1
用法: python3 tests/anchor_check.py
"""
import os, sys, json, csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES = os.path.join(BASE_DIR, 'namecore', 'tables')

_pass = _fail = 0


def check(name, cond, detail=''):
    global _pass, _fail
    if cond:
        _pass += 1
        print(f'  PASS {name}')
    else:
        _fail += 1
        print(f'  FAIL {name}  {detail}')


def count_lines(path):
    with open(path, 'rb') as f:
        return sum(1 for _ in f)


def missing_hint(path):
    return (f'{path} 不存在。模型/契约 CSV 不入库（仅 pkl 入库），'
            f'全新克隆环境无 CSV 属预期；锚点自检需在训练机/产物齐备环境运行')


def main():
    print('== 1. 产物存在性 ==')
    models = ['gender', 'decade', 'zodiac', 'season', 'solar']
    for m in models:
        for tier in ['char', 'name']:
            p = os.path.join(TABLES, f'{m}_{tier}.csv.pkl')
            check(f'pkl {m}_{tier}', os.path.isfile(p) and os.path.getsize(p) > 1000)
    for f in ['unihan_year.csv', 'gender_guess.csv']:
        p = os.path.join(TABLES, f)
        check(f'契约 {f}', os.path.isfile(p) and os.path.getsize(p) > 1000)

    print('== 2. 契约格式 ==')
    uy = os.path.join(TABLES, 'unihan_year.csv')
    if not os.path.isfile(uy):
        check('unihan_year.csv 在场', False, missing_hint(uy))
    else:
        with open(uy, 'rb') as f:
            check('unihan_year utf-8-sig', f.read(3) == b'\xef\xbb\xbf')
        with open(uy, encoding='utf-8-sig') as f:
            r = csv.reader(f)
            check('unihan_year 表头', next(r) == ['UniHan', 'Year', 'TF'])
            rows = list(r)
        check('unihan_year 行数%6==0', len(rows) % 6 == 0, f'{len(rows)}')
        check('unihan_year 字内年代升序',
              all(rows[i][1] <= rows[i + 1][1] for i in range(0, len(rows) - 1) if rows[i][0] == rows[i + 1][0]))
        anchor = {row[1]: row[2] for row in rows if row[0] == '一'}
        check('unihan_year 锚点 一', anchor.get('1950-01-01') == '4479' and anchor.get('1980-01-01') == '24243',
              str(anchor))

    gg = os.path.join(TABLES, 'gender_guess.csv')
    if not os.path.isfile(gg):
        check('gender_guess.csv 在场', False, missing_hint(gg))
    else:
        with open(gg, 'rb') as f:
            check('gender_guess utf-8-sig', f.read(3) == b'\xef\xbb\xbf')
        with open(gg, encoding='utf-8-sig') as f:
            r = csv.reader(f)
            check('gender_guess 表头', next(r) == ['name', 'boy_prob'])
            ok = True
            for i, row in enumerate(r):
                if i >= 100000:
                    break
                try:
                    v = float(row[1])
                    if not (0.0 <= v <= 1.0):
                        ok = False
                        break
                except (ValueError, IndexError):
                    ok = False
                    break
            check('gender_guess 概率∈[0,1] (抽样10万)', ok)
        check('gender_guess 行数>400万', count_lines(gg) > 4000000)

    print('== 3. 接口锚点 ==')
    sys.path.insert(0, BASE_DIR)
    from namecore import guess_gender, guess_decade, guess_zodiac, guess_season, guess_solar

    g, p = guess_gender('王伟')
    check("guess_gender('王伟')→男", g == '男' and p > 0.5, f'{g},{p:.4f}')
    g, p = guess_gender('刘亦菲')
    check("guess_gender('刘亦菲')→女", g == '女' and p > 0.5, f'{g},{p:.4f}')
    g, _ = guess_gender('張偉')
    check("guess_gender('張偉')→男(繁体)", g == '男', g)
    d, p, dist = guess_decade('张宇轩')
    check("guess_decade('张宇轩')→90s/00s", d in ('1990s', '2000s'), d)
    check('guess_decade 分布和≈1', abs(sum(dist.values()) - 1.0) < 1e-6)
    for func, n_cls in [(guess_zodiac, 12), (guess_season, 4), (guess_solar, 24)]:
        label, prob, dist = func('王伟')
        check(f'{func.__module__} 返回(label,prob,dist[{n_cls}])',
              label != '未知' and 0 < prob <= 1 and len(dist) == n_cls,
              f'{label},{prob},{len(dist)}')

    print('== 4. 一致性 ==')
    with open(os.path.join(BASE_DIR, 'data', 'train_stats.json'), encoding='utf-8') as f:
        stats = json.load(f)
    for key, expected in stats['table_rows'].items():
        csv_path = os.path.join(TABLES, f'{key}.csv')
        if not os.path.isfile(csv_path):
            check(f'{key}.csv 在场', False, missing_hint(csv_path))
            continue
        actual = count_lines(csv_path) - 1
        check(f'{key} 行数==stats', actual == expected, f'{actual} vs {expected}')

    print(f'\n结果: {_pass} PASS, {_fail} FAIL')
    sys.exit(1 if _fail else 0)


if __name__ == '__main__':
    main()
