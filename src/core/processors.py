import hashlib, time

from core.blockchain.transaction import TransferTransaction, CoinbaseTransaction
from core.blockchain.block import Block

from core import consensus

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import App

class ProcessError(Exception):
    def __init__(self, message):
        super().__init__(message)

def validate_tx_timestamp(tx, check_for_block):
    now = int(time.time())
    if tx.timestamp > now:
        return False
    if now - tx.timestamp > 600 and not check_for_block:
        return False
    return True

def validate_block_timestamp(block, previous_block, max_future_offset=15):
    """
    Sprawdza czy timestamp bloku jest prawidłowy.
    - block.timestamp >= previous_block.timestamp
    - block.timestamp nie jest dalej niż max_future_offset sekund w przyszłość względem aktualnego czasu
    """
    import time
    now = int(time.time())
    
    if block.timestamp < previous_block.timestamp:
        return False
    
    if block.timestamp > now + max_future_offset:
        return False
    
    return True

def process_transfer_transaction(app: "App", tx: TransferTransaction, check_for_block = False):
    input_address = hashlib.sha3_256(hashlib.sha3_256(tx.input_public_key.encode()).digest()).digest()[:20]
    if not hashlib.sha3_256(tx.raw[32:]).digest() != tx.txid:
        raise ProcessError("Wrong TxID!")
    if not tx.verify_signature():
        raise ProcessError("Invalid Signature!")
    if not tx.version == app.blockchain.version:
        raise ProcessError("Version doesn't match!")
    if not tx.chain_id == app.blockchain.chain_id:
        raise ProcessError("Wrong ChainID!")
    if not validate_tx_timestamp(tx, check_for_block):
        raise ProcessError("Timestamp is in the future or Timestamp is too old!")
    if not tx.nonce == app.blockchain.state.get_address_nonce(input_address):
        raise ProcessError("Wrong Nonce!")
    if not tx.gas_limit >= tx.calculate_gas():
        raise ProcessError("Not enough gas!")
    if not app.blockchain.state.get_balance(input_address) >= tx.amount:
        raise ProcessError("Not enough funds!")
    
    if check_for_block:
        return True
    else:
        pass # Add tx to pool

def process_coinbase_transaction(app: "App", tx: CoinbaseTransaction):
    pass

def process_any_transaction(app: "App", tx):
    if isinstance(tx, TransferTransaction):
        process_transfer_transaction(app, tx, check_for_block=True)
    elif isinstance(tx, CoinbaseTransaction):
        process_coinbase_transaction(app, tx)

def process_block(app: "App", block: "Block"):
    if hashlib.sha3_256(block.raw[32:]).digest() != block.block_id:
        raise ProcessError("Wrong BlockID!")
    if not block.version == app.blockchain.version:
        raise ProcessError("Version doesn't match!")
    if not block.chain_id == app.blockchain.chain_id:
        raise ProcessError("Wrong ChainID!")
    if not validate_block_timestamp(block, app.blockchain.state.get_block()):
        raise ProcessError("Timestamp is in the future or Timestamp is too old!")
    if not block.height == app.blockchain.state.get_block().height + 1:
        raise ProcessError("Wrong Height!")
    if not block.max_gas == app.blockchain.state.max_gas:
        raise ProcessError("Wrong Max Gas!")
    if not block.difficulty == app.blockchain.state.get_difficulty():
        raise ProcessError("Wrong difficulty!")
    if not block.previous_hash == app.blockchain.state.get_block().block_id:
        raise ProcessError("Wrong Previous Hash!")
    
    if not consensus.verify(app, block):
        raise ProcessError("The block failed consensus rule validation!")
    
    process_coinbase_transaction(app, block.coinbase_transaction)

    for tx in block.transactions:
        process_any_transaction(app, tx)
    
    app.blockchain.add_block(block)