#!/usr/bin/env python3
"""构建 decadefreq.csv — 位置感知年代频率表（含2000s插值）"""
import os, subprocess, shutil
from utils import given_name, pos_keys, load_std_chars

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VALID_DATA = os.path.join(BASE_DIR, 'data', 'train', '有效数据.txt')

if not os.path.exists(VALID_DATA):
    print(f"错误: 有效数据文件不存在: {VALID_DATA}")
    print("请确认 data/train/有效数据.txt 文件存在")
    exit(1)
CHAR_TABLE_FILE = os.path.join(BASE_DIR, 'data', 'ref', '《通用规范汉字表》（2013年）.txt')
OUTPUT_FILE = os.path.join(BASE_DIR, 'tables', 'decadefreq.csv')

CN_URL = 'https://raw.githubusercontent.com/psychbruce/ChineseNames/main/data-csv/givenname.csv'
CN_CACHE = os.path.join(BASE_DIR, 'data', 'ref', '.cache_givenname.csv')

DECADE_CLASSES = ['1950s前', '1960s', '1970s', '1980s', '1990s', '2000s']
MIN_FREQ, DEFAULT_FREQ = 10, 5


def _download_cn():
    if os.path.exists(CN_CACHE):
        return CN_CACHE

    # Try multiple sources
    urls = [CN_URL]
    tmp = '/tmp/givenname.csv'
    if os.path.exists(tmp):
        urls.insert(0, 'file://' + tmp)

    for url in urls:
        try:
            print(f'下载 ChineseNames: {url}')
            if url.startswith('file://'):
                shutil.copy(url[7:], CN_CACHE)
            else:
                subprocess.run(['curl', '-sL', '--insecure', '-o', CN_CACHE, url],
                             check=True, timeout=30)
            if os.path.getsize(CN_CACHE) > 1000:
                return CN_CACHE
        except Exception as e:
            print(f'  失败: {e}')

    raise RuntimeError('无法获取 ChineseNames 数据，请手动下载到 ' + CN_CACHE)


def load_cn_ratios(filepath):
    ratios = {}
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        next(f)
        for line in f:
            parts = line.strip().split(',')
            ch = parts[0]
            n90 = int(parts[10])
            n00 = int(parts[11])
            if n90 > 0 and n00 > 0:
                ratios[ch] = n00 / n90
    return ratios


def get_decade_class(id_str):
    if len(id_str) < 14: return None
    y = int(id_str[6:10])
    if 1930 <= y <= 1959: return '1950s前'
    elif y <= 1969: return '1960s'
    elif y <= 1979: return '1970s'
    elif y <= 1989: return '1980s'
    elif y <= 1999: return '1990s'
    return None


def main():
    print('加载标准汉字表...')
    std_chars = load_std_chars(CHAR_TABLE_FILE)
    print(f'  标准汉字: {len(std_chars)}')

    cn_path = _download_cn()
    cn_ratios = load_cn_ratios(cn_path)
    global_ratio = sum(cn_ratios.values()) / len(cn_ratios) if cn_ratios else 0.7
    print(f'  ChineseNames 有效字符: {len(cn_ratios)}, 平均比值(00s/90s): {global_ratio:.4f}')

    counts = {}
    total = 0
    with open(VALID_DATA, 'r', encoding='gbk', errors='replace') as f:
        for line in f:
            total += 1
            p = line.strip().split(',')
            if len(p) < 2: continue
            name, id_str = p[0], p[1]
            dc = get_decade_class(id_str)
            if not dc: continue
            gn = given_name(name)
            if not gn: continue
            for k in pos_keys(gn):
                if k not in counts:
                    counts[k] = {d: 0 for d in DECADE_CLASSES}
                counts[k][dc] += 1
            if total % 5000000 == 0:
                print(f'  已处理 {total//10000}W...')

    print(f'  自有数据总计: {total}')

    TIME_FACTOR = 10.0 / 9.0
    print(f'插值 2000s 数据（时间跨度修正 ×{TIME_FACTOR:.3f}）...')
    for k in list(counts.keys()):
        ch = k.split('_')[0]
        cnt_90s = counts[k]['1990s']
        if cnt_90s > 0:
            ratio = cn_ratios.get(ch, global_ratio)
            counts[k]['2000s'] = max(1, int(cnt_90s * ratio * TIME_FACTOR))
        else:
            avg = sum(counts[k][d] for d in ['1980s', '1990s']) / 2
            counts[k]['2000s'] = max(1, int(avg * global_ratio * 0.5 * TIME_FACTOR))

    all_keys = set(counts.keys())
    for pos in ['p0', 'p1', 'p2', 'p3']:
        for c in std_chars:
            all_keys.add(f'{c}_{pos}')

    header = 'char_pos,' + ','.join(DECADE_CLASSES)
    lines = [header]
    for k in sorted(all_keys):
        c = counts.get(k, {})
        t = sum(c.values()) if c else 0
        if t < MIN_FREQ:
            row = [str(DEFAULT_FREQ)] * len(DECADE_CLASSES)
        else:
            row = [str(c.get(d, DEFAULT_FREQ)) for d in DECADE_CLASSES]
        lines.append(f'{k},{",".join(row)}')

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    data_keys = set(counts.keys())
    total_00s = sum(counts[k]['2000s'] for k in data_keys)
    total_90s = sum(counts[k]['1990s'] for k in data_keys)
    print(f'\n输出: {OUTPUT_FILE}')
    print(f'  数据条目: {len(data_keys)}, 输出总条目: {len(all_keys)}')
    print(f'  1990s总频: {total_90s:,}, 2000s总频(插值): {total_00s:,}')


if __name__ == '__main__':
    main()
