"""Business-logic services extracted from api/main.py during the v1 refactor.

Services own the multi-step orchestration that doesn't belong in a route
handler: conflict detection, status transitions, background-task scheduling.
"""
