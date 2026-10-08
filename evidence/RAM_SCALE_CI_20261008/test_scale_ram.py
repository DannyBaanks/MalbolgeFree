import unittest
from scale_ram import costs, gate, parse_run, projections, verify_seed
from pathlib import Path

class ScaleTests(unittest.TestCase):
    def test_exact21_costs(self):
        c=costs(21)
        self.assertEqual(c['steps'],3486784402)
        self.assertFalse(c['dense_u32_supported'])
        self.assertEqual(c['hypothetical_source_array_min_bytes'],9*(3486784402+1000)+96)
        self.assertGreater(c['current_source_storage_min_bytes'],128*2**30)

    def test_no_go_before_allocation(self):
        g=gate(21,16*2**30,20*2**30,18*2**30)
        self.assertEqual(g['decision'],'NO_GO')
        self.assertIn('DENSE_U32_WIDTH_CEILING',g['reasons'])
        self.assertIn('CURRENT_STORAGE_MIN_ABOVE_BUDGET',g['reasons'])

    def test_larger_memory_still_cannot_enable_u32_21(self):
        self.assertIn('DENSE_U32_WIDTH_CEILING',gate(21,1024*2**30,20*2**30,1)['reasons'])

    def test_budget_and_disk_boundary(self):
        self.assertEqual(gate(20,16*2**30,8*2**30,7*2**30)['decision'],'GO')
        self.assertIn('TEMP_DISK_BELOW_8_GIB',gate(20,16*2**30,8*2**30-1,7*2**30)['reasons'])
        self.assertIn('PREDICTED_PEAK_ABOVE_BUDGET',gate(20,16*2**30,8*2**30,10*2**30)['reasons'])

    def test_projections_are_not_measurements(self):
        rows=projections()
        self.assertEqual([r['current_storage_gate_max'] for r in rows],[20]*4)
        self.assertEqual([r['hypothetical_wider_dense_storage_gate_max'] for r in rows],[20,20,21,21])
        self.assertTrue(all(r['status'].startswith('PROJECTION_ONLY') for r in rows))

    def test_seed_and_real20_event_parser(self):
        verify_seed()
        log=Path(__file__).resolve().parents[1]/'E20_GITHUB_RUN_20261008/e20.log'
        text=log.read_text()
        self.assertEqual(parse_run(text,20)['fields']['growth'],'10')
        with self.assertRaises(AssertionError):
            parse_run(text.replace('old_w=19 new_w=20','old_w=19 new_w=21'),20)

    def test_out_of_scope_width_rejected(self):
        for width in [10,61]:
            with self.assertRaises(ValueError): costs(width)

if __name__=='__main__': unittest.main()
