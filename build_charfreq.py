#!/usr/bin/env python3
"""构建 charfreq.csv — 位置感知性别频率表"""
import os
from utils import given_name, pos_keys, load_std_chars

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VALID_DATA = os.path.join(BASE_DIR, 'data', 'train', '有效数据.txt')

if not os.path.exists(VALID_DATA):
    print(f"错误: 有效数据文件不存在: {VALID_DATA}")
    print("请确认 data/train/有效数据.txt 文件存在")
    exit(1)
CHAR_TABLE_FILE = os.path.join(BASE_DIR, 'data', 'ref', '《通用规范汉字表》（2013年）.txt')
OUTPUT_FILE = os.path.join(BASE_DIR, 'tables', 'charfreq.csv')

MIN_FREQ = 10
DEFAULT_FREQ = 5


def get_gender_from_id(id_str):
    if len(id_str) < 17: return None
    return '男' if int(id_str[16]) % 2 == 1 else '女'


def main():
    print('加载标准汉字表...')
    std_chars = load_std_chars(CHAR_TABLE_FILE)
    print(f'  标准汉字: {len(std_chars)}')

    male_counts, female_counts = {}, {}
    total = 0
    with open(VALID_DATA, 'r', encoding='gbk', errors='replace') as f:
        for line in f:
            total += 1
            p = line.strip().split(',')
            if len(p) < 2: continue
            name, id_str = p[0], p[1]
            gender = get_gender_from_id(id_str)
            if not gender: continue
            gn = given_name(name)
            if not gn: continue
            target = male_counts if gender == '男' else female_counts
            for k in pos_keys(gn):
                target[k] = target.get(k, 0) + 1
            if total % 5000000 == 0:
                print(f'  已处理 {total//10000}W...')

    print(f'  总计: {total}')

    all_keys = set(male_counts.keys()) | set(female_counts.keys())
    for pos in ['p0', 'p1', 'p2', 'p3']:
        for c in std_chars:
            all_keys.add(f'{c}_{pos}')

    lines = ['char_pos,female,male']
    for k in sorted(all_keys):
        f_c = female_counts.get(k, 0)
        m_c = male_counts.get(k, 0)
        if f_c + m_c < MIN_FREQ:
            f_c = m_c = DEFAULT_FREQ
        lines.append(f'{k},{f_c},{m_c}')

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    print(f'\n输出: {OUTPUT_FILE}')
    data_keys = set(male_counts.keys()) | set(female_counts.keys())
    print(f'  数据中条目: {len(data_keys)}, 输出总条目: {len(all_keys)}')


if __name__ == '__main__':
    main()
