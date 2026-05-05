#!/usr/bin/env python3
"""
单元测试 — 5种识别方法
"""
import sys, os, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import given_name, pos_keys, load_std_chars


class TestUtils(unittest.TestCase):

    def test_given_name_single(self):
        self.assertEqual(given_name('王伟'), '伟')
        self.assertEqual(given_name('张丽'), '丽')
        self.assertEqual(given_name('李强'), '强')

    def test_given_name_compound(self):
        self.assertEqual(given_name('欧阳娜娜'), '娜娜')
        self.assertEqual(given_name('司马光'), '光')
        self.assertEqual(given_name('上官婉儿'), '婉儿')

    def test_given_name_unknown(self):
        # Unknown surname: whole name returned as given name
        result = given_name('阿Q正传')
        self.assertGreater(len(result), 0)

    def test_given_name_empty(self):
        self.assertEqual(given_name(''), '')

    def test_given_name_known_surname(self):
        # "可" is a valid surname, so given_name('可亚洲') = '亚洲'
        self.assertEqual(given_name('可亚洲'), '亚洲')

    def test_pos_keys_single(self):
        self.assertEqual(pos_keys('伟'), ['伟_p0'])

    def test_pos_keys_double(self):
        self.assertEqual(pos_keys('建国'), ['建_p1', '国_p2'])

    def test_pos_keys_repeated(self):
        self.assertEqual(pos_keys('婷婷'), ['婷_p3'])
        self.assertEqual(pos_keys('伟伟'), ['伟_p3'])

    def test_pos_keys_empty(self):
        self.assertEqual(pos_keys(''), [])

    def test_pos_keys_three_chars(self):
        self.assertEqual(pos_keys('烊千玺'), [])

    def test_load_std_chars(self):
        table = os.path.join(os.path.dirname(__file__), 'data', 'ref', '《通用规范汉字表》（2013年）.txt')
        chars = load_std_chars(table)
        self.assertGreater(len(chars), 7000)
        self.assertIn('一', chars)
        self.assertIn('齉', chars)  # last char in table
        for c in chars:
            self.assertTrue('\u4e00' <= c <= '\u9fa5', f'{c} out of range')


class TestGenderGuesser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from gender_guess import GenderGuesser
        cls.g = GenderGuesser()

    def test_male_names(self):
        tests = [('王伟', '男'), ('李建国', '男'), ('黄自强', '男'), ('张宇轩', '男')]
        for name, expected in tests:
            with self.subTest(name=name):
                pred, prob = self.g.guess(name)
                self.assertEqual(pred, expected)
                self.assertGreater(prob, 0.5)

    def test_female_names(self):
        tests = [('刘亦菲', '女'), ('欧阳芳菲', '女')]
        for name, expected in tests:
            with self.subTest(name=name):
                pred, prob = self.g.guess(name)
                self.assertEqual(pred, expected)
                self.assertGreater(prob, 0.5)

    def test_probability_range(self):
        for name in ['王伟', '刘亦菲', '杨洋']:
            _, prob = self.g.guess(name)
            self.assertGreaterEqual(prob, 0)
            self.assertLessEqual(prob, 1.0)

    def test_unknown_name(self):
        pred, prob = self.g.guess('')
        self.assertEqual(pred, '未知')

    def test_mode_namec(self):
        """输入名部分（非完整姓名）"""
        pred, prob = self.g.guess('伟', mode='namec')
        self.assertEqual(pred, '男')
        pred, prob = self.g.guess('芳菲', mode='namec')
        self.assertEqual(pred, '女')

    def test_mode_named_namee_namef(self):
        """单字/拆字模式"""
        pred, _ = self.g.guess('建国', mode='namec')
        pe, _ = self.g.guess('建', mode='namee')
        pf, _ = self.g.guess('国', mode='namef')
        self.assertEqual(pred, '男')
        self.assertEqual(pe, '男')
        self.assertEqual(pf, '男')

    def test_mode_consistency(self):
        """auto 和 namec 结果一致"""
        g1, p1 = self.g.guess('王伟', mode='auto')
        g2, p2 = self.g.guess('伟', mode='namec')
        self.assertEqual(g1, g2)

    def test_invalid_mode(self):
        with self.assertRaises(ValueError):
            self.g.guess('王伟', mode='invalid')


class TestDecadeGuesser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from decade_guess import DecadeGuesser, _DECADE_CLASSES
        cls.g = DecadeGuesser()
        cls.classes = _DECADE_CLASSES

    def test_older_names(self):
        pred, prob, _ = self.g.guess('李建国')
        self.assertIn(pred, ['1960s', '1970s'])

    def test_younger_names(self):
        pred, prob, all_p = self.g.guess('张宇轩')
        # 张宇轩 is a 2000s-style name
        self.assertEqual(pred, '2000s')

    def test_mid_names(self):
        pred, prob, _ = self.g.guess('王伟')
        self.assertEqual(pred, '1980s')

    def test_all_probs_sum_to_one(self):
        _, _, all_p = self.g.guess('王伟')
        self.assertAlmostEqual(sum(all_p.values()), 1.0, places=4)

    def test_unknown(self):
        p, _, _ = self.g.guess('')
        self.assertEqual(p, '未知')

    def test_mode_namec(self):
        a_pred, _, _ = self.g.guess('王伟', 'auto')
        c_pred, _, _ = self.g.guess('伟', 'namec')
        self.assertEqual(a_pred, c_pred)

    def test_mode_named_namee_namef(self):
        from decade_guess import _DECADE_CLASSES
        d, _, _ = self.g.guess('建国', 'namec')
        de, _, _ = self.g.guess('建', 'namee')
        df, _, _ = self.g.guess('国', 'namef')
        self.assertIn(d, _DECADE_CLASSES)
        self.assertIn(de, _DECADE_CLASSES)
        self.assertIn(df, _DECADE_CLASSES)


class TestZodiacGuesser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from zodiac_guess import ZodiacGuesser
        cls.g = ZodiacGuesser()

    def test_returns_valid_zodiac(self):
        from zodiac_guess import ZODIACS
        for name in ['王伟', '刘亦菲', '张宇轩']:
            pred, prob, all_p = self.g.guess(name)
            if pred != '未知':
                self.assertIn(pred, ZODIACS)

    def test_probability_sum(self):
        _, _, all_p = self.g.guess('王伟')
        if all_p:
            self.assertAlmostEqual(sum(all_p.values()), 1.0, places=4)

    def test_unknown(self):
        p, _, _ = self.g.guess('')
        self.assertEqual(p, '未知')

    def test_mode_namec(self):
        a_pred, _, _ = self.g.guess('王伟', 'auto')
        c_pred, _, _ = self.g.guess('伟', 'namec')
        self.assertEqual(a_pred, c_pred)

    def test_mode_unsupported(self):
        """named/namee/namef 对名字级模型返回未知"""
        for m in ['named', 'namee', 'namef']:
            p, _, _ = self.g.guess('伟', m)
            self.assertEqual(p, '未知')


class TestSeasonGuesser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from season_guess import SeasonGuesser
        cls.g = SeasonGuesser()

    def test_returns_valid_season(self):
        for name in ['王伟', '刘亦菲', '李建国']:
            pred, prob, all_p = self.g.guess(name)
            if pred != '未知':
                self.assertIn(pred, ['春', '夏', '秋', '冬'])

    def test_probability_sum(self):
        _, _, all_p = self.g.guess('王伟')
        if all_p:
            self.assertAlmostEqual(sum(all_p.values()), 1.0, places=4)

    def test_mode_namec(self):
        a_pred, _, _ = self.g.guess('王伟', 'auto')
        c_pred, _, _ = self.g.guess('伟', 'namec')
        self.assertEqual(a_pred, c_pred)

    def test_mode_unsupported(self):
        for m in ['named', 'namee', 'namef']:
            p, _, _ = self.g.guess('伟', m)
            self.assertEqual(p, '未知')


class TestSolarGuesser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from solar_guess import SolarGuesser
        cls.g = SolarGuesser()

    def test_returns_valid_solar(self):
        from solar_guess import SOLAR_TERMS
        for name in ['王伟', '刘亦菲']:
            pred, prob, all_p = self.g.guess(name)
            if pred != '未知':
                self.assertIn(pred, SOLAR_TERMS)

    def test_probability_sum(self):
        _, _, all_p = self.g.guess('王伟')
        if all_p:
            self.assertAlmostEqual(sum(all_p.values()), 1.0, places=4)

    def test_mode_namec(self):
        a_pred, _, _ = self.g.guess('王伟', 'auto')
        c_pred, _, _ = self.g.guess('伟', 'namec')
        self.assertEqual(a_pred, c_pred)

    def test_mode_unsupported(self):
        for m in ['named', 'namee', 'namef']:
            p, _, _ = self.g.guess('伟', m)
            self.assertEqual(p, '未知')


class TestPriors(unittest.TestCase):
    """Verify all priors sum to 1.0"""

    def test_gender_priors(self):
        from gender_guess import GenderGuesser
        g = GenderGuesser()
        self.assertAlmostEqual(g.PRIOR_MALE + g.PRIOR_FEMALE, 1.0)

    def test_decade_priors(self):
        from decade_guess import DecadeGuesser
        g = DecadeGuesser()
        self.assertAlmostEqual(sum(g.PRIORS.values()), 1.0)

    def test_zodiac_priors(self):
        from zodiac_guess import ZodiacGuesser
        g = ZodiacGuesser()
        self.assertAlmostEqual(sum(g.PRIORS.values()), 1.0, places=2)

    def test_season_priors(self):
        from season_guess import SeasonGuesser
        g = SeasonGuesser()
        self.assertAlmostEqual(sum(g.PRIORS.values()), 1.0, places=2)

    def test_solar_priors(self):
        from solar_guess import SolarGuesser
        g = SolarGuesser()
        self.assertAlmostEqual(sum(g.PRIORS.values()), 1.0, places=3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
