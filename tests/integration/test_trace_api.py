from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_trace_address_route_works() -> None:
    res = client.get('/api/v1/trace/address/bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080')
    assert res.status_code == 200
    body = res.json()['data']
    assert body['no_custody'] is True
    assert body['advisory_not_legal_verdict'] is True
    assert body['not_consensus_proof'] is True
    assert body['trace_band'] in {'UNKNOWN', 'LOW'}
    assert body['limitations']
    assert 'trace_dna' in body
    assert 'confidence_ledger' in body
    assert 'factor_contributions' in body


def test_sensitive_inputs_rejected() -> None:
    assert client.get('/api/v1/trace/address/abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about').status_code == 400
    assert client.get('/api/v1/trace/address/xprv9s21ZrQH143K3abc').status_code == 400
    assert client.get('/api/v1/trace/address/0x742d35Cc6634C0532925a3b844Bc454e4438f44e').status_code == 400


def test_watchlist_and_sources_routes_work() -> None:
    post = client.post('/api/v1/trace/watchlist', json={'address': '1BoatSLRHtKNngkdXEeobR76b53LETtpyT', 'label': 'test'})
    assert post.status_code == 200
    assert client.get('/api/v1/trace/watchlist').status_code == 200
    assert client.get('/api/v1/trace/sources').status_code == 200


def test_origin_source_routes_work() -> None:
    analyzed = client.get('/api/v1/trace/address/1BoatSLRHtKNngkdXEeobR76b53LETtpyT')
    report_id = analyzed.json()['data']['id']
    assert client.get(f'/api/v1/trace/report/{report_id}/origin-passport').status_code == 200
    assert client.get(f'/api/v1/trace/report/{report_id}/source-summary').status_code == 200
    assert client.get(f'/api/v1/trace/report/{report_id}/provider-disagreement').status_code == 200
    assert client.get('/api/v1/trace/sources').status_code == 200
    assert client.get('/api/v1/trace/sources/baseline_scoring_engine').status_code == 200


def test_privacy_routes_work() -> None:
    analyzed = client.get('/api/v1/trace/address/1BoatSLRHtKNngkdXEeobR76b53LETtpyT')
    report_id = analyzed.json()['data']['id']
    assert client.get(f'/api/v1/trace/report/{report_id}/privacy-shield').status_code == 200
    assert client.get(f'/api/v1/trace/report/{report_id}/utxo-hygiene').status_code == 200
    assert client.get(f'/api/v1/trace/report/{report_id}/dust-radar').status_code == 200


def test_counterparty_and_payment_context_routes_work() -> None:
    analyzed = client.get('/api/v1/trace/address/1BoatSLRHtKNngkdXEeobR76b53LETtpyT')
    report_id = analyzed.json()['data']['id']
    assert client.get(f'/api/v1/trace/report/{report_id}/counterparty-lens').status_code == 200
    payload = {'address': '1BoatSLRHtKNngkdXEeobR76b53LETtpyT', 'amount_sats': 200000, 'direction': 'SEND'}
    assert client.post('/api/v1/trace/payment-context', json=payload).status_code == 200
    preview = client.post('/api/v1/trace/payment-intent/preview', json=payload)
    assert preview.status_code == 200
    assert preview.json()['data']['transaction_signing_performed'] is False
    assert preview.json()['data']['transaction_broadcast_performed'] is False
    assert client.post('/api/v1/trace/destination-review', json=payload).status_code == 200


def test_lite_endpoint_works_and_rejects_sensitive() -> None:
    ok = client.get('/api/v1/trace/lite/1BoatSLRHtKNngkdXEeobR76b53LETtpyT')
    assert ok.status_code == 200
    data = ok.json()['data']
    assert 'qr_payload' in data
    assert 'clipboard_payload' in data
    assert client.get('/api/v1/trace/lite/0x742d35Cc6634C0532925a3b844Bc454e4438f44e').status_code == 400
    assert client.get('/api/v1/trace/lite/abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about').status_code == 400
