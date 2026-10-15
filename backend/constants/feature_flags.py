"""Customer-app feature flags.

Audience is ``admins`` or ``all``. ``admins`` is visible only to a logged-in
admin. ``all`` is visible to guests and customers. Launch a flag by changing
its audience to ``all``.
"""

FEATURE_FLAGS = {
    'recipes': 'admins',
}


def is_enabled(name, user=None):
    audience = FEATURE_FLAGS.get(name)
    if audience == 'all':
        return True
    if audience == 'admins':
        return bool(user and user.is_admin)
    return False


def enabled_map(user=None):
    return {name: is_enabled(name, user) for name in FEATURE_FLAGS}
