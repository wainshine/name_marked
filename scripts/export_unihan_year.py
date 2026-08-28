#!/usr/bin/env python3
"""
导出 unihan_year.csv — 字级年代分布表（供 NameMoe UniHan_Year 真数据）

读 namecore/tables/decade_char.csv（字×位置×年代），跨位置(p0~p3)按字求和，
每字每十年一行。格式冻结：
  表头: UniHan,Year,TF
  编码: utf-8-sig
  排序: 字(Unicode升序) → 字内年代升序
  年代: 1950s前→1950-01-01, 1960s→1960-01-01, ..., 2000s→2000-01-01
注意: 2000s 列为插值估计（ChineseNames 字频外推），非真实样本计数。

用法: python scripts/export_unihan_year.py
"""
import os, sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES_DIR = os.path.join(BASE_DIR, 'namecore', 'tables')
INPUT = os.path.join(TABLES_DIR, 'decade_char.csv')
OUTPUT = os.path.join(TABLES_DIR, 'unihan_year.csv')

DECADE_CLASSES = ['1950s前', '1960s', '1970s', '1980s', '1990s', '2000s']
YEARS = ['1950-01-01', '1960-01-01', '1970-01-01',
         '1980-01-01', '1990-01-01', '2000-01-01']


def main():
    if not os.path.isfile(INPUT):
        print(f'错误: {INPUT} 不存在，请先运行 scripts/train.py')
        sys.exit(1)

    char_counts = {}
    with open(INPUT, 'r', encoding='utf-8') as f:
        header = next(f).strip().split(',')
        if header[1:] != DECADE_CLASSES:
            print(f'错误: 年代列不符: {header[1:]}')
            sys.exit(1)
        for line in f:
            parts = line.rstrip('\n').split(',')
            if len(parts) < 7:
                continue
            ch = parts[0].rsplit('_', 1)[0]
            row = char_counts.get(ch)
            if row is None:
                row = char_counts[ch] = [0] * 6
            for i in range(6):
                row[i] += int(parts[i + 1])

    lines = ['UniHan,Year,TF']
    for ch in sorted(char_counts):
        row = char_counts[ch]
        for i in range(6):
            lines.append(f'{ch},{YEARS[i]},{row[i]}')

    with open(OUTPUT, 'w', encoding='utf-8-sig') as f:
        f.write('\n'.join(lines) + '\n')

    print(f'输出: {OUTPUT}')
    print(f'  字数: {len(char_counts):,}, 行数: {len(lines) - 1:,}')


if __name__ == '__main__':
    main()
