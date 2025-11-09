import os
import sys
import hashlib
import base58
import random
import sqlite3
import multiprocessing
import threading
import time
import ecdsa
import psutil
from bech32 import bech32_encode, convertbits

OUTPUT_FILE = "found_keys.txt"
ADDRESS_DB = "addresses111.db"
PROCESSES = 5

EXTRA_PATHS = [
    "44'/0'/0'/0/0", "44'/0'/0'/1/0", "44'/0'/1'/0/0", "44'/0'/1'/1/0",
    "49'/0'/0'/0/0", "49'/0'/0'/1/0", "49'/0'/1'/0/0", "49'/0'/1'/1/0",
    "84'/0'/0'/0/0", "84'/0'/0'/1/0", "84'/0'/1'/0/0", "84'/0'/1'/1/0",
    "44'/0'/0'/0/1", "44'/0'/0'/1/1", "49'/0'/0'/0/1", "49'/0'/0'/1/1",
    "84'/0'/0'/0/1", "84'/0'/0'/1/1", "84'/0'/1'/0/1", "84'/0'/1'/1/1",
    "44'/1'/0'/0/0", "49'/1'/0'/0/0", "84'/1'/0'/0/0"
]

def jump_generator(start, stop):
    while True:
        yield random.randrange(start, stop)

def private_key_to_wif(priv_key, compressed=True):
    pk_bytes = priv_key.to_bytes(32, 'big')
    if compressed:
        extended = b'\x80' + pk_bytes + b'\x01'
    else:
        extended = b'\x80' + pk_bytes
    checksum = hashlib.sha256(hashlib.sha256(extended).digest()).digest()[:4]
    wif = base58.b58encode(extended + checksum).decode()
    return wif

def private_key_to_addresses(priv_key):
    sk = ecdsa.SigningKey.from_secret_exponent(priv_key, curve=ecdsa.SECP256k1)
    vk = sk.verifying_key

    pubkey_bytes_compressed = (
        b'\x02' + vk.to_string()[:32] if vk.to_string()[63] % 2 == 0 else b'\x03' + vk.to_string()[:32]
    )
    pubkey_bytes_uncompressed = b'\x04' + vk.to_string()

    h160_comp = hashlib.new('ripemd160', hashlib.sha256(pubkey_bytes_compressed).digest()).digest()
    addr44_comp = base58.b58encode_check(b'\x00' + h160_comp).decode()
    redeem_script_comp = b'\x00\x14' + h160_comp
    redeem_script_hash_comp = hashlib.new('ripemd160', hashlib.sha256(redeem_script_comp).digest()).digest()
    addr49_comp = base58.b58encode_check(b'\x05' + redeem_script_hash_comp).decode()
    segwit_data_comp = [0] + convertbits(h160_comp, 8, 5, True)
    addr84_comp = bech32_encode('bc', segwit_data_comp)

    h160_uncomp = hashlib.new('ripemd160', hashlib.sha256(pubkey_bytes_uncompressed).digest()).digest()
    addr44_uncomp = base58.b58encode_check(b'\x00' + h160_uncomp).decode()
    redeem_script_uncomp = b'\x00\x14' + h160_uncomp
    redeem_script_hash_uncomp = hashlib.new('ripemd160', hashlib.sha256(redeem_script_uncomp).digest()).digest()
    addr49_uncomp = base58.b58encode_check(b'\x05' + redeem_script_hash_uncomp).decode()
    segwit_data_uncomp = [0] + convertbits(h160_uncomp, 8, 5, True)
    addr84_uncomp = bech32_encode('bc', segwit_data_uncomp)

    return {
        "compressed": (addr44_comp, addr49_comp, addr84_comp),
        "uncompressed": (addr44_uncomp, addr49_uncomp, addr84_uncomp),
        "wif": {
            "compressed": private_key_to_wif(priv_key, True),
            "uncompressed": private_key_to_wif(priv_key, False)
        }
    }

def address_exists_in_db(conn, address):
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM addresses WHERE address = ?", (address,))
    return cursor.fetchone() is not None

def search_process(a, b, counter, process_id, lock):
    print(f"[Process {process_id}] 🔥 Starting! PID={os.getpid()}")
    conn = sqlite3.connect(ADDRESS_DB)
    proc = psutil.Process(os.getpid())
    key_gen = jump_generator(a, b)
    local_counter = 0

    while True:
        priv_key = next(key_gen)
        addresses = private_key_to_addresses(priv_key)
        found = False

        for addr_type in addresses.values():
            if isinstance(addr_type, tuple):
                for addr in addr_type:
                    if address_exists_in_db(conn, addr):
                        found = True
                        break
            if found:
                break

        if found:
            print(f"\n💰 MATCH FOUND IN DATABASE!")
            print(f"🔑 Private Key: {hex(priv_key)}")
            print(f"Compressed: {addresses['compressed']}")
            print(f"Uncompressed: {addresses['uncompressed']}")
            print("🎁 If this address has balance, please support my work with a 10% donation!")
            print("BTC donate: bc1q4nyq7kr4nwq6zw35pg0zl0k9jmdmtmadlfvqhr")
            print("-" * 50)

            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write("✅ HIT!\n")
                f.write(f"Private Key (hex): {hex(priv_key)}\n")
                f.write(f"Private Key WIF compressed: {addresses['wif']['compressed']}\n")
                f.write(f"Private Key WIF uncompressed: {addresses['wif']['uncompressed']}\n")
                f.write(f"\n📥 Electrum import strings:\n")
                f.write(f"Legacy (P2PKH): {addresses['wif']['uncompressed']}\n")
                f.write(f"P2SH-SegWit (BIP49): p2wpkh-p2sh:{addresses['wif']['compressed']}\n")
                f.write(f"Native SegWit (BIP84): p2wpkh:{addresses['wif']['compressed']}\n\n")
                f.write(f"Compressed Addresses:\n  BIP44: {addresses['compressed'][0]}\n  BIP49: {addresses['compressed'][1]}\n  BIP84: {addresses['compressed'][2]}\n")
                f.write(f"Uncompressed Addresses:\n  BIP44: {addresses['uncompressed'][0]}\n  BIP49: {addresses['uncompressed'][1]}\n  BIP84: {addresses['uncompressed'][2]}\n")
                f.write("🎁 If this address has balance, please support my work with a 10% donation!\n")
                f.write("BTC donate: bc1q4nyq7kr4nwq6zw35pg0zl0k9jmdmtmadlfvqhr\n")
                f.write("------------------------------------------------------------\n\n")

        if local_counter % 10_000 == 0:
            print(f"[{process_id}] 🌐 Sample: {addresses['compressed'][0]}")

        with lock:
            counter.value += 1
        local_counter += 1

        if local_counter % 100_000 == 0:
            print(f"[{process_id}] 🔁 {counter.value} keys checked... RAM: {proc.memory_info().rss // 1024 ** 2} MB")

    conn.close()

def print_counter(counter, lock):
    while True:
        with lock:
            print(f"⏱️ Total Checked: {counter.value:,}", end='\r')
        time.sleep(1)

if __name__ == "__main__":
    print("🪙 If you find an address with a balance, please support my work with a 10% donation 🙏")
    print("BTC donate: bc1q4nyq7kr4nwq6zw35pg0zl0k9jmdmtmadlfvqhr\n")

    print("Enter BTC Puzzle range (e.g. 67–70):")
    start_bit = int(input("From bit: "))
    end_bit = int(input("To bit: "))
    a = 2 ** start_bit
    b = 2 ** end_bit
    print(f"🔎 Scanning addresses in range {a}–{b}...")

    manager = multiprocessing.Manager()
    counter = multiprocessing.Value('i', 0)
    lock = multiprocessing.Lock()
    processes = []

    thread = threading.Thread(target=print_counter, args=(counter, lock))
    thread.daemon = True
    thread.start()

    step = (b - a) // PROCESSES

    for i in range(PROCESSES):
        a_i = a + i * step
        b_i = a + (i + 1) * step if i < PROCESSES - 1 else b
        print(f"[Process {i}] Range: {a_i} → {b_i}")
        p = multiprocessing.Process(target=search_process, args=(a_i, b_i, counter, i, lock))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    print(f"\n✅ Done. Total keys checked: {counter.value:,}")
