# steps to start Anatomy
# copy over StcPython from
# C:\Program Files (x86)\Spirent Communications\Spirent TestCenter 5.32\Spirent TestCenter Application\API\Python\StcPython.py
# os.environ['STC_PRIVATE_INSTALL_DIR'] = "C:\\Program Files (x86)\\Spirent Communications\\Spirent TestCenter 5.32\\Spirent TestCenter Application"

import sys
import fx2_10g_s16_2_ports_test_1 as StcTest

if __name__ == "__main__":
    if StcTest.init() == 'FAILED':
        sys.exit(1)
    else:
        sys.exit(0)