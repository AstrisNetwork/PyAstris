import queue, threading

import nacl.signing

from core.const_config import CHAIN_ID

from utils.load_config import load_config
from core.blockchain.blockchain import Blockchain
from core.blockchain.block import Block

from core.db_backend.memory import MemoryBackend

from core import core

BACKEND_REGISTRY = {
    "memory": MemoryBackend,
}

class App:
    def __init__(self, config):
        self.config = config

        self.incomingMessages = queue.Queue()

        engine_name = config["db"]["engine"].lower()

        if engine_name not in BACKEND_REGISTRY:
            raise ValueError(f"Unsupported DB engine: {engine_name}")

        backend_class = BACKEND_REGISTRY[engine_name]
        backend = backend_class()
        
        self.blockchain = Blockchain(backend, CHAIN_ID)

config_path = "config.yml"

config = load_config(config_path)
app = App(config)

threading.Thread(target=core.init, args=(app,)).start()

import time, nacl, os

genesis_block = Block(
    block_id = None,
    version = "0.1.0",
    chain_id = 2,
    timestamp = int(time.time()),
    height = 0,
    nonce = 0,
    max_gas = 20,
    difficulty = 1,
    previous_hash = b"\x00"*32,
    coinbase_transaction = None,
    transactions = []
)
genesis_block.build_raw()

app.blockchain.new(**{
    "genesisBlock": genesis_block, # Wypełnić blok genezy
    "protocolVersion": "0.1.0"
})

print(app.blockchain._blocks[0].timestamp)
print("Max gas",genesis_block.max_gas, app.blockchain.state.max_gas)

genesis = app.blockchain.state.get_block()
import hashlib
private = nacl.signing.SigningKey.generate()
public_raw = private.verify_key.encode()
address = hashlib.sha3_256(hashlib.sha3_256(public_raw).digest()).digest()[:20]

from core.blockchain.transaction import CoinbaseTransaction

new_block = Block(
    block_id = None,
    version = "0.1.0",
    chain_id = 2,
    timestamp = int(time.time()),
    height = 1,
    nonce = 0,
    max_gas = 20,
    difficulty = app.blockchain.state.get_difficulty(),
    previous_hash = app.blockchain.state.get_block().block_id,
    coinbase_transaction = CoinbaseTransaction.new(
        version = "0.1.0",
        nonce = app.blockchain.state.get_address_nonce(address),
        reward = 10,
        output_address = address
    ),
    transactions = []
)

while True:
    raw_block = new_block.build_raw(True)
    h = int.from_bytes(hashlib.sha3_256(raw_block).digest(), "big")
    difficulty = app.blockchain.state.get_difficulty()
    max_target = 2**256 - 1

    # Oblicz target jako max_target // difficulty (czyli im trudniej, tym mniejszy target)
    target = max_target // difficulty

    if h <= target:
        break
    new_block.nonce += 1

new_block.build_raw()

app.incomingMessages.put(new_block)
print(app.blockchain._blocks, app.blockchain.state.get_balance(address))
print("Max gas",new_block.max_gas, app.blockchain.state.max_gas)



new_block = Block(
    block_id = None,
    version = "0.1.0",
    chain_id = 2,
    timestamp = int(time.time()),
    height = 2,
    nonce = 0,
    max_gas = 20,
    difficulty = app.blockchain.state.get_difficulty(),
    previous_hash = app.blockchain.state.get_block().block_id,
    coinbase_transaction = CoinbaseTransaction.new(
        version = "0.1.0",
        nonce = app.blockchain.state.get_address_nonce(b"\x12"*20),
        reward = 10,
        output_address = b"\x12"*20
    ),
    transactions = []
)

while True:
    raw_block = new_block.build_raw(True)
    h = int.from_bytes(hashlib.sha3_256(raw_block).digest(), "big")
    difficulty = app.blockchain.state.get_difficulty()
    max_target = 2**256 - 1

    # Oblicz target jako max_target // difficulty (czyli im trudniej, tym mniejszy target)
    target = max_target // difficulty

    if h <= target:
        break
    new_block.nonce += 1

new_block.build_raw()

print(new_block.height, app.blockchain.state.get_block().height)

app.incomingMessages.put(new_block)
time.sleep(2)
print(app.blockchain._blocks, app.blockchain.state._backend.__dict__)
print("Max gas",new_block.max_gas, app.blockchain.state.max_gas)







from core.blockchain.transaction import TransferTransaction




tx = TransferTransaction(
    version = "0.1.0",
    chain_id = 2,
    timestamp = int(time.time()),
    nonce = app.blockchain.state.get_address_nonce(address),
    gas_price = 2,
    gas_limit = 1,
    input_public_key = nacl.signing.VerifyKey(public_raw),
    output_address = b"\x12"*20,
    amount = 5
)

tx.build()
tx.sign(private)



new_block = Block(
    block_id = None,
    version = "0.1.0",
    chain_id = 2,
    timestamp = int(time.time()),
    height = 3,
    nonce = 0,
    max_gas = 20,
    difficulty = app.blockchain.state.get_difficulty(),
    previous_hash = app.blockchain.state.get_block().block_id,
    coinbase_transaction = CoinbaseTransaction.new(
        version = "0.1.0",
        nonce = app.blockchain.state.get_address_nonce(b"\x12"*20),
        reward = 10,
        output_address = b"\x12"*20
    ),
    transactions = [tx]
)

while True:
    raw_block = new_block.build_raw(True)
    h = int.from_bytes(hashlib.sha3_256(raw_block).digest(), "big")
    difficulty = app.blockchain.state.get_difficulty()
    max_target = 2**256 - 1

    # Oblicz target jako max_target // difficulty (czyli im trudniej, tym mniejszy target)
    target = max_target // difficulty

    if h <= target:
        break
    new_block.nonce += 1

new_block.build_raw()

print(new_block.height, app.blockchain.state.get_block().height)

app.incomingMessages.put(new_block)
time.sleep(2)
print(app.blockchain._blocks, app.blockchain.state._backend.__dict__)
print("Max gas",new_block.max_gas, app.blockchain.state.max_gas)