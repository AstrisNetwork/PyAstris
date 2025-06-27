from core.blockchain.block import Block
from core.blockchain.transaction import TransferTransaction

from core.processors import process_block, process_transfer_transaction

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import App

def init(app_object: "App"):
    global app
    app = app_object
    main()

handlers = {
    TransferTransaction: process_transfer_transaction,
    Block: process_block
}

def main():
    global app
    while True:
        message = app.incomingMessages.get()
        handler = handlers.get(type(message))
        if handler:
            handler(app, message)
        else:
            # opcjonalnie log lub raise
            print(f"Unknown message type: {type(message)}")