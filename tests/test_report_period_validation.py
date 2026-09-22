import pytest
from tests.test_tenancy import tenant_api, isolated_accounts, headers  # noqa: F401


@pytest.mark.parametrize('path', ['/reports/revenue', '/reports/clients'])
@pytest.mark.parametrize('params', [
    {'period_start': 'invalid'},
    {'period_end': '2026-02-30'},
    {'period_start': '2026-09-01T00:00:00Z'},
    {'period_start': '2026-09-30', 'period_end': '2026-09-01'},
    {'period_start': '2026-09-01', 'period_end': '2026-09-01'},
])
def test_invalid_report_period_is_validation_error_not_server_error(tenant_api, path, params):
    api, factory, (account, _) = tenant_api
    assert api.get(path, params=params, headers=headers(account)).status_code == 422


def test_valid_local_report_period(tenant_api):
    api, factory, (account, _) = tenant_api
    result = api.get('/reports/revenue', params={'period_start': '2026-09-01', 'period_end': '2026-10-01'}, headers=headers(account))
    assert result.status_code == 200
    assert result.json()['period_start'] == '2026-09-01T00:00:00'
