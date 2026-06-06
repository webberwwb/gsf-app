"""Assert Python and JS business rules text stay in sync."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.order_business_rules import ORDER_PRICING_AND_POINTS_RULES, RULES_VERSION


def _normalize(text: str) -> str:
    return re.sub(r'\s+', ' ', text.strip())


def _load_js_rules() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, 'shared', 'order-pricing', 'businessRules.js')
    with open(path, encoding='utf-8') as f:
        content = f.read()
    match = re.search(
        r'export const ORDER_PRICING_AND_POINTS_RULES = `\n([\s\S]*?)`\s*\.trim\(\)',
        content,
    )
    if not match:
        raise AssertionError('Could not parse ORDER_PRICING_AND_POINTS_RULES from businessRules.js')
    return match.group(1).strip()


def _load_js_version() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, 'shared', 'order-pricing', 'businessRules.js')
    with open(path, encoding='utf-8') as f:
        content = f.read()
    match = re.search(r"export const RULES_VERSION = '([^']+)'", content)
    if not match:
        raise AssertionError('Could not parse RULES_VERSION from businessRules.js')
    return match.group(1)


def test_rules_version_parity():
    assert RULES_VERSION == _load_js_version()


def test_rules_text_parity():
    py = ORDER_PRICING_AND_POINTS_RULES.strip()
    js = _load_js_rules()
    assert _normalize(py) == _normalize(js), (
        'Python ORDER_PRICING_AND_POINTS_RULES differs from shared/order-pricing/businessRules.js'
    )


if __name__ == '__main__':
    test_rules_version_parity()
    test_rules_text_parity()
    print('business rules parity tests passed')
