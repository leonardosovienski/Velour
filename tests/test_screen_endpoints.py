from tests.test_tenancy import tenant_api, isolated_accounts, headers  # noqa: F401


def test_all_admin_screen_endpoints_are_available(tenant_api):
    api, factory, (a, _) = tenant_api
    endpoints = [
        '/auth/me', '/users', '/clients', f"/clients/{a['client']}", f"/clients/{a['client']}/briefing",
        '/professionals', f"/professionals/{a['professional']}/stats", f"/professionals/{a['professional']}/dashboard",
        '/services', '/service-categories', '/products', '/appointments',
        '/loyalty/overview', '/loyalty/transactions', '/referrals', '/referrals/ranking',
        '/dashboard/today', '/dashboard/kpis', '/dashboard/weekly-revenue', '/dashboard/alerts',
        '/reports/revenue', '/reports/clients', '/reports/loyalty-monthly', '/reports/referrals-monthly',
        '/billing/status', '/fiscal/config', '/fiscal/profile', '/fiscal/appointments', '/fiscal/documents',
        '/finance/overview?month=2026-09',
    ]
    for path in endpoints:
        result = api.get(path, headers=headers(a))
        assert result.status_code == 200, (path, result.status_code, result.text)
        result.json()
