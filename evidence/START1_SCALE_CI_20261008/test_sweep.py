import unittest
from sweep import parse, python_case

ZERO_ENCRYPTION = '''LABEL boot_width=1 source_ascii_min=33 boot_word_max=2 source_cells_outside_boot_word=1002 classification=PARAMETRIC_ASCII_OUTSIDE_BOOT_WORD
RESULT target=1 status=MAX_STEPS steps=2 padwidth=1 growth=0 final_c=2 cells=1014 capacity=0 stdout_len=0 repr=dense
HASH source=8d7e9bb741f0e7ce9912959e1f0c6285dd7cb67068aac50306b642d0ff837eda stdout=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 final_d=2 encrypted=0 assisted=0
AUDIT width=1 fetches=2 fetched_cells_outside_word=2 encrypted_cells=0 encryption_results_outside_word=0
Maximum resident set size (kbytes): 2000
'''

class Start1Tests(unittest.TestCase):
    def test_legitimate_zero_encryption_in_small_word(self):
        r=parse(ZERO_ENCRYPTION,1)
        self.assertEqual(r['hashes']['encrypted'],'0')
        self.assertEqual(r['label']['classification'],'PARAMETRIC_ASCII_OUTSIDE_BOOT_WORD')

    def test_small_python_boot_width_and_growth(self):
        for target in range(1,6):
            r=python_case(target)
            self.assertEqual(r['padwidth'],target)
            self.assertEqual(r['growth'],target-1)
            self.assertEqual(r['final_c'],3**(target-1)+1)

    def test_tampered_label_is_rejected(self):
        with self.assertRaises(AssertionError):
            parse(ZERO_ENCRYPTION.replace('boot_word_max=2','boot_word_max=26'),1)

if __name__=='__main__': unittest.main()
