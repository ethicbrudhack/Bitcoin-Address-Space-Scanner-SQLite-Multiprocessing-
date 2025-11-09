# ⚡ Bitcoin Address Space Scanner (SQLite + Multiprocessing)

This Python project implements a **parallel Bitcoin private key scanner** that:
- Generates random private keys across a specified bit range  
- Derives all major Bitcoin address types (BIP44, BIP49, BIP84)  
- Checks each generated address against a **local SQLite database** (`addresses111.db`)  
- Logs all matching results (private keys, addresses, WIF formats) to a file  

> ⚠️ **Educational and research use only.**  
> This software is a cryptographic experiment to understand Bitcoin key/address structures — **not a wallet brute-forcer.**

---

## ⚙️ Features

✅ Multi-process scanning using Python’s `multiprocessing`  
✅ Live progress counter (threaded output)  
✅ Efficient SQLite address lookup  
✅ Support for all main Bitcoin derivation paths:
- **BIP44** → Legacy (`1...`)
- **BIP49** → P2SH-SegWit (`3...`)
- **BIP84** → Native SegWit (`bc1...`)
✅ WIF (compressed / uncompressed) key output  
✅ Memory usage and progress monitoring via `psutil`

---

## 📂 File Overview

| File | Description |
|------|--------------|
| `main.py` | The main scanning script |
| `addresses111.db` | SQLite database containing known Bitcoin addresses |
| `found_keys.txt` | Output file where matching private keys and addresses are stored |

---

## ⚙️ Database Structure

Your database `addresses111.db` must include a table named `addresses`:

```sql
CREATE TABLE addresses (
    address TEXT PRIMARY KEY
);
Populate it with known Bitcoin addresses you want to search for:

INSERT INTO addresses (address) VALUES ('1BoatSLRHtKNngkdXEeobR76b53LETtpyT');
INSERT INTO addresses (address) VALUES ('bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080');

🚀 How to Run
1️⃣ Install dependencies
pip install ecdsa bech32 psutil base58

2️⃣ Place addresses111.db in the same directory

Ensure your SQLite database file exists and contains valid Bitcoin addresses.

3️⃣ Run the scanner
python3 main.py

4️⃣ Set your search range

When prompted, choose the bit range for key generation — for example:

Enter BTC Puzzle range (e.g. 67–70):
From bit: 67
To bit: 70


The program will search random private keys in the range:

2^67 to 2^70


and check all derived Bitcoin addresses against your database.

🧩 How It Works
🔹 1. Private key generation

Keys are generated randomly within the specified range:

priv_key = random.randrange(2**start_bit, 2**end_bit)

🔹 2. Address derivation

Each key produces 6 addresses (3 compressed + 3 uncompressed):

Derivation	Type	Example
BIP44	Legacy	1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
BIP49	P2SH-SegWit	3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy
BIP84	Native SegWit	bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080
🔹 3. SQLite lookup

Each generated address is compared to the local SQLite database using:

cursor.execute("SELECT 1 FROM addresses WHERE address = ?", (address,))

🔹 4. Result logging

When a match is found:

The private key (in hex and WIF)

All derived addresses

Import strings for Electrum wallet
are saved to found_keys.txt.

Example log entry:

✅ HIT!
Private Key (hex): 0x1234abcd...
Private Key WIF compressed: Kx1234...
Private Key WIF uncompressed: 5Habc...

📥 Electrum import strings:
Legacy (P2PKH): 5Habc...
P2SH-SegWit (BIP49): p2wpkh-p2sh:Kx1234...
Native SegWit (BIP84): p2wpkh:Kx1234...

Compressed Addresses:
  BIP44: 1ABC...
  BIP49: 3XYZ...
  BIP84: bc1q...

🧮 Parallel Execution Model

The program runs multiple scanning processes concurrently:

[Main Thread] ──► spawns 5 processes ──► each scans a key subrange
       │
       ├── Thread: real-time counter update
       ├── Process 0 → range a₀–b₀
       ├── Process 1 → range a₁–b₁
       ├── ...
       └── Process 4 → range a₄–b₄


Each process:

Randomly jumps within its assigned range (jump_generator)

Derives addresses

Queries SQLite for matches

Logs results asynchronously

🧰 Configuration Parameters
Parameter	Default	Description
PROCESSES	5	Number of parallel scanning processes
OUTPUT_FILE	found_keys.txt	File to save matching keys
ADDRESS_DB	addresses111.db	SQLite database with addresses
EXTRA_PATHS	Predefined list	Common derivation paths (BIP44/49/84)
🧠 Performance Tips

Use SSD storage for your SQLite DB for faster lookups.

Keep the database indexed on the address column.

Run fewer processes (PROCESSES = 2–4) if RAM usage is high.

Increase randomness by running multiple scanners with different seeds.

🧩 Example Output
[Process 3] 🔥 Starting! PID=10794
[3] 🌐 Sample: 1FZbgi29cpjq2GjdwV8eyHuJJnkLtktZc5
⏱️ Total Checked: 482,190
💰 MATCH FOUND IN DATABASE!
🔑 Private Key: 0x46b3a94e5b9c...
Compressed: ('1ABC...', '3XYZ...', 'bc1q...')
Uncompressed: ('1DEF...', '3LMN...', 'bc1q...')
🎁 If this address has balance, please support my work with a 10% donation!
BTC donate: bc1q4nyq7kr4nwq6zw35pg0zl0k9jmdmtmadlfvqhr
------------------------------------------------------------

⚠️ Legal & Ethical Notice

⚠️ This project is intended for cryptographic education, testing, and research.
It does not and cannot feasibly brute-force Bitcoin private keys due to the size of the keyspace (2²⁵⁶).
Do not use it to target live wallets or third-party assets.

Use it only to:

Learn Bitcoin key/address generation

Verify address derivation paths (BIP44/49/84)

Experiment with local databases for blockchain analytics


BTC donation address: bc1q4nyq7kr4nwq6zw35pg0zl0k9jmdmtmadlfvqhr
