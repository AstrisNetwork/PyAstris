import hashlib

from core.blockchain.transaction import TransferTransaction, CoinbaseTransaction

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

        transaction_type_map = {
            TransferTransaction: 0
        }

        for i in self.transactions:
            raw_tx_length = len(i.raw)
            raw_tx_length_raw = raw_tx_length.to_bytes((raw_tx_length.bit_length() + 7) // 8 or 1, "big")
            raw_tx_length_raw_length_raw = len(raw_tx_length_raw).to_bytes(1, "big")

            raw_tx = raw_tx_length_raw_length_raw + raw_tx_length_raw + transaction_type_map[type(i)].to_bytes(1, "big") + i.raw
            transactions_raw += raw_tx
        
        raw_body = version_raw + chain_id_raw + timestamp_raw + height_raw + nonce_raw + max_gas_raw + difficulty_raw + previous_hash_raw + coinbase_transaction_raw + transactions_raw
        
        if return_body:
            return raw_body

        if not self.block_id:
            self.block_id = hashlib.sha3_256(raw_body).digest()
        
        self.raw = self.block_id + raw_body
    
    @staticmethod
    def from_raw(raw_block: bytes) -> "Block":
        offset = 0

        block_id = raw_block[offset:offset + 32]
        offset += 32

        version_raw = raw_block[offset:offset + 6]
        version_major = version_raw[0:2]
        version_minor = version_raw[2:4]
        version_patch = version_raw[4:6]
        version = "{}.{}.{}".format(
            int.from_bytes(version_major, "big"),
            int.from_bytes(version_minor, "big"),
            int.from_bytes(version_patch, "big")
        )
        offset += 6

        chain_id = int.from_bytes(raw_block[offset:offset + 2], byteorder="big")
        offset += 2

        timestamp = int.from_bytes(raw_block[offset:offset + 8], byteorder="big")
        offset += 8

        height = int.from_bytes(raw_block[offset:offset + 4], byteorder="big")
        offset += 4

        nonce = int.from_bytes(raw_block[offset:offset + 8], byteorder="big")
        offset += 8

        max_gas = int.from_bytes(raw_block[offset:offset + 32], byteorder="big")
        offset += 32

        difficulty = int.from_bytes(raw_block[offset:offset + 32], byteorder="big")
        offset += 32

        previous_hash = raw_block[offset:offset + 32]
        offset += 32

        coinbase_tx_raw = raw_block[offset:offset + 120]
        coinbase_transaction = CoinbaseTransaction.from_raw(coinbase_tx_raw)
        offset += 120

        transactions_raw = raw_block[offset:]

        transaction_type_map = {
            0: "transfer"
        }

        tx_offset = 0
        transactions = []
        while True:
            if tx_offset + offset >= len(raw_block):
                break

            length_of_lenght = transactions_raw[tx_offset]
            tx_offset += 1

            length = int.from_bytes(transactions_raw[tx_offset:tx_offset+length_of_lenght], "big")
            tx_offset += length_of_lenght

            if tx_offset + length > len(transactions_raw):
                raise ValueError("Nieprawidłowa długość transakcji – zbyt krótki surowy blok.")
            
            tx_raw = transactions_raw[tx_offset:tx_offset+length]
            tx_offset += length

            tx_type = int.from_bytes(tx_raw[0:1], "big")
            if tx_type not in transaction_type_map:
                raise ValueError(f"Nieznany typ transakcji: {tx_type}")

            if transaction_type_map[tx_type] == "transfer":
                tx = TransferTransaction.from_raw(tx_raw[1:])
            
            transactions.append(tx)
        
        return Block(
            block_id = block_id,
            version = version,
            chain_id = chain_id,
            timestamp = timestamp,
            height = height,
            nonce = nonce,
            max_gas = max_gas,
            difficulty = difficulty,
            previous_hash = previous_hash,
            coinbase_transaction = coinbase_transaction,
            transactions = transactions,
            raw = raw_block
        )