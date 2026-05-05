#!/usr/bin/env python3
"""
共享工具模块 — 姓氏加载、名提取、位置键生成、繁简转换
"""

__version__ = '1.0.0'

import os

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SURNAME_FILE = os.path.join(_BASE_DIR, 'data', 'ref', 'nameb.txt')

# 懒加载缓存
_single = None
_compound = None
_opencc = None
_trad_warned = False


def _load():
    global _single, _compound
    if _single is not None:
        return
    _single, _compound = set(), set()
    with open(_SURNAME_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            s = line.strip()
            if not s or s == 'NameB':
                continue
            if len(s) == 1:
                _single.add(s)
            elif len(s) == 2:
                _compound.add(s)


def get_single_surnames():
    _load()
    return _single


def get_compound_surnames():
    _load()
    return _compound


def given_name(full_name):
    """从完整姓名中提取名部分（去除姓氏，含复姓）"""
    _load()
    name = full_name.strip()
    if len(name) >= 2 and name[:2] in _compound:
        return name[2:]
    if len(name) >= 1 and name[0] in _single:
        return name[1:]
    return name


def pos_keys(given_name):
    """
    生成位置感知键列表
    p0:单字名  p1:双字名首字  p2:双字名末字  p3:叠字名
    """
    keys = []
    if len(given_name) == 1:
        keys.append(f'{given_name}_p0')
    elif len(given_name) == 2:
        if given_name[0] == given_name[1]:
            keys.append(f'{given_name[0]}_p3')
        else:
            keys.append(f'{given_name[0]}_p1')
            keys.append(f'{given_name[1]}_p2')
    return keys


def load_std_chars(filepath):
    """加载标准汉字表 ∩ [一-龥]"""
    chars = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                for c in line:
                    if '\u4e00' <= c <= '\u9fa5':
                        chars.add(c)
    except (FileNotFoundError, PermissionError):
        pass
    return chars


def detect_traditional(text, sample_size=200):
    """检测文本中的繁体比例。采样前 sample_size 个CJK字符，返回繁体字占比"""
    std_chars = None  # lazy load
    cjk_count = 0
    trad_count = 0
    for c in text:
        if '\u4e00' <= c <= '\u9fa5':
            cjk_count += 1
            if cjk_count > sample_size:
                break
            # 检查是否在标准简体中
            if std_chars is None:
                std_table = os.path.join(_BASE_DIR, 'data', 'ref', '《通用规范汉字表》（2013年）.txt')
                std_chars = load_std_chars(std_table)
            if c not in std_chars:
                trad_count += 1
    if cjk_count == 0:
        return 0.0
    return trad_count / cjk_count


def to_simplified(text):
    """繁体转简体（自动检测+转换+一次提示），使用 OpenCC"""
    global _opencc, _trad_warned
    try:
        if _opencc is None:
            from opencc import OpenCC
            _opencc = OpenCC('t2s')
    except ImportError:
        return text
    if _opencc is None:
        return text

    # 检测繁体比例，超阈值时打印一次提示
    if not _trad_warned and len(text) > 10:
        ratio = detect_traditional(text)
        if ratio > 0.05:
            print(f'[繁体检测] 比例 {ratio*100:.0f}%，自动转换简体')
            _trad_warned = True

    return _opencc.convert(text)


def mode_keys(name, mode):
    """
    根据模式返回位置键列表
    auto: 姓名→提取名→pos_keys   namec: 名→pos_keys
    named: 单字名_p0  namee: 首字_p1  namef: 末字_p2
    """
    if mode == 'auto':
        gn = given_name(name)
        return pos_keys(gn)
    elif mode == 'namec':
        return pos_keys(name)
    elif mode == 'named':
        return [f'{name}_p0'] if name else []
    elif mode == 'namee':
        return [f'{name}_p1'] if name else []
    elif mode == 'namef':
        return [f'{name}_p2'] if name else []
    raise ValueError(f"Unknown mode: {mode}, expected auto/namec/named/namee/namef")
