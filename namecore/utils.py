#!/usr/bin/env python3
"""共享工具 — 姓氏加载、名提取、位置键生成、繁简转换"""

import os

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_BASE_DIR)
SURNAME_FILE = os.path.join(_PROJECT_DIR, 'data', 'ref', 'nameb.txt')
STD_CHAR_FILE = os.path.join(_PROJECT_DIR, 'data', 'ref', '《通用规范汉字表》（2013年）.txt')

_single = None
_compound = None
_opencc = None
_std_chars = None
_trad_warned = False


def _load():
    global _single, _compound
    if _single is not None:
        return
    _single, _compound = set(), set()
    with open(SURNAME_FILE, 'r', encoding='utf-8') as f:
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


def pos_keys(gn):
    """
    位置感知键
    p0:单字名  p1:双字名首字  p2:双字名末字  p3:叠字名
    三字名按首字p1+末字p2处理（训练数据中三字名极少，无独立位置统计）
    """
    n = len(gn)
    if n == 1:
        return [f'{gn}_p0']
    if n == 2:
        if gn[0] == gn[1]:
            return [f'{gn[0]}_p3']
        return [f'{gn[0]}_p1', f'{gn[1]}_p2']
    if n == 3:
        return [f'{gn[0]}_p1', f'{gn[2]}_p2']
    return []


def load_std_chars(filepath=STD_CHAR_FILE):
    """加载标准汉字表 ∩ [一-龥]"""
    chars = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                for c in line:
                    if '一' <= c <= '龥':
                        chars.add(c)
    except (FileNotFoundError, PermissionError):
        pass
    return chars


def detect_traditional(text, sample_size=200):
    """采样前 sample_size 个CJK字符，返回繁体字占比"""
    std_chars = None
    cjk_count = 0
    trad_count = 0
    for c in text:
        if '一' <= c <= '龥':
            cjk_count += 1
            if cjk_count > sample_size:
                break
            if std_chars is None:
                std_chars = load_std_chars()
            if c not in std_chars:
                trad_count += 1
    if cjk_count == 0:
        return 0.0
    return trad_count / cjk_count


def to_simplified(text):
    """繁体转简体（OpenCC，未安装时原样返回）。纯简体输入走快速路径，零开销"""
    global _opencc, _trad_warned, _std_chars
    if _std_chars is None:
        _std_chars = load_std_chars()
    has_trad = False
    for c in text:
        if '一' <= c <= '龥' and c not in _std_chars:
            has_trad = True
            break
    if not has_trad:
        return text
    if _opencc is None:
        try:
            from opencc import OpenCC
            _opencc = OpenCC('t2s')
        except ImportError:
            _opencc = False
    if not _opencc:
        return text
    if not _trad_warned and len(text) > 10:
        ratio = detect_traditional(text)
        if ratio > 0.05:
            print(f'[繁体检测] 比例 {ratio * 100:.0f}%，自动转换简体')
            _trad_warned = True
    return _opencc.convert(text)


def extract_given(name, mode):
    """根据输入模式提取名部分。auto/namea: 完整姓名  namec: 名"""
    if mode in ('auto', 'namea'):
        return given_name(name)
    if mode == 'namec':
        return name
    return name


def mode_keys(name, mode):
    """
    根据模式返回位置键列表
    auto: 姓名→提取名→pos_keys   namec: 名→pos_keys
    named: 单字名_p0  namee: 双字首字_p1  namef: 双字末字_p2
    """
    if mode in ('auto', 'namea'):
        return pos_keys(given_name(name))
    if mode == 'namec':
        return pos_keys(name)
    if mode == 'named':
        return [f'{name}_p0'] if name else []
    if mode == 'namee':
        return [f'{name}_p1'] if name else []
    if mode == 'namef':
        return [f'{name}_p2'] if name else []
    raise ValueError(f"Unknown mode: {mode}, expected auto/namec/named/namee/namef")
