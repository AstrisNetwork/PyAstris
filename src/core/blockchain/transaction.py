from nacl.signing import VerifyKey, SigningKey
from nacl.exceptions import BadSignatureError

from core.const_config import TRANSFER_GAS

import hashlib

class TransactionError(Exception):
    def __init__(self, message):
        super().__init__(message)

class BaseTransaction:
    def __init__(self):
        pass

class TransferTransaction(BaseTransaction):
    def __init__(self, **kwargs):
        self.txid = kwargs.get("txid")
        self.version = kwargs.get("version")
        self.chain_id = kwargs.get("chain_id")
        self.timestamp = kwargs.get("timestamp")
        self.nonce = kwargs.get("nonce")
        self.gas_price = kwargs.get("gas_price")
        self.gas_limit = kwargs.get("gas_limit")
        self.input_public_key = kwargs.get("input_public_key")
        self.output_address = kwargs.get("output_address")
        self.amount = kwargs.get("amount")
        self.signature = kwargs.get("signature")
        self.raw = kwargs.get("raw")
    
    def verify_signature(self) -> bool:
        message = self.raw[:-64]
        try:
            self.input_public_key.verify(message, self.signature)
            return True
        except BadSignatureError:
            return False

    def calculate_gas(self):
        return TRANSFER_GAS

    def build(self):
        mmp_version = self.version.split(".")
        version_raw = int(mmp_version[0]).to_bytes(2, "big") + int(mmp_version[1]).to_bytes(2, "big") + int(mmp_version[2]).to_bytes(2, "big")
        chain_id_raw = int(self.chain_id).to_bytes(2, "big")
        timestamp_raw = int(self.timestamp).to_bytes(8, "big")
        nonce_raw = int(self.nonce).to_bytes(32, "big")
        gas_price_raw = int(self.gas_price).to_bytes(32, "big")
        gas_limit_raw = int(self.gas_limit).to_bytes(32, "big")
        input_public_key_raw = bytes(self.input_public_key.encode())
        output_address_raw = bytes(self.output_address)
        amount_raw = int(self.amount).to_bytes(32, "big")

        raw_body = version_raw+chain_id_raw+timestamp_raw+nonce_raw+gas_price_raw+gas_limit_raw+input_public_key_raw+output_address_raw+amount_raw
        self.txid = hashlib.sha3_256(raw_body).digest()
        self.raw = raw_body + b"\x00"*64
    
    def sign(self, private: SigningKey):
        signature = private.sign(self.raw[:-64]).signature
        self.signature = signature
        self.raw = self.raw[:-64] + signature
    
    @staticmethod
    def new(**kwargs) -> "TransferTransaction":
        version = kwargs.get("version")
        chain_id = kwargs.get("chain_id")
        timestamp = kwargs.get("timestamp")
        nonce = kwargs.get("nonce")
        gas_price = kwargs.get("gas_price")
        gas_limit = kwargs.get("gas_limit")

        try:
            input_public_key_raw = kwargs.get("input_public_key")
            input_public_key = VerifyKey(input_public_key_raw)
        except Exception:
            raise TransactionError("Wrong Public Key format!")

        output_address = kwargs.get("output_address")
        amount = kwargs.get("amount")

        tx = TransferTransaction(
            version=version,
            chain_id=chain_id,
            timestamp=timestamp,
            nonce=nonce,
            gas_price=gas_price,
            gas_limit=gas_limit,
            input_public_key=input_public_key,
            output_address=output_address,
            amount=amount
        )
        tx.build()
        return tx
    
    @staticmethod
    def from_raw(raw: bytes) -> "TransferTransaction":
        if len(raw) != 320:
            raise ValueError(f"Nieprawidłowy rozmiar transakcji: {len(raw)} bajtów (oczekiwano 320)")

        offset = 0

        tx_id = raw[offset:offset + 32]
        offset += 32

        version_raw = raw[offset:offset + 6]
        version = "{}.{}.{}".format(
            int.from_bytes(version_raw[0:2], "big"),
            int.from_bytes(version_raw[2:4], "big"),
            int.from_bytes(version_raw[4:6], "big")
        )
        offset += 6

        chain_id = int.from_bytes(raw[offset:offset + 2], "big")
        offset += 2

        timestamp = int.from_bytes(raw[offset:offset + 8], "big")
        offset += 8

        nonce = int.from_bytes(raw[offset:offset + 32], "big")
        offset += 32

        gas_price = int.from_bytes(raw[offset:offset + 32], "big")
        offset += 32

        gas_limit = int.from_bytes(raw[offset:offset + 32], "big")
        offset += 32

        input_public_key = raw[offset:offset + 32]
        offset += 32

        output_address = raw[offset:offset + 20]
        offset += 20

        amount = int.from_bytes(raw[offset:offset + 32], "big")
        offset += 32

        sign = raw[offset:offset + 64]
        offset += 64

        return TransferTransaction(
            txid=tx_id,
            version=version,
            chain_id=chain_id,
            timestamp=timestamp,
            nonce=nonce,
            gas_price=gas_price,
            gas_limit=gas_limit,
            input_public_key=VerifyKey(input_public_key),
            output_address=output_address,
            amount=amount,
            sign=sign,
            raw=raw
        )

class CoinbaseTransaction(BaseTransaction):
    def __init__(self, **kwargs):
        self.txid = kwargs.get("txid")
        self.version = kwargs.get("version")
        self.nonce = kwargs.get("nonce")
        self.reward = kwargs.get("reward")
        self.output_address = kwargs.get("output_address")
        self.raw = kwargs.get("raw")
    
    @staticmethod
    def new(**kwargs):
        version = kwargs.get("version")
        nonce = kwargs.get("nonce")
        reward = kwargs.get("reward")
        output_address = kwargs.get("output_address")

        mmp_version = version.split(".")
        version_raw = int(mmp_version[0]).to_bytes(2, "big") + int(mmp_version[1]).to_bytes(2, "big") + int(mmp_version[2]).to_bytes(2, "big")
        nonce_raw = int(nonce).to_bytes(32, "big")
        reward_raw = int(reward).to_bytes(32, "big")
        output_address_raw = bytes(output_address)
        raw_body = version_raw + nonce_raw + reward_raw + output_address_raw
        tx_id = hashlib.sha3_256(raw_body).digest()

        return CoinbaseTransaction(txid = tx_id, version = version, nonce = nonce, reward = reward, output_address = output_address, raw = tx_id + raw_body)
    
    @staticmethod
    def from_raw(raw: bytes) -> "CoinbaseTransaction":
        if len(raw) != 122:
            raise ValueError(f"Nieprawidłowy rozmiar coinbase transakcji: {len(raw)} bajtów (oczekiwano 122)")

        offset = 0

        txid = raw[offset:offset + 32]
        offset += 32

        version_raw = raw[offset:offset + 6]
        version = "{}.{}.{}".format(
            int.from_bytes(version_raw[0:2], "big"),
            int.from_bytes(version_raw[2:4], "big"),
            int.from_bytes(version_raw[4:6], "big")
        )
        offset += 6

        nonce = int.from_bytes(raw[offset:offset + 32], "big")
        offset += 32

        reward = int.from_bytes(raw[offset:offset + 32], "big")
        offset += 32

        output_address = raw[offset:offset + 20]
        offset += 20

        return CoinbaseTransaction(
            txid=txid,
            version=version,
            nonce=nonce,
            reward=reward,
            output_address=output_address,
            raw=raw
        )