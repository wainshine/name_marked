#!/usr/bin/env python3
"""
批处理模块 — 对文件批量标记姓名属性

用法:
  python batch_guess.py input.txt                           # 默认5项全标记
  python batch_guess.py input.txt --models gender           # 仅性别
  python batch_guess.py input.txt --models gender,decade    # 性别+年代
  python batch_guess.py input.txt --output result.csv       # 指定输出

输入文件:
  - 首行为 namea 或 namec (不区分大小写)，声明输入类型
  - 其余每行一个姓名/名字
  - 示例:
      namec
      建国
      伟
      芳菲

模式:
  namea → 完整姓名(自动提取名)    namec → 名(已去除姓氏)
"""

import os, sys, argparse, time

# 懒加载模型
_models = None


def _load_models(enabled):
    global _models
    if _models is not None:
        return _models
    _models = {}
    if 'gender' in enabled:
        from gender_guess import guess as g
        _models['gender'] = g
    if 'decade' in enabled:
        from decade_guess import guess as d
        _models['decade'] = d
    if 'zodiac' in enabled:
        from zodiac_guess import guess as z
        _models['zodiac'] = z
    if 'season' in enabled:
        from season_guess import guess as s
        _models['season'] = s
    if 'solar' in enabled:
        from solar_guess import guess as st
        _models['solar'] = st
    return _models


MODEL_META = [
    ('gender', '性别', '性别概率'),
    ('decade', '年代', '年代概率'),
    ('zodiac', '星座', '星座概率'),
    ('season', '四季', '四季概率'),
    ('solar', '节气', '节气概率'),
]


def build_header(enabled):
    cols = ['input']
    for key, label, prob_label in MODEL_META:
        if key in enabled:
            cols.append(label)
            cols.append(prob_label)
    return ','.join(cols)


def process(name, mode, models):
    """返回一行各字段的列表"""
    row = [name]
    for key, _, _ in MODEL_META:
        if key not in models:
            continue
        func = models[key]
        if key in ('gender',):
            label, prob = func(name, mode)
        else:
            label, prob, _ = func(name, mode)
        row.append(label)
        row.append(f'{prob:.4f}')
    return row


VALID_MODES = {'namea': 'auto', 'namec': 'namec'}


def detect_mode(first_line):
    """检测首行模式: namea → auto, namec → namec"""
    h = first_line.lstrip('\ufeff').lower()
    return VALID_MODES.get(h)


def main():
    parser = argparse.ArgumentParser(description='姓名属性批量标记')
    parser.add_argument('input', help='输入文件路径')
    parser.add_argument('--models', default='all',
                        help='模型列表, 逗号分隔 (gender,decade,zodiac,season,solar 或 all)')
    parser.add_argument('--mode', default='auto',
                        help='输入模式: auto/namea(姓名), namec(名), named/e/f(单字/首字/末字)')
    parser.add_argument('--output', default=None, help='输出文件 (默认: input_marked.csv)')
    parser.add_argument('--encoding', default='utf-8', help='输入文件编码 (默认: utf-8, 可选: gbk)')
    args = parser.parse_args()

    # 规范化: namea → auto
    default_mode = args.mode
    if default_mode == 'namea':
        default_mode = 'auto'

    inpath = args.input
    if not os.path.isfile(inpath):
        print(f'错误: 文件不存在 {inpath}')
        sys.exit(1)

    # 解析模型
    if args.models == 'all':
        enabled = set(k for k, _, _ in MODEL_META)
    else:
        enabled = set(m.strip() for m in args.models.split(','))

    # 预加载
    t0 = time.time()
    models = _load_models(enabled)
    header = build_header(enabled)
    print(f'启用模型: {", ".join(enabled)}')
    print(f'加载耗时: {time.time() - t0:.1f}s')

    # 输出路径
    outpath = args.output or (os.path.splitext(inpath)[0] + '_marked.csv')

    # 流式处理
    print(f'输入: {inpath}')
    print(f'输出: {outpath}')

    t_start = time.time()

    with open(inpath, 'r', encoding=args.encoding, errors='replace') as fin, \
         open(outpath, 'w', encoding='utf-8-sig') as fout:

        # 首行检测模式
        first = fin.readline().strip()
        mode = detect_mode(first)
        first_is_data = (mode is None)
        if mode:
            print(f'模式: {first.strip().lstrip(chr(0xfeff))} → {mode}')
        else:
            mode = default_mode
            print(f'模式: {mode} (首行非声明)')

        fout.write(header + '\n')

        count = 0

        # 处理首行（如果是数据）
        if first_is_data and first:
            result = process(first, mode, models)
            if result:
                fout.write(','.join(result) + '\n')
                count = 1

        for line in fin:
            name = line.strip()
            if not name:
                continue
            result = process(name, mode, models)
            if result:
                fout.write(','.join(result) + '\n')
                count += 1
                if count % 200000 == 0:
                    elapsed = time.time() - t_start
                    speed = count / elapsed
                    print(f'  已处理 {count//10000}W (速度: {speed:.0f} 行/s)')

    elapsed = time.time() - t_start
    print(f'完成: {count:,} 行, 耗时 {elapsed:.1f}s ({count/elapsed:.0f} 行/s)')


if __name__ == '__main__':
    main()
