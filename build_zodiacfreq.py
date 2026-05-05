#!/usr/bin/env python3
"""构建 zodiacfreq.csv — 人名级别星座频率表"""
import os
from utils import given_name

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VALID_DATA = os.path.join(BASE_DIR, 'data', 'train', '有效数据.txt')

if not os.path.exists(VALID_DATA):
    print(f"错误: 有效数据文件不存在: {VALID_DATA}")
    print("请确认 data/train/有效数据.txt 文件存在")
    exit(1)
OUTPUT_FILE = os.path.join(BASE_DIR, 'tables', 'zodiacfreq.csv')

ZODIACS = ['摩羯座','水瓶座','双鱼座','白羊座','金牛座','双子座',
           '巨蟹座','狮子座','处女座','天秤座','天蝎座','射手座']
MIN_FREQ = 10


def get_zodiac(id_str):
    if len(id_str) < 14: return None
    m = int(id_str[10:12]); d = int(id_str[12:14]); md = (m, d)
    if md >= (12, 22) or md <= (1, 19): return '摩羯座'
    elif md <= (2, 18): return '水瓶座'
    elif md <= (3, 20): return '双鱼座'
    elif md <= (4, 19): return '白羊座'
    elif md <= (5, 20): return '金牛座'
    elif md <= (6, 21): return '双子座'
    elif md <= (7, 22): return '巨蟹座'
    elif md <= (8, 22): return '狮子座'
    elif md <= (9, 22): return '处女座'
    elif md <= (10, 23): return '天秤座'
    elif md <= (11, 22): return '天蝎座'
    return '射手座'


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
            z = get_zodiac(p[1])
            if not z: continue
            if gn not in counts:
                counts[gn] = {x: 0 for x in ZODIACS}
            counts[gn][z] += 1
            if total % 5000000 == 0:
                print(f'  已处理 {total//10000}W...')

    print(f'  总计: {total}')
    filtered = {gn: c for gn, c in counts.items() if sum(c.values()) >= MIN_FREQ}
    print(f'  总人名: {len(counts)}, >=10次: {len(filtered)}')

    header = 'given_name,' + ','.join(ZODIACS)
    lines = [header]
    for gn in sorted(filtered.keys()):
        row = [str(filtered[gn][z]) for z in ZODIACS]
        lines.append(f'{gn},{",".join(row)}')

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'输出: {OUTPUT_FILE}, 条目数: {len(filtered)}')


if __name__ == '__main__':
    main()
