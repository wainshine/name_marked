#!/usr/bin/env python3
"""
统一训练管线 — 单次扫描训练数据，生成全部 10 张频率表

两遍扫描:
  pass1: 数据QA + 字符级计数(5模型) + 人名总频次 + holdout切分
  pass2: 人名级计数(5模型, 仅频次>=MIN_NAME_FREQ的人名)

用法:
  python scripts/train.py --input /path/有效数据.txt
  python scripts/train.py --input /path/有效数据.txt --holdout 0.1 --min-name-freq 10
"""
import os, sys, json, zlib, argparse, subprocess, random, time
from array import array
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from namecore.utils import given_name, pos_keys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES_DIR = os.path.join(BASE_DIR, 'namecore', 'tables')
HOLDOUT_FILE = os.path.join(BASE_DIR, 'data', 'holdout.txt')
STATS_FILE = os.path.join(BASE_DIR, 'data', 'train_stats.json')
CN_CACHE = os.path.join(BASE_DIR, 'data', 'ref', '.cache_givenname.csv')
CN_URL = 'https://raw.githubusercontent.com/psychbruce/ChineseNames/main/data-csv/givenname.csv'

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
ZODIAC_IDX = {z: i for i, z in enumerate(ZODIACS)}
SEASON_IDX = {s: i for i, s in enumerate(SEASONS)}
SOLAR_IDX = {s: i for i, s in enumerate(SOLAR_TERMS)}
DECADE_IDX = {d: i for i, d in enumerate(DECADE_CLASSES)}


def parse_id(id_str):
    """返回 (gender, year, month, day)，非法返回 None"""
    n = len(id_str)
    if n < 17:
        return None
    try:
        year = int(id_str[6:10])
        month = int(id_str[10:12])
        day = int(id_str[12:14])
    except ValueError:
        return None
    if not (1930 <= year <= 2020 and 1 <= month <= 12 and 1 <= day <= 31):
        return None
    gender = 'male' if int(id_str[16]) % 2 == 1 else 'female'
    return gender, year, month, day


def decade_of(year):
    if year < 1960:
        return 0
    if year >= 2000:
        return 5
    return (year - 1960) // 10 + 1


def zodiac_of(month, day):
    md = (month, day)
    if md >= (12, 22) or md <= (1, 19):
        return 0
    bounds = [(2, 18), (3, 20), (4, 19), (5, 20), (6, 21), (7, 22),
              (8, 22), (9, 22), (10, 23), (11, 22)]
    for i, b in enumerate(bounds):
        if md <= b:
            return i + 1
    return 11


def season_of(month):
    if 3 <= month <= 5:
        return 0
    if 6 <= month <= 8:
        return 1
    if 9 <= month <= 11:
        return 2
    return 3


def solar_of(month, day):
    md = (month, day)
    for i, ((sm, sd), (em, ed)) in enumerate(SOLAR_RANGES):
        if sm == 12 and em == 1:
            if md >= (sm, sd) or md <= (em, ed):
                return i
        elif (sm, sd) <= md <= (em, ed):
            return i
    return -1


def _download_cn():
    if os.path.exists(CN_CACHE) and os.path.getsize(CN_CACHE) > 1000:
        return CN_CACHE
    try:
        print(f'下载 ChineseNames: {CN_URL}')
        subprocess.run(['curl', '-sL', '--insecure', '-o', CN_CACHE, CN_URL],
                       check=True, timeout=60)
        if os.path.getsize(CN_CACHE) > 1000:
            return CN_CACHE
    except Exception as e:
        print(f'  下载失败: {e}')
    return None


def load_cn_ratios():
    """ChineseNames 字频比值 r = 2000s/1990s（用于2000s插值）"""
    path = _download_cn()
    ratios = {}
    if path:
        with open(path, 'r', encoding='utf-8-sig') as f:
            next(f)
            for line in f:
                parts = line.strip().split(',')
                if len(parts) < 12:
                    continue
                try:
                    n90, n00 = int(parts[10]), int(parts[11])
                except ValueError:
                    continue
                if n90 > 0 and n00 > 0:
                    ratios[parts[0]] = n00 / n90
    global_ratio = sum(ratios.values()) / len(ratios) if ratios else 0.7
    return ratios, global_ratio


class CountTable:
    """key -> array('i') 计数表"""
    def __init__(self, nclass):
        self.nclass = nclass
        self.d = {}

    def bump(self, key, idx):
        row = self.d.get(key)
        if row is None:
            row = array('i', bytes(4 * self.nclass))
            self.d[key] = row
        row[idx] += 1

    def write(self, path, header):
        lines = [header]
        for k in sorted(self.d.keys()):
            lines.append(k + ',' + ','.join(str(x) for x in self.d[k]))
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        return len(self.d)


def main():
    ap = argparse.ArgumentParser(description='name_marked 统一训练管线')
    ap.add_argument('--input', default=os.path.join(BASE_DIR, 'data', 'train', '有效数据.txt'))
    ap.add_argument('--holdout', type=float, default=0.1, help='holdout 比例 (默认 0.1)')
    ap.add_argument('--min-name-freq', type=int, default=10, help='人名级表最低频次 (默认 10)')
    ap.add_argument('--encoding', default='gbk')
    args = ap.parse_args()

    inpath = args.input
    if not os.path.isfile(inpath):
        print(f'错误: 训练数据不存在: {inpath}')
        sys.exit(1)

    os.makedirs(TABLES_DIR, exist_ok=True)
    t0 = time.time()
    holdout_mod = int(args.holdout * 100)

    # ---------- pass 1 ----------
    print(f'[pass1] 扫描 {inpath} ...')
    gender_char = CountTable(2)   # [female, male]
    decade_char = CountTable(6)
    zodiac_char = CountTable(12)
    season_char = CountTable(4)
    solar_char = CountTable(24)
    name_total = Counter()

    total = 0
    bad_id = 0
    no_name = 0
    holdout_n = 0
    holdout_rows = []
    gender_tot = [0, 0]
    decade_tot = [0] * 6
    id_len_dist = Counter()

    with open(inpath, 'r', encoding=args.encoding, errors='replace') as fin:
        for line in fin:
            total += 1
            p = line.split(',')
            if len(p) < 2:
                bad_id += 1
                continue
            name = p[0]
            id_str = p[1].strip()
            id_len_dist[len(id_str)] += 1
            parsed = parse_id(id_str)
            if not parsed:
                bad_id += 1
                continue
            gn = given_name(name)
            if not gn or len(gn) > 3:
                no_name += 1
                continue
            if zlib.crc32(name.encode('utf-8')) % 100 < holdout_mod:
                holdout_n += 1
                holdout_rows.append(f'{name},{id_str}\n')
                continue
            gender, year, month, day = parsed
            gi = 1 if gender == 'male' else 0
            di = decade_of(year)
            zi = zodiac_of(month, day)
            si = season_of(month)
            li = solar_of(month, day)
            gender_tot[gi] += 1
            decade_tot[di] += 1
            name_total[gn] += 1
            for k in pos_keys(gn):
                gender_char.bump(k, gi)
                decade_char.bump(k, di)
                zodiac_char.bump(k, zi)
                season_char.bump(k, si)
                if li >= 0:
                    solar_char.bump(k, li)
            if total % 5000000 == 0:
                print(f'  {total // 10000}W 行 ({time.time() - t0:.0f}s)')

    # holdout 洗牌后落盘（输入按编码前缀有序，不洗牌则 --limit 小样本评估有偏）
    random.seed(42)
    random.shuffle(holdout_rows)
    with open(HOLDOUT_FILE, 'w', encoding='utf-8') as fho:
        fho.writelines(holdout_rows)
    del holdout_rows

    train_n = total - bad_id - no_name - holdout_n
    print(f'[pass1] 完成: 总行 {total:,}, 训练 {train_n:,}, holdout {holdout_n:,}, '
          f'非法ID {bad_id:,}, 无名 {no_name:,} ({time.time() - t0:.0f}s)')
    print(f'  唯一人名: {len(name_total):,}, 男性占比: {gender_tot[1] / max(1, sum(gender_tot)):.4f}')
    print(f'  编码长度分布: {dict(sorted(id_len_dist.items()))}')
    print(f'  年代分布: {dict(zip(DECADE_CLASSES, decade_tot))}')

    # ---------- pass 2 ----------
    print(f'[pass2] 人名级计数 (人名频次>={args.min_name_freq}) ...')
    keep = {n for n, c in name_total.items() if c >= args.min_name_freq}
    del name_total
    print(f'  保留人名: {len(keep):,}')

    gender_name = CountTable(2)
    decade_name = CountTable(6)
    zodiac_name = CountTable(12)
    season_name = CountTable(4)
    solar_name = CountTable(24)

    total = 0
    with open(inpath, 'r', encoding=args.encoding, errors='replace') as fin:
        for line in fin:
            total += 1
            p = line.split(',')
            if len(p) < 2:
                continue
            name = p[0]
            id_str = p[1].strip()
            parsed = parse_id(id_str)
            if not parsed:
                continue
            gn = given_name(name)
            if not gn or gn not in keep:
                continue
            if zlib.crc32(name.encode('utf-8')) % 100 < holdout_mod:
                continue
            gender, year, month, day = parsed
            gi = 1 if gender == 'male' else 0
            gender_name.bump(gn, gi)
            decade_name.bump(gn, decade_of(year))
            zodiac_name.bump(gn, zodiac_of(month, day))
            season_name.bump(gn, season_of(month))
            li = solar_of(month, day)
            if li >= 0:
                solar_name.bump(gn, li)
            if total % 5000000 == 0:
                print(f'  {total // 10000}W 行 ({time.time() - t0:.0f}s)')

    print(f'[pass2] 完成 ({time.time() - t0:.0f}s)')

    # ---------- 2000s 插值 ----------
    has_real_2000s = decade_tot[5] > 0
    if has_real_2000s:
        print('  训练数据含2000s真实数据，跳过插值')
    else:
        print('插值 2000s 数据 ...')
        cn_ratios, global_r = load_cn_ratios()
        print(f'  ChineseNames 字比值: {len(cn_ratios)}, 全局均值: {global_r:.4f}')
        TIME_FACTOR = 10.0 / 9.0

        def interp_2000s(row, chars):
            n80, n90 = row[3], row[4]
            if n90 > 0:
                rs = [cn_ratios[c] for c in chars if c in cn_ratios]
                if rs:
                    r = 1.0
                    for x in rs:
                        r *= x
                    r = r ** (1.0 / len(rs))
                elif n80 > 0:
                    r = min(3.0, max(0.3, n90 / n80))
                else:
                    r = global_r
                row[5] = max(1, int(n90 * r * TIME_FACTOR))
            elif n80 > 0:
                row[5] = max(1, int(n80 * global_r * 0.5 * TIME_FACTOR))

        for k, row in decade_char.d.items():
            interp_2000s(row, [k.rsplit('_', 1)[0]])
        for gn, row in decade_name.d.items():
            interp_2000s(row, list(gn))

    # ---------- 写表 ----------
    print('写频率表 ...')
    written = {}
    written['gender_char'] = gender_char.write(
        os.path.join(TABLES_DIR, 'gender_char.csv'), 'char_pos,female,male')
    written['gender_name'] = gender_name.write(
        os.path.join(TABLES_DIR, 'gender_name.csv'), 'given_name,female,male')
    hdr = 'char_pos,' + ','.join(DECADE_CLASSES)
    written['decade_char'] = decade_char.write(os.path.join(TABLES_DIR, 'decade_char.csv'), hdr)
    hdr = 'given_name,' + ','.join(DECADE_CLASSES)
    written['decade_name'] = decade_name.write(os.path.join(TABLES_DIR, 'decade_name.csv'), hdr)
    hdr = 'char_pos,' + ','.join(ZODIACS)
    written['zodiac_char'] = zodiac_char.write(os.path.join(TABLES_DIR, 'zodiac_char.csv'), hdr)
    hdr = 'given_name,' + ','.join(ZODIACS)
    written['zodiac_name'] = zodiac_name.write(os.path.join(TABLES_DIR, 'zodiac_name.csv'), hdr)
    hdr = 'char_pos,' + ','.join(SEASONS)
    written['season_char'] = season_char.write(os.path.join(TABLES_DIR, 'season_char.csv'), hdr)
    hdr = 'given_name,' + ','.join(SEASONS)
    written['season_name'] = season_name.write(os.path.join(TABLES_DIR, 'season_name.csv'), hdr)
    hdr = 'char_pos,' + ','.join(SOLAR_TERMS)
    written['solar_char'] = solar_char.write(os.path.join(TABLES_DIR, 'solar_char.csv'), hdr)
    hdr = 'given_name,' + ','.join(SOLAR_TERMS)
    written['solar_name'] = solar_name.write(os.path.join(TABLES_DIR, 'solar_name.csv'), hdr)

    stats = {
        'input': os.path.basename(inpath),
        'total_lines': total,
        'train_rows': train_n,
        'holdout_rows': holdout_n,
        'bad_id_rows': bad_id,
        'no_name_rows': no_name,
        'unique_given_names': len(keep),
        'male_ratio': gender_tot[1] / max(1, sum(gender_tot)),
        'decade_distribution': dict(zip(DECADE_CLASSES, decade_tot)),
        'has_real_2000s': has_real_2000s,
        'table_rows': written,
        'elapsed_sec': round(time.time() - t0, 1),
    }
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f'\n完成 ({time.time() - t0:.0f}s)')
    for k, v in written.items():
        print(f'  {k}: {v:,} 行')
    print(f'  holdout: {HOLDOUT_FILE} ({holdout_n:,} 行)')
    print(f'  统计: {STATS_FILE}')


if __name__ == '__main__':
    main()
