#!/usr/bin/env python3
"""
评估脚本 — 在 holdout 集上评估各模型准确率/覆盖率

用法:
  python scripts/evaluate.py                    # 评估全部 holdout
  python scripts/evaluate.py --limit 100000     # 限制样本数
"""
import os, sys, argparse, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOLDOUT_FILE = os.path.join(BASE_DIR, 'data', 'holdout.txt')

DECADE_CLASSES = ['1950s前', '1960s', '1970s', '1980s', '1990s', '2000s']
ZODIACS = ['摩羯座', '水瓶座', '双鱼座', '白羊座', '金牛座', '双子座',
           '巨蟹座', '狮子座', '处女座', '天秤座', '天蝎座', '射手座']
SEASONS = ['春', '夏', '秋', '冬']
SOLAR_TERMS = [
    '小寒', '大寒', '立春', '雨水', '惊蛰', '春分',
    '清明', '谷雨', '立夏', '小满', '芒种', '夏至',
    '小暑', '大暑', '立秋', '处暑', '白露', '秋分',
    '寒露', '霜降', '立冬', '小雪', '大雪', '冬至',
]
SOLAR_RANGES = [
    ((1, 6), (1, 19)), ((1, 20), (2, 3)), ((2, 4), (2, 18)), ((2, 19), (3, 5)),
    ((3, 6), (3, 20)), ((3, 21), (4, 4)), ((4, 5), (4, 19)), ((4, 20), (5, 5)),
    ((5, 6), (5, 20)), ((5, 21), (6, 5)), ((6, 6), (6, 21)), ((6, 22), (7, 6)),
    ((7, 7), (7, 22)), ((7, 23), (8, 6)), ((8, 7), (8, 22)), ((8, 23), (9, 7)),
    ((9, 8), (9, 22)), ((9, 23), (10, 7)), ((10, 8), (10, 22)), ((10, 23), (11, 6)),
    ((11, 7), (11, 21)), ((11, 22), (12, 6)), ((12, 7), (12, 21)), ((12, 22), (1, 5)),
]


def true_labels(id_str):
    if len(id_str) < 17:
        return None
    try:
        year = int(id_str[6:10]); month = int(id_str[10:12]); day = int(id_str[12:14])
    except ValueError:
        return None
    if not (1930 <= year <= 2020 and 1 <= month <= 12 and 1 <= day <= 31):
        return None
    gender = '男' if int(id_str[16]) % 2 == 1 else '女'
    if year < 1960:
        decade = DECADE_CLASSES[0]
    elif year >= 2000:
        decade = DECADE_CLASSES[5]
    else:
        decade = DECADE_CLASSES[(year - 1960) // 10 + 1]
    md = (month, day)
    if md >= (12, 22) or md <= (1, 19):
        zodiac = ZODIACS[0]
    else:
        zodiac = ZODIACS[-1]
        for i, b in enumerate([(2, 18), (3, 20), (4, 19), (5, 20), (6, 21),
                               (7, 22), (8, 22), (9, 22), (10, 23), (11, 22)]):
            if md <= b:
                zodiac = ZODIACS[i + 1]
                break
    season = SEASONS[0] if 3 <= month <= 5 else SEASONS[1] if 6 <= month <= 8 \
        else SEASONS[2] if 9 <= month <= 11 else SEASONS[3]
    solar = None
    for i, ((sm, sd), (em, ed)) in enumerate(SOLAR_RANGES):
        if sm == 12 and em == 1:
            if md >= (sm, sd) or md <= (em, ed):
                solar = SOLAR_TERMS[i]
                break
        elif (sm, sd) <= md <= (em, ed):
            solar = SOLAR_TERMS[i]
            break
    return {'gender': gender, 'decade': decade, 'zodiac': zodiac,
            'season': season, 'solar': solar}


def load_engine():
    from namecore import guess_gender, guess_decade, guess_zodiac, guess_season, guess_solar
    return {'gender': guess_gender, 'decade': guess_decade, 'zodiac': guess_zodiac,
            'season': guess_season, 'solar': guess_solar}


def evaluate(limit=0):
    engine = load_engine()
    if not os.path.isfile(HOLDOUT_FILE):
        print(f'错误: 评估集不存在: {HOLDOUT_FILE}')
        print('按敏感数据处置规则，holdout 不常驻本机。')
        print('请先重训生成: python scripts/train.py --input <有效数据.txt>，评估完成后删除。')
        sys.exit(1)
    stats = {m: {'n': 0, 'hit': 0, 'unknown': 0, 'near': 0} for m in engine}
    t0 = time.time()
    n = 0
    with open(HOLDOUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if limit and n >= limit:
                break
            p = line.rstrip('\n').split(',')
            if len(p) < 2:
                continue
            truth = true_labels(p[1].strip())
            if not truth:
                continue
            n += 1
            name = p[0]
            for m, func in engine.items():
                pred = func(name)[0]
                s = stats[m]
                s['n'] += 1
                if pred == '未知':
                    s['unknown'] += 1
                elif pred == truth[m]:
                    s['hit'] += 1
                    s['near'] += 1
                elif m == 'decade':
                    if abs(DECADE_CLASSES.index(pred) - DECADE_CLASSES.index(truth[m])) == 1:
                        s['near'] += 1
    rows = []
    for m, s in stats.items():
        n_m = max(1, s['n'])
        rows.append({
            'model': m,
            'acc': s['hit'] / n_m,
            'near': s['near'] / n_m,
            'coverage': 1.0 - s['unknown'] / n_m,
        })
    return rows, n, time.time() - t0


def main():
    ap = argparse.ArgumentParser(description='holdout 评估')
    ap.add_argument('--limit', type=int, default=0, help='限制样本数 (0=全部)')
    args = ap.parse_args()

    print('评估 holdout ...')
    rows, n, elapsed = evaluate(args.limit)
    print(f'  样本 {n:,}, 耗时 {elapsed:.0f}s')

    print(f'\n{"模型":<8} {"准确率":>8} {"±1准确率":>8} {"覆盖率":>8}')
    for r in rows:
        print(f'{r["model"]:<8} {r["acc"]:>8.2%} {r["near"]:>8.2%} {r["coverage"]:>8.2%}')


if __name__ == '__main__':
    main()
