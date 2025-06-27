import hashlib, copy

from typing import TYPE_CHECKING
from core.const_config import COINBASE_DELAY, BLOCK_REWARD, MAX_GAS

from core.blockchain.transaction import TransferTransaction

from nacl.signing import VerifyKey

if TYPE_CHECKING:
    from core.blockchain.block import Block
    from core.blockchain.transaction import BaseTransaction
    from core.db_backend.base import BaseBackend

def public_key_to_address(pubkey: VerifyKey) -> bytes:
    return hashlib.sha3_256(hashlib.sha3_256(pubkey.encode()).digest()).digest()[:20]

class BlockchainState:
    def __init__(self, backend: "BaseBackend", blockchain: "Blockchain"):
        self._blockchain = blockchain
        self._backend = backend
        self.max_gas = MAX_GAS

        self._coinbase_queue = dict()

        self.set_block_reward(BLOCK_REWARD)
        self.state_height = 0
    
    def compute_state(self, blocks_num: int = 1):
        blocks_to_compute = self._blockchain._blocks[-blocks_num:]
        for block in blocks_to_compute:
            if TYPE_CHECKING:
                block = Block()
            
            self._set_block(block)
            self.state_height = block.height

            block.coinbase_transaction.output_address
            block.coinbase_transaction.reward
            self._backend.add_to_coinbase_queue(block.coinbase_transaction, block.height)
            gas_fee = 0
            for tx in block.transactions:
                if isinstance(tx, TransferTransaction):
                    fee = tx.gas_price * tx.calculate_gas()
                    gas_fee += fee

                    input_address = public_key_to_address(tx.input_public_key)
                    self.set_balance(input_address, self.get_balance(input_address) - (tx.amount + fee))
                    self.increment_address_nonce(input_address)
                    self.set_balance(tx.output_address, self.get_balance(tx.output_address) + tx.amount)
            if block.height - COINBASE_DELAY > 0:
                ready_coinbase_tx = self._backend.get_coinbase_transaction(block.height - COINBASE_DELAY)
                self.set_balance(ready_coinbase_tx.output_address, self.get_balance(ready_coinbase_tx.output_address) + ready_coinbase_tx.reward)

                self.set_balance(ready_coinbase_tx.output_address, self.get_balance(ready_coinbase_tx.output_address) + gas_fee)
    
    def get_chain_length(self) -> int:
        return len(self._blockchain._blocks)
    
    def get_difficulty(self) -> int:
        return self.get_block().difficulty

    def get_balance(self, address: bytes) -> int:
        return self._backend.get_balance(address)
    def set_balance(self, address: bytes, amount: int):
        self._backend.set_balance(address, amount)

    def get_address_nonce(self, address: bytes) -> int:
        return self._backend.get_address_nonce(address)
    def increment_address_nonce(self, address: bytes):
        self._backend.increment_address_nonce(address)

    def get_block(self) -> "Block":
        return self._backend.get_block()
    def _set_block(self, block: "Block"):
        self._backend.set_block(block)
    
    def get_block_reward(self) -> int:
        return self._backend.get_block_reward()
    def set_block_reward(self, new_reward: int):
        self._backend.set_block_reward(new_reward)
    
    def add_transaction(self, tx: "BaseTransaction"):
        self._backend.add_transaction(tx)
    def get_transactions(self, sort: str = "gas_price", limit: int = 0) -> list["BaseTransaction"]:
        return self._backend.get_transactions(sort, limit)
    
    def create_snapshot(self) -> "BlockchainState":
        state_snapshot = copy.deepcopy(self)
        state_snapshot._blockchain = None
        state_snapshot._backend._last_block = None
        return state_snapshot

class Blockchain:
    def __init__(self, backend, chain_id):
        self._blocks = list()
        self.state = BlockchainState(backend, self)
        self.chain_id = chain_id

    def new(self, **kwargs):
        self.version = kwargs.get("protocolVersion")
        genesis = kwargs.get("genesisBlock")
        initial_state = kwargs.get("initialState")
        if initial_state:
            self.state = copy.deepcopy(initial_state)
            self.state._blockchain = self

        self._blocks.append(genesis)
        self.state._set_block(genesis)
    
    def add_block(self, block: "Block"):
        self._blocks.append(block)
        self.state.compute_state(1)