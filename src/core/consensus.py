from typing import TYPE_CHECKING
import hashlib

if TYPE_CHECKING:
    from core.blockchain.block import Block
    from main import App

def verify(app: "App", block: "Block") -> bool:
    difficulty = app.blockchain.state.get_difficulty()
    max_target = 2**256 - 1

    # Oblicz target jako max_target // difficulty (czyli im trudniej, tym mniejszy target)
    target = max_target // difficulty

    # Załóżmy, że block.raw to bytes całego bloku (lub nagłówka), które należy zhashować
    block_hash_int = int.from_bytes(block.raw[:32], "big")

    if block_hash_int <= target:
        return True
    else:
        return False