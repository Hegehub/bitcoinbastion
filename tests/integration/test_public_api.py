from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_public_landing_endpoint_works() -> None:
    r = client.get('/api/v1/public/landing')
    assert r.status_code == 200
    data = r.json()['data']
    assert data['platform_name'] == 'Bitcoin Bastion'
    assert data['production_readiness']['production_calibrated'] is False


def test_public_status_endpoint_works() -> None:
    r = client.get('/api/v1/public/status')
    assert r.status_code == 200
    assert r.json()['data']['production_calibrated'] is False


def test_public_roadmap_endpoint_works() -> None:
    r = client.get('/api/v1/public/roadmap')
    assert r.status_code == 200
    assert 'current_phase' in r.json()['data']


def test_public_stats_endpoint_works() -> None:
    r = client.get('/api/v1/public/stats')
    assert r.status_code == 200
    assert 'reports_generated' in r.json()['data']


def test_public_feature_catalog_includes_trace_features() -> None:
    r = client.get('/api/v1/public/features')
    assert r.status_code == 200
    names = {i['name'] for i in r.json()['data']}
    assert 'Lite Address Check' in names
    assert 'Proof Packets' in names


def test_public_trace_summary_and_safe_wording() -> None:
    created = client.get('/api/v1/trace/address/1BoatSLRHtKNngkdXEeobR76b53LETtpyT')
    report_id = created.json()['data']['id']
    r = client.get(f'/api/v1/public/trace/{report_id}/summary')
    assert r.status_code == 200
    data = r.json()['data']
    joined = ' '.join(data['safety_warnings'] + [data['risk_summary'], data['origin_summary'], data['privacy_summary']]).lower()
    for bad in ['clean', 'dirty', 'criminal', 'safe', 'guaranteed', 'approved']:
        assert bad not in joined
    assert 'internal' not in data
    assert 'audit' not in data
