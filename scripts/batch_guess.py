#!/usr/bin/env python3
"""
批处理 CLI — 对文件批量标记姓名属性

用法:
  python scripts/batch_guess.py input.txt                          # 5项全标
  python scripts/batch_guess.py input.txt --models gender,decade   # 指定模型
  python scripts/batch_guess.py input.txt --mode namec             # 输入为名
  python scripts/batch_guess.py input.txt --encoding gbk           # GBK编码
  python scripts/batch_guess.py input.txt --output result.csv      # 指定输出

输入文件首行可声明模式: namea(完整姓名) 或 namec(名), 不区分大小写, 兼容BOM
"""
import os, sys, argparse, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

MODEL_META = [
    ('gender', '性别', '性别概率'),
    ('decade', '年代', '年代概率'),
    ('zodiac', '星座', '星座概率'),
    ('season', '四季', '四季概率'),
    ('solar', '节气', '节气概率'),
]

VALID_MODES = {'namea': 'auto', 'namec': 'namec'}


def load_models(enabled):
    models = {}
    if 'gender' in enabled:
        from namecore import guess_gender
        models['gender'] = guess_gender
    if 'decade' in enabled:
        from namecore import guess_decade
        models['decade'] = guess_decade
    if 'zodiac' in enabled:
        from namecore import guess_zodiac
        models['zodiac'] = guess_zodiac
    if 'season' in enabled:
        from namecore import guess_season
        models['season'] = guess_season
    if 'solar' in enabled:
        from namecore import guess_solar
        models['solar'] = guess_solar
    return models


def build_header(enabled):
    cols = ['input']
    for key, label, prob_label in MODEL_META:
        if key in enabled:
            cols += [label, prob_label]
    return ','.join(cols)


def process(name, mode, models):
    row = [name]
    for key, _, _ in MODEL_META:
        if key not in models:
            continue
        result = models[key](name, mode)
        row.append(result[0])
        row.append(f'{result[1]:.4f}')
    return row


def detect_mode(first_line):
    return VALID_MODES.get(first_line.lstrip('﻿').lower())


def main():
    parser = argparse.ArgumentParser(description='姓名属性批量标记')
    parser.add_argument('input', help='输入文件路径')
    parser.add_argument('--models', default='all',
                        help='模型列表, 逗号分隔 (gender,decade,zodiac,season,solar 或 all)')
    parser.add_argument('--mode', default='auto',
                        help='输入模式: auto/namea(姓名), namec(名), named/e/f(单字/首字/末字)')
    parser.add_argument('--output', default=None, help='输出文件 (默认: input_marked.csv)')
    parser.add_argument('--encoding', default='utf-8', help='输入编码 (默认: utf-8, 可选: gbk)')
    args = parser.parse_args()

    default_mode = 'auto' if args.mode == 'namea' else args.mode

    if not os.path.isfile(args.input):
        print(f'错误: 文件不存在 {args.input}')
        sys.exit(1)

    enabled = set(MODEL_META[i][0] for i in range(len(MODEL_META))) if args.models == 'all' \
        else set(m.strip() for m in args.models.split(','))

    t0 = time.time()
    models = load_models(enabled)
    print(f'启用模型: {", ".join(sorted(enabled))}')
    print(f'加载耗时: {time.time() - t0:.1f}s')

    outpath = args.output or (os.path.splitext(args.input)[0] + '_marked.csv')
    print(f'输入: {args.input}')
    print(f'输出: {outpath}')

    t_start = time.time()
    with open(args.input, 'r', encoding=args.encoding, errors='replace') as fin, \
         open(outpath, 'w', encoding='utf-8-sig') as fout:
        first = fin.readline().strip()
        mode = detect_mode(first)
        first_is_data = mode is None
        if mode:
            print(f'模式: {first.lstrip(chr(0xfeff))} → {mode}')
        else:
            mode = default_mode
            print(f'模式: {mode} (首行非声明)')

        fout.write(build_header(enabled) + '\n')
        count = 0
        if first_is_data and first:
            fout.write(','.join(process(first, mode, models)) + '\n')
            count = 1
        for line in fin:
            name = line.strip()
            if not name:
                continue
            fout.write(','.join(process(name, mode, models)) + '\n')
            count += 1
            if count % 200000 == 0:
                elapsed = time.time() - t_start
                print(f'  已处理 {count // 10000}W (速度: {count / elapsed:.0f} 行/s)')

    elapsed = time.time() - t_start
    print(f'完成: {count:,} 行, 耗时 {elapsed:.1f}s ({count / max(elapsed, 0.01):.0f} 行/s)')


if __name__ == '__main__':
    main()
