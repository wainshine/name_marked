#!/usr/bin/env python3
"""构建 seasonfreq.csv — 人名级别四季频率表"""
import os
from utils import given_name

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VALID_DATA = os.path.join(BASE_DIR, 'data', 'train', '有效数据.txt')

if not os.path.exists(VALID_DATA):
    print(f"错误: 有效数据文件不存在: {VALID_DATA}")
    print("请确认 data/train/有效数据.txt 文件存在")
    exit(1)
OUTPUT_FILE = os.path.join(BASE_DIR, 'tables', 'seasonfreq.csv')

SEASONS = ['春', '夏', '秋', '冬']
MIN_FREQ = 10


def get_season(id_str):
    if len(id_str) < 14: return None
    m = int(id_str[10:12])
    if 3 <= m <= 5: return '春'
    if 6 <= m <= 8: return '夏'
    if 9 <= m <= 11: return '秋'
    return '冬'


def main():
    counts = {}
    total = 0
    with open(VALID_DATA, 'r', encoding='gbk', errors='replace') as f:
        for line in f:
            total += 1
            p = line.strip().split(',')
            if len(p) < 2: continue
            gn = given_name(p[0])
            if not gn: continue
            s = get_season(p[1])
            if not s: continue
            if gn not in counts:
                counts[gn] = {x: 0 for x in SEASONS}
            counts[gn][s] += 1
            if total % 5000000 == 0:
                print(f'  已处理 {total//10000}W...')

    print(f'  总计: {total}')
    filtered = {gn: c for gn, c in counts.items() if sum(c.values()) >= MIN_FREQ}
    print(f'  总人名: {len(counts)}, >=10次: {len(filtered)}')

    header = 'given_name,' + ','.join(SEASONS)
    lines = [header]
    for gn in sorted(filtered.keys()):
        row = [str(filtered[gn][s]) for s in SEASONS]
        lines.append(f'{gn},{",".join(row)}')

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'输出: {OUTPUT_FILE}, 条目数: {len(filtered)}')


if __name__ == '__main__':
    main()
