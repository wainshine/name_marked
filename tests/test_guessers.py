#!/usr/bin/env python3
"""单元测试 — namecore 包"""
import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from namecore.utils import given_name, pos_keys, load_std_chars, to_simplified


class TestUtils(unittest.TestCase):

    def test_given_name_single(self):
        self.assertEqual(given_name('王伟'), '伟')
        self.assertEqual(given_name('张丽'), '丽')

    def test_given_name_compound(self):
        self.assertEqual(given_name('欧阳娜娜'), '娜娜')
        self.assertEqual(given_name('司马光'), '光')
        self.assertEqual(given_name('上官婉儿'), '婉儿')

    def test_given_name_empty(self):
        self.assertEqual(given_name(''), '')

    def test_pos_keys_single(self):
        self.assertEqual(pos_keys('伟'), ['伟_p0'])

    def test_pos_keys_double(self):
        self.assertEqual(pos_keys('建国'), ['建_p1', '国_p2'])

    def test_pos_keys_repeated(self):
        self.assertEqual(pos_keys('婷婷'), ['婷_p3'])

    def test_pos_keys_three_chars(self):
        self.assertEqual(pos_keys('烊千玺'), ['烊_p1', '玺_p2'])

    def test_pos_keys_empty(self):
        self.assertEqual(pos_keys(''), [])

    def test_load_std_chars(self):
        chars = load_std_chars()
        self.assertGreater(len(chars), 7000)
        self.assertIn('一', chars)

    def test_to_simplified_idempotent(self):
        self.assertEqual(to_simplified('王伟'), '王伟')


class TestGenderGuesser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from namecore.gender import GenderGuesser
        cls.g = GenderGuesser()

    def test_male_names(self):
        for name in ['王伟', '李建国', '黄自强', '张宇轩']:
            with self.subTest(name=name):
                pred, prob = self.g.guess(name)
                self.assertEqual(pred, '男')
                self.assertGreater(prob, 0.5)

    def test_female_names(self):
        for name in ['刘亦菲', '欧阳芳菲', '黄婷婷']:
            with self.subTest(name=name):
                pred, prob = self.g.guess(name)
                self.assertEqual(pred, '女')
                self.assertGreater(prob, 0.5)

    def test_three_char_name(self):
        pred, prob = self.g.guess('易烊千玺')
        self.assertIn(pred, ['男', '女'])
        self.assertGreater(prob, 0.5)

    def test_empty(self):
        pred, prob = self.g.guess('')
        self.assertEqual(pred, '未知')

    def test_mode_namec(self):
        self.assertEqual(self.g.guess('伟', mode='namec')[0], '男')
        self.assertEqual(self.g.guess('芳菲', mode='namec')[0], '女')

    def test_mode_named_namee_namef(self):
        self.assertEqual(self.g.guess('建国', mode='namec')[0], '男')
        self.assertEqual(self.g.guess('建', mode='namee')[0], '男')
        self.assertEqual(self.g.guess('国', mode='namef')[0], '男')

    def test_mode_consistency(self):
        g1, _ = self.g.guess('王伟', mode='auto')
        g2, _ = self.g.guess('伟', mode='namec')
        self.assertEqual(g1, g2)

    def test_invalid_mode(self):
        with self.assertRaises(ValueError):
            self.g.guess('王伟', mode='invalid')

    def test_rare_char_no_unknown(self):
        """生僻字不应返回未知（回退到先验/平滑）"""
        pred, prob = self.g.guess('王龘', mode='auto')
        self.assertIn(pred, ['男', '女'])

    def test_probability_range(self):
        for name in ['王伟', '刘亦菲', '杨洋']:
            _, prob = self.g.guess(name)
            self.assertGreaterEqual(prob, 0)
            self.assertLessEqual(prob, 1.0)


class TestDecadeGuesser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from namecore.decade import DecadeGuesser, DECADE_CLASSES
        cls.g = DecadeGuesser()
        cls.classes = DECADE_CLASSES

    def test_older_name(self):
        pred, _, _ = self.g.guess('李建国')
        self.assertIn(pred, ['1960s', '1970s', '1980s'])

    def test_younger_name(self):
        pred, _, _ = self.g.guess('张宇轩')
        self.assertIn(pred, ['1990s', '2000s'])

    def test_probs_sum_to_one(self):
        _, _, all_p = self.g.guess('王伟')
        self.assertAlmostEqual(sum(all_p.values()), 1.0, places=4)

    def test_empty(self):
        self.assertEqual(self.g.guess('')[0], '未知')

    def test_mode_consistency(self):
        a, _, _ = self.g.guess('王伟', 'auto')
        c, _, _ = self.g.guess('伟', 'namec')
        self.assertEqual(a, c)


class _DistModelTestBase:
    """人名级模型公共测试"""
    module = None
    label = None
    valid = None

    @classmethod
    def setUpClass(cls):
        cls.g = cls.module._guesser

    def test_valid_label(self):
        for name in ['王伟', '刘亦菲', '李建国']:
            pred, _, _ = self.g.guess(name)
            self.assertIn(pred, self.valid)

    def test_probs_sum_to_one(self):
        _, _, all_p = self.g.guess('王伟')
        if all_p:
            self.assertAlmostEqual(sum(all_p.values()), 1.0, places=4)

    def test_empty(self):
        self.assertEqual(self.g.guess('')[0], '未知')

    def test_never_unknown_for_known_chars(self):
        """字符级回退保证有预测"""
        pred, prob, _ = self.g.guess('张晓', 'auto')
        self.assertNotEqual(pred, '未知')
        self.assertGreater(prob, 0)


class TestZodiacGuesser(_DistModelTestBase, unittest.TestCase):
    label = 'zodiac'

    @classmethod
    def setUpClass(cls):
        import namecore.zodiac as m
        cls.module = m
        cls.valid = m.ZODIACS
        super().setUpClass()


class TestSeasonGuesser(_DistModelTestBase, unittest.TestCase):
    label = 'season'

    @classmethod
    def setUpClass(cls):
        import namecore.season as m
        cls.module = m
        cls.valid = m.SEASONS
        super().setUpClass()


class TestSolarGuesser(_DistModelTestBase, unittest.TestCase):
    label = 'solar'

    @classmethod
    def setUpClass(cls):
        import namecore.solar as m
        cls.module = m
        cls.valid = m.SOLAR_TERMS
        super().setUpClass()


class TestPriors(unittest.TestCase):

    def test_gender_priors(self):
        from namecore.gender import GenderGuesser
        g = GenderGuesser()
        self.assertAlmostEqual(sum(g.PRIORS.values()), 1.0)

    def test_decade_priors(self):
        from namecore.decade import DecadeGuesser
        self.assertAlmostEqual(sum(DecadeGuesser.PRIORS.values()), 1.0)

    def test_zodiac_priors(self):
        from namecore.zodiac import ZodiacGuesser
        self.assertAlmostEqual(sum(ZodiacGuesser.PRIORS.values()), 1.0, places=2)

    def test_season_priors(self):
        from namecore.season import SeasonGuesser
        self.assertAlmostEqual(sum(SeasonGuesser.PRIORS.values()), 1.0, places=2)

    def test_solar_priors(self):
        from namecore.solar import SolarGuesser
        self.assertAlmostEqual(sum(SolarGuesser.PRIORS.values()), 1.0, places=3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
