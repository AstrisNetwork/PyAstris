from core.db_backend.base import BaseBackend
from typing import TYPE_CHECKING

import copy

if TYPE_CHECKING:
    from core.blockchain.block import Block
    from core.blockchain.transaction import BaseTransaction, CoinbaseTransaction

class MemoryBackend(BaseBackend):
    def __init__(self):
        self._balances = dict()
        self._addresses_nonce = dict()

        self._chain_vars = dict()

        self._transactions = list()
        self._coinbase_queue = dict()
    
    def add_to_coinbase_queue(self, coinbase_tx: "CoinbaseTransaction", height: int):
        self._coinbase_queue[height] = coinbase_tx
    def get_coinbase_transaction(self, height: int) -> "CoinbaseTransaction":
        coinbase_tx = self._coinbase_queue[height]
        del self._coinbase_queue[height]
        return coinbase_tx

    def get_balance(self, address: bytes) -> int:
        return self._balances.get(address, 0)
    def set_balance(self, address: bytes, amount: int):
        self._balances[address] = amount
    
    def get_address_nonce(self, address: bytes) -> int:
        return self._addresses_nonce.get(address, 0)
    def increment_address_nonce(self, address: bytes):
        self._addresses_nonce[address] = self._addresses_nonce.get(address, 0) + 1
    
    def set_block(self, block: "Block"):
        self._last_block = block
    def get_block(self) -> "Block":
        return self._last_block
    
    def get_block_reward(self) -> int:
        return self._chain_vars["reward"]
    def set_block_reward(self, new_reward: int):
        self._chain_vars["reward"] = new_reward
    
    def add_transaction(self, tx: "BaseTransaction"):
        self._transactions.append(tx)
    def get_transactions(self, sort: str = "gas_price", limit: int = 0) -> list["BaseTransaction"]:
        tx_list = copy.deepcopy(self._transactions)
        if sort == "gas_price":
            # Sortujemy rosnąco po gas_price — zmień reverse=True, jeśli chcesz malejąco
            tx_list.sort(key=lambda tx: tx.gas_price, reverse=True)
        # Jeśli limit > 0, przycinamy listę
        if limit > 0:
            tx_list = tx_list[:limit]
        return tx_list