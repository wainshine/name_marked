# Name Marked — 中文姓名属性识别系统

> v1.0.0

基于海量中文人名数据，通过贝叶斯算法从姓名中识别性别、出生年代、星座、四季、节气五种属性。

## 目录结构

```
name_marked/
├── tables/                          # 频率表（5个CSV，由build脚本生成）
│   ├── charfreq.csv                 #   字符-性别频率（31,317行）
│   ├── decadefreq.csv               #   字符-年代频率，含2000s插值（31,317行）
│   ├── zodiacfreq.csv               #   人名-星座频率（191,801行）
│   ├── seasonfreq.csv               #   人名-四季频率（191,801行）
│   └── solarfreq.csv                #   人名-节气频率（191,801行）
│
├── data/
│   ├── train/                       # 训练数据
│   │   ├── 有效数据.txt             #   训练数据（GBK编码）
│   │   └── 无效数据.txt             #   被过滤掉的记录及原因
│   ├── ref/                         # 参考数据
│   │   ├── nameb.txt                #   姓氏表（1018单姓 + 56复姓）
│   │   ├── 《通用规范汉字表》（2013年）.txt  # 标准汉字8105字
│   │   └── .cache_givenname.csv     #   ChineseNames缓存（自动下载）
│   └── samples/                     # 测试样本及输出
│
├── utils.py                         # 共享工具：姓氏加载、名字提取、繁简转换
├── gender_guess.py                  # 性别识别（位置感知贝叶斯，2类）
├── decade_guess.py                  # 年代识别（位置感知贝叶斯，6类）
├── zodiac_guess.py                  # 星座识别（人名级查找，12类）
├── season_guess.py                  # 四季识别（人名级查找，4类）
├── solar_guess.py                   # 节气识别（人名级查找，24类）
├── batch_guess.py                   # 批处理CLI入口
├── test_guessers.py                 # 单元测试（44项）
├── build_*.py                       # 5个频率表构建脚本
└── .gitignore
```

## 依赖

| 依赖 | 用途 | 必需 |
|------|------|:--:|
| Python 3.x | 运行环境 | ✓ |
| `data/train/有效数据.txt` | 训练数据（GBK） | ✓ |
| `data/ref/nameb.txt` | 姓氏表 | ✓ |
| `data/ref/《通用规范汉字表》（2013年）.txt` | 标准汉字表 | ✓ |
| [OpenCC](https://github.com/BYVoid/OpenCC) | 繁简转换 | 可选 |
| [ChineseNames](https://github.com/psychbruce/ChineseNames) | 2000s插值 | 仅构建 |

安装 OpenCC：

```bash
pip install opencc-python-reimplemented
```

未安装时，繁简转换自动跳过（简体输入不受影响）。

## 快速开始

### Python API

```python
from gender_guess import guess as guess_gender
from decade_guess import guess as guess_decade
from zodiac_guess import guess as guess_zodiac

# 性别 → ('男', 0.9045)
guess_gender('王伟')

# 年代 → ('2000s', 0.8620, {'1950s前':0.01, '1960s':0.01, ...})
guess_decade('张宇轩')

# 星座 → ('天秤座', 0.2456, {...})
guess_zodiac('刘亦菲')

# 支持繁体自动转换
guess_gender('張偉')  # → ('男', 0.9045)
```

### 批处理 CLI

```bash
# 全部5项标记
python batch_guess.py data/samples/names.txt

# 仅性别+年代
python batch_guess.py data/samples/names.txt --models gender,decade

# GBK编码 + namea模式
python batch_guess.py data/samples/names_gbk.txt --mode namea --encoding gbk

# 自定义输出
python batch_guess.py data/samples/names.txt --output result.csv
```

**输入格式：**

```csv
namec
建国
伟
芳菲
```

首行 `namea` 或 `namec`（不区分大小写，兼容BOM）自动识别输入类型。无首行时用 `--mode` 指定。繁体文本自动检测并转换为简体。

**输出格式：**

```csv
input,性别,性别概率,年代,年代概率,星座,星座概率,四季,四季概率,节气,节气概率
建国,男,0.9976,1960s,0.3514,天秤座,0.1440,秋,0.3661,秋分,0.0739
伟,男,0.9045,1980s,0.3561,天秤座,0.1320,秋,0.3517,寒露,0.0706
```

## 核心概念

### 位置编码

同一个汉字在名字中的不同位置，属性倾向不同。拆分为四种位置分别建模：

| 后缀 | 含义 | 示例 |
|------|------|------|
| `_p0` | 单字名 | 王**伟** → `伟_p0` |
| `_p1` | 双字名第1字 | 李**建**国 → `建_p1` |
| `_p2` | 双字名第2字 | 李建**国** → `国_p2` |
| `_p3` | 叠字名 | 黄婷**婷** → `婷_p3` |

### 输入模式

| mode | 含义 | 示例 | 支持模型 |
|------|------|------|:--:|
| `auto` / `namea` | 完整姓名，自动提取名 | `王伟` → 名=`伟` | 全部 |
| `namec` | 名（已去除姓氏） | `建国` → 直接使用 | 全部 |
| `named` | 单字名 | `伟` → `伟_p0` | 性别/年代 |
| `namee` | 双字名首字 | `建` → `建_p1` | 性别/年代 |
| `namef` | 双字名末字 | `国` → `国_p2` | 性别/年代 |

### 名词定义

| 缩写 | 含义 | 示例（欧阳芳菲） |
|------|------|------|
| namea | 姓名 | 欧阳芳菲 |
| nameb | 姓氏 | 欧阳 |
| namec | 名 | 芳菲 |
| named | 单字名 | — |
| namee | 双字名首字 | 芳 |
| namef | 双字名末字 | 菲 |

## 数据来源

训练数据来自 `data/train/有效数据.txt`，每行为 `姓名,标签`（GBK编码），标签含性别和出生年月信息。经过以下清洗：

- 姓名校验：姓氏表匹配 + 长度限制 + 标准汉字表（8,105字，过滤至 [一-龥] 范围内 7,829 字）
- 数据去重
- 年代筛选：1930–1999年出生

## 算法

### 字符级贝叶斯（性别、年代）

```
P(class | name) ∝ P(class) × Π P(char_pos_i | class)
```

1. 提取名部分，生成位置键（`_p0` / `_p1` / `_p2` / `_p3`）
2. 从频率表查找每个位置键的类别条件概率
3. 乘以先验概率（基于真实人口统计），取最大后验类别

### 人名级查找（星座、四季、节气）

1. 提取完整名（如"建国"、"芳菲"）
2. 在频率表中查找该名的类别分布
3. 乘以先验概率，取最大后验类别
4. 名不在表中（频次 < 10）返回"未知"

### 繁体自动转换

每个 `guess()` 调用首先通过 [OpenCC](https://github.com/BYVoid/OpenCC) 将输入转换为简体（幂等，简体输入零开销）。OpenCC未安装时静默跳过。

## 模型概览

| 模型 | 类别数 | 算法 | 先验 | 准确率 | 信号 |
|------|:--:|------|------|------|:--:|
| 性别 | 2 | 位置感知贝叶斯 | 七普 51.2/48.8 | **86.2%** | 强 |
| 年代 | 6 | 位置感知贝叶斯 | 七普年龄结构 | 76.3%(±1) | 中 |
| 四季 | 4 | 人名级贝叶斯 | 出生分布 | 27.4% | 弱 |
| 星座 | 12 | 人名级贝叶斯 | 用户分布 | 11.8% | 弱 |
| 节气 | 24 | 人名级贝叶斯 | 出生分布 | 6.8% | 弱 |

- **性别**：男女准确率近乎均衡（男 86.1%，女 86.3%）
- **年代**：6分类精确匹配 35%，±1年代 76%。2000s类别通过 [ChineseNames](https://github.com/psychbruce/ChineseNames) 数据插值生成
- **星座/四季/节气**：名字与出生日期几乎无关联，仅略高于随机基线

## 构建频率表

从训练数据重新生成所有频率表：

```bash
cd name_marked
python build_charfreq.py     # → tables/charfreq.csv
python build_decadefreq.py   # → tables/decadefreq.csv（需ChineseNames）
python build_zodiacfreq.py   # → tables/zodiacfreq.csv
python build_seasonfreq.py   # → tables/seasonfreq.csv
python build_solarfreq.py    # → tables/solarfreq.csv
```

前置条件：`data/train/有效数据.txt` 存在。`build_decadefreq.py` 自动从 GitHub 获取 ChineseNames 数据并缓存。

### 2000s 数据插值

训练数据止于1999年。2000s类别通过以下方式插值：

1. 加载 [ChineseNames](https://github.com/psychbruce/ChineseNames) 的字频数据（含 2000–2008 年）
2. 对每个字-位置组合，计算比值 `r = CN_2000s / CN_1990s`
3. 插值：`count_2000s = count_1990s × r × (10/9)`
4. `(10/9)` 修正因 2000–2008 仅覆盖9年

## 数据文件格式

### charfreq.csv / decadefreq.csv（字符级）

```
char_pos,female,male
伟_p0,12345,67890
建_p1,2345,45678
```

31,317行 = 7,829标准字 × 4位置 + 表头。decadefreq.csv 列数为6个年代类别。

### zodiacfreq.csv / seasonfreq.csv / solarfreq.csv（人名级）

```
given_name,摩羯座,水瓶座,...,射手座
建国,12345,11234,...,8901
```

191,801行 = 频次≥10的人名 + 表头。列数分别为12/4/24。

## 运行测试

```bash
cd name_marked
python test_guessers.py
# 44 tests：utils / 5个guesser / priors验证
```

## 性能

| 场景 | 速度 |
|------|------|
| 性别单项 | 740,000 行/s |
| 性别+年代 | 250,000 行/s |
| 全部5项 | 150,000 行/s |

测试环境：Mac, Python 3.14, 194万行输入。

## License

训练数据与参考数据的版权归原始数据提供方所有。代码遵循 Apache 2.0 协议。

## 致谢

- [ngender](https://github.com/observerss/ngender) — 性别识别的朴素贝叶斯实现参考
- [ChineseNames](https://github.com/psychbruce/ChineseNames) — 年代模型中 2000s 类别的字频数据
- [OpenCC](https://github.com/BYVoid/OpenCC) — 繁简转换引擎
