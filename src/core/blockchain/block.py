import hashlib

class BlockError(Exception):
    def __init__(self, message):
        super().__init__(message)

class Block:
    def __init__(self, **kwargs):
        self.block_id = kwargs.get("block_id")
        self.version = kwargs.get("version")
        self.chain_id = kwargs.get("chain_id")
        self.timestamp = kwargs.get("timestamp")
        self.height = kwargs.get("height")
        self.nonce = kwargs.get("nonce")
        self.max_gas = kwargs.get("max_gas")
        self.difficulty = kwargs.get("difficulty")
        self.previous_hash = kwargs.get("previous_hash")
        self.coinbase_transaction = kwargs.get("coinbase_transaction")
        self.transactions = kwargs.get("transactions")
        self.raw = kwargs.get("raw")
    
    def build_raw(self, return_body = False):
        mmp_version = self.version.split(".")
        version_raw = int(mmp_version[0]).to_bytes(2, "big") + int(mmp_version[1]).to_bytes(2, "big") + int(mmp_version[2]).to_bytes(2, "big")
        chain_id_raw = int(self.chain_id).to_bytes(2, "big")
        timestamp_raw = int(self.timestamp).to_bytes(8, "big")
        height_raw = int(self.height).to_bytes(4, "big")
        nonce_raw = int(self.nonce).to_bytes(8, "big")
        max_gas_raw = int(self.max_gas).to_bytes(32, "big")
        difficulty_raw = int(self.difficulty).to_bytes(32, "big")
        previous_hash_raw = bytes(self.previous_hash)
        if self.coinbase_transaction:
            coinbase_transaction_raw = self.coinbase_transaction.raw
        else:
            coinbase_transaction_raw = b"\x00"*122
        transactions_raw = b""
        for i in self.transactions:
            raw_tx_length = len(i.raw)
            raw_tx_length_raw = raw_tx_length.to_bytes((raw_tx_length.bit_length() + 7) // 8 or 1, "big")
            raw_tx_length_raw_length_raw = len(raw_tx_length_raw).to_bytes(1, "big")

            raw_tx = raw_tx_length_raw_length_raw + raw_tx_length_raw + i.raw
            transactions_raw += raw_tx
        
        raw_body = version_raw + chain_id_raw + timestamp_raw + height_raw + nonce_raw + max_gas_raw + difficulty_raw + previous_hash_raw + coinbase_transaction_raw + transactions_raw
        
        if return_body:
            return raw_body

        if not self.block_id:
            self.block_id = hashlib.sha3_256(raw_body).digest()
        
        self.raw = self.block_id + raw_body