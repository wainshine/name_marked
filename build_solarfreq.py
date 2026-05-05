#!/usr/bin/env python3
"""构建 solarfreq.csv — 人名级别二十四节气频率表"""
import os
from utils import given_name

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VALID_DATA = os.path.join(BASE_DIR, 'data', 'train', '有效数据.txt')

if not os.path.exists(VALID_DATA):
    print(f"错误: 有效数据文件不存在: {VALID_DATA}")
    print("请确认 data/train/有效数据.txt 文件存在")
    exit(1)
OUTPUT_FILE = os.path.join(BASE_DIR, 'tables', 'solarfreq.csv')

SOLAR_TERMS = [
    '小寒','大寒','立春','雨水','惊蛰','春分',
    '清明','谷雨','立夏','小满','芒种','夏至',
    '小暑','大暑','立秋','处暑','白露','秋分',
    '寒露','霜降','立冬','小雪','大雪','冬至',
]
SOLAR_RANGES = [
    ((1,6),(1,19)),((1,20),(2,3)),((2,4),(2,18)),((2,19),(3,5)),
    ((3,6),(3,20)),((3,21),(4,4)),((4,5),(4,19)),((4,20),(5,5)),
    ((5,6),(5,20)),((5,21),(6,5)),((6,6),(6,21)),((6,22),(7,6)),
    ((7,7),(7,22)),((7,23),(8,6)),((8,7),(8,22)),((8,23),(9,7)),
    ((9,8),(9,22)),((9,23),(10,7)),((10,8),(10,22)),((10,23),(11,6)),
    ((11,7),(11,21)),((11,22),(12,6)),((12,7),(12,21)),((12,22),(1,5)),
]
MIN_FREQ = 10


def get_solar(id_str):
    if len(id_str) < 14: return None
    m = int(id_str[10:12]); d = int(id_str[12:14]); md = (m, d)
    for i, ((sm, sd), (em, ed)) in enumerate(SOLAR_RANGES):
        if sm == 12 and em == 1:
            if md >= (sm, sd) or md <= (em, ed): return SOLAR_TERMS[i]
        elif (sm, sd) <= md <= (em, ed):
            return SOLAR_TERMS[i]
    return None


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
            st = get_solar(p[1])
            if not st: continue
            if gn not in counts:
                counts[gn] = {x: 0 for x in SOLAR_TERMS}
            counts[gn][st] += 1
            if total % 5000000 == 0:
                print(f'  已处理 {total//10000}W...')

    print(f'  总计: {total}')
    filtered = {gn: c for gn, c in counts.items() if sum(c.values()) >= MIN_FREQ}
    print(f'  总人名: {len(counts)}, >=10次: {len(filtered)}')

    header = 'given_name,' + ','.join(SOLAR_TERMS)
    lines = [header]
    for gn in sorted(filtered.keys()):
        row = [str(filtered[gn][st]) for st in SOLAR_TERMS]
        lines.append(f'{gn},{",".join(row)}')

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'输出: {OUTPUT_FILE}, 条目数: {len(filtered)}')


if __name__ == '__main__':
    main()
