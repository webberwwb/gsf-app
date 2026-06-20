#!/usr/bin/env python3
"""Run backend tests safely (SQLite in-memory). Never use prod MySQL."""
import os
import subprocess
import sys

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BACKEND_DIR)


def assert_safe_test_env():
    os.environ.setdefault('TESTING', '1')
    db_name = os.environ.get('MYSQL_DATABASE', '')
    if db_name == 'gsf_app' and os.environ.get('GSF_ALLOW_PROD_DB') != '1':
        print(
            'ERROR: MYSQL_DATABASE=gsf_app (prod). Tests use SQLite via TestConfig only.\n'
            'Unset MYSQL_DATABASE or use run_tests.py without overriding TestConfig.'
        )
        sys.exit(1)
    print('Using test database: sqlite:///:memory: (TestConfig)')


def main():
    assert_safe_test_env()
    os.chdir(BACKEND_DIR)
    sys.path.insert(0, BACKEND_DIR)

    # Parity (no DB)
    from test_order_business_rules_parity import test_rules_version_parity, test_rules_text_parity
    test_rules_version_parity()
    test_rules_text_parity()
    print('business rules parity: OK')

    # Pytest suite
    rc = subprocess.call(
        [sys.executable, '-m', 'pytest', 'tests/', '-q'],
        cwd=BACKEND_DIR,
    )
    if rc != 0:
        sys.exit(rc)

    # Shared JS tests (node --test)
    js_tests = [
        os.path.join(ROOT, 'shared', 'order-pricing', 'shipping.test.js'),
        os.path.join(ROOT, 'shared', 'order-pricing', 'orderPricing.test.js'),
    ]
    for path in js_tests:
        if os.path.isfile(path):
            rc = subprocess.call(['node', '--test', path], cwd=ROOT)
            if rc != 0:
                sys.exit(rc)

    print('All tests passed.')


if __name__ == '__main__':
    main()
