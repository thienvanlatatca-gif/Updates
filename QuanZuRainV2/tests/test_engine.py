import unittest
from rainloop.engine import (
    piecewise_linear_expr, brightness_expr, RenderConfig,
    curve_value_at, quantize_value, smart_brightness_schedule,
    db_volume_expr,
)

class EngineTests(unittest.TestCase):
    def test_piecewise_has_time(self):
        e=piecewise_linear_expr([0,10,0],100)
        self.assertIn('lt(t,50)',e)
        self.assertIn('lt(t,100)',e)

    def test_brightness_scales_percent(self):
        e=brightness_expr([0,-10],3600)
        self.assertIn('-0.1',e)

    def test_db_expr(self):
        e=db_volume_expr([-20,-10],3600)
        self.assertIn('pow(10,',e)

    def test_config_seconds_and_thunder(self):
        c=RenderConfig('a','b',duration_hours=8)
        self.assertEqual(c.duration_seconds,28800)
        self.assertEqual(len(c.thunder_curve_db), 9)

    def test_curve_value_at(self):
        self.assertAlmostEqual(curve_value_at([0,-10],100,50), -5.0)

    def test_quantize(self):
        self.assertEqual(quantize_value(-7.4, 1.0), -7.0)
        self.assertEqual(quantize_value(-7.6, 1.0), -8.0)

    def test_smart_schedule_uses_blocks(self):
        c=RenderConfig('a','b',duration_hours=1,brightness_curve_pct=[0,-2],apply_brightness=True,brightness_step_pct=1,block_seconds=60)
        levels, uniq=smart_brightness_schedule(c, source_duration=9.2)
        self.assertGreaterEqual(len(levels), 60)
        self.assertLessEqual(len(uniq), 3)

if __name__=='__main__': unittest.main()