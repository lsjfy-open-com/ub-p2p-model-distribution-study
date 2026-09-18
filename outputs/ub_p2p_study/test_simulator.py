import unittest
import numpy as np
from simulator import Config, simulate, max_min_rates


class Tests(unittest.TestCase):
    def test_allocator_shared_source(self):
        np.testing.assert_allclose(max_min_rates([[0,1],[0,2]], np.array([10.,9.,9.])), [5,5])

    def test_allocator_redistributes(self):
        np.testing.assert_allclose(max_min_rates([[0,1],[0,2]], np.array([10.,2.,20.])), [2,8])

    def test_single_analytic(self):
        r = simulate(Config(n=8, size_gb=4, chunk_gb=1, policy="single", hop_delay_s=0))
        self.assertAlmostEqual(r["time_s"], 8*4/10)

    def test_multiple_seeds_analytic(self):
        r = simulate(Config(n=8,size_gb=4,chunk_gb=1,policy="multi",seeds=4,hop_delay_s=0))
        self.assertAlmostEqual(r["time_s"], 8*4/40)

    def test_p2p_conservation(self):
        r = simulate(Config(n=8,size_gb=4,chunk_gb=.5,hop_delay_s=0))
        self.assertAlmostEqual(r["source_gb"],4)
        self.assertAlmostEqual(r["peer_gb"],28)

    def test_one_peer(self):
        a = simulate(Config(n=1,size_gb=4,chunk_gb=1,hop_delay_s=0))
        b = simulate(Config(n=1,size_gb=4,chunk_gb=1,policy="single",hop_delay_s=0))
        self.assertAlmostEqual(a["time_s"],b["time_s"])

    def test_partial_last_chunk(self):
        r = simulate(Config(n=3,size_gb=1.1,chunk_gb=.4))
        self.assertAlmostEqual(r["source_gb"]+r["peer_gb"],3.3)

    def test_one_chunk_chain(self):
        r = simulate(Config(n=8,size_gb=4,chunk_gb=4,hop_delay_s=.1))
        self.assertAlmostEqual(r["time_s"],8*(4/10+.1))

    def test_pipeline_closed_form(self):
        c = Config(n=50,size_gb=10,chunk_gb=.25,hop_delay_s=.00002)
        r = simulate(c)
        self.assertAlmostEqual(r["time_s"], (40+50-1)*.25/10+50*.00002)

    def test_global_bottleneck(self):
        r = simulate(Config(n=8,size_gb=4,chunk_gb=.5,fabric_gbps=1,hop_delay_s=0))
        self.assertGreaterEqual(r["time_s"]+1e-8,32)

    def test_memory_bottleneck(self):
        r = simulate(Config(n=8,size_gb=4,chunk_gb=.5,memory_gbps=1,hop_delay_s=0))
        self.assertGreaterEqual(r["time_s"]+1e-8,4)

    def test_repeatable(self):
        c = Config(n=8,size_gb=2,ordering="random",random_seed=12,rack_size=2,rack_gbps=1)
        self.assertEqual(simulate(c),simulate(c))

class InputValidationTests(unittest.TestCase):
    def test_invalid_configuration_rejected(self):
        from dataclasses import replace
        cases = dict(n=0, rack_size=0, slots=1.5, seeds=True, random_seed=-1,
                     hop_delay_s=-1, source_memory_gbps=0, down_gbps=float("nan"),
                     size_gb=float("inf"), ordering="typo", root_mode="typo", policy="typo")
        for key, value in cases.items():
            with self.subTest(key=key), self.assertRaises(ValueError):
                simulate(replace(Config(), **{key: value}))

if __name__ == "__main__":
    unittest.main(verbosity=2)
