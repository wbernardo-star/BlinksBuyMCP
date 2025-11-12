import os, requests

BASE = os.getenv("MOCK_API_BASE", "").rstrip("/")

def get_menu():
    r = requests.get(f"{BASE}/menu")
    r.raise_for_status()
    return r.json()

def create_order(item: str, quantity: int, address: str):
    payload = {"item": item, "quantity": quantity, "address": address}
    r = requests.post(f"{BASE}/orders", json=payload)
    r.raise_for_status()
    return r.json()

def get_order_status(order_id: str):
    r = requests.get(f"{BASE}/orders/{order_id}")
    r.raise_for_status()
    return r.json()
