#!/usr/bin/env python

from web3 import Web3
import typer
import sys

def main(api_url: str):
    if not api_url.startswith("ws"):
        raise ValueError("api_url must be a websockets url")
    w3 = Web3(Web3.WebsocketProvider(api_url))

    print(w3.isConnected())

if __name__ == "__main__":
    typer.run(main)