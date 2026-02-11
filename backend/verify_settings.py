import socket
import sys
import os

def check_postgres_port(host="localhost", port=5432):
    print(f"Checking connectivity to {host}:{port}...")
    try:
        with socket.create_connection((host, port), timeout=3):
            print("  [OK] Port is open.")
            return True
    except (socket.timeout, ConnectionRefusedError):
        print("  [ERROR] Port is closed or unreachable. Is Docker running?")
        return False
    except Exception as e:
        print(f"  [ERROR] Connection failed: {e}")
        return False

if __name__ == "__main__":
    if not check_postgres_port():
        print("Skipping tests because database is not reachable.")
        sys.exit(1)
    
    # Only import app after checking connectivity to avoid hanging
    print("Importing application...")
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        from app.auth import create_access_token
        from datetime import timedelta
        
        client = TestClient(app)

        print("Starting Verification Tests...")
        
        # Helper admin token
        def get_admin_token():
            return create_access_token(
                data={"sub": "admin@example.com", "role": "admin"},
                expires_delta=timedelta(minutes=30)
            )

        token = get_admin_token()
        headers = {"Authorization": f"Bearer {token}"}

        # --- Test Webhooks ---
        print("\n[TEST] Webhook CRUD")
        # Create
        wh_payload = {
            "url": "https://example.com/webhook",
            "events": ["shipment.created"],
            "is_active": True
        }
        res = client.post("/settings/webhooks/", json=wh_payload, headers=headers)
        if res.status_code == 200:
            wh = res.json()
            wh_id = wh["id"]
            print(f"  [PASS] Created: {wh_id}")
            
            # List
            res = client.get("/settings/webhooks/", headers=headers)
            webhooks = res.json()
            found_wh = [w for w in webhooks if w["id"] == wh_id]
            assert len(found_wh) > 0
            print(f"  [PASS] Listed new webhook")
            
            # Delete
            res = client.delete(f"/settings/webhooks/{wh_id}", headers=headers)
            assert res.status_code == 200
            print(f"  [PASS] Deleted")
        else:
            print(f"  [FAIL] Create returned {res.status_code}: {res.text}")

        # --- Test API Keys ---
        print("\n[TEST] API Keys CRUD")
        # Create
        key_payload = {
            "name": "Verification Key",
            "scopes": ["read:all"]
        }
        res = client.post("/settings/api-keys/", json=key_payload, headers=headers)
        if res.status_code == 200:
            key_data = res.json()
            key_id = key_data["id"]
            print(f"  [PASS] Created Key ID: {key_id}")
            print(f"  [INFO] Raw Key: {key_data['key']}")
            
            # List
            res = client.get("/settings/api-keys/", headers=headers)
            found = any(k["id"] == key_id for k in res.json())
            if found:
                print(f"  [PASS] Listed new key")
            else:
                print(f"  [FAIL] Key not found in list")
            
            # Revoke
            res = client.delete(f"/settings/api-keys/{key_id}", headers=headers)
            assert res.status_code == 200
            print(f"  [PASS] Revoked Key")
        else:
            print(f"  [FAIL] Create Key returned {res.status_code}: {res.text}")

        print("\nAll tests completed.")

    except ImportError as e:
        print(f"Import Error: {e}")
    except Exception as e:
        print(f"Execution Error: {e}")
        import traceback
        traceback.print_exc()
