"""Real vs demo data isolation.

Demo role may only touch is_demo=True rows.
Office / staff never see demo catalog mixed into production boards.
"""

from __future__ import annotations

from app.models import Employee, Role


def is_demo_user(user: Employee) -> bool:
    return user.role == Role.demo


def wants_demo_rows(user: Employee) -> bool:
    """True → filter to demo sample rows; False → production rows only."""
    return is_demo_user(user)
