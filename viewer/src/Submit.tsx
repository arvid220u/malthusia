import React, { useCallback, useRef, useEffect, useState } from "react";
import Map from "./Map";
import ControlPane from "./ControlPane";
import { RouteComponentProps } from "@gatsbyjs/reach-router";
import Web3 from 'web3';
import Hash from 'ipfs-only-hash';

async function mintNFT(name: string, code: string, account: string, w3: any) {
  const contract_source = await fetch("Malthusia.json").then(r => r.json());
  const contract_address = process.env.REACT_APP_MALTHUSIA_CONTRACT_ADDRESS;
  const contract = new w3.eth.Contract(contract_source.abi, contract_address);

  const nonce = await w3.eth.getTransactionCount(account, "latest");

  // we don't directly upload to ipfs for the user, but instead ask the user to do so on their own if they want to
  // TODO: send to server which uploads to pinata
  const metadata = {
    name,
    description: `Malthusia bot ${name}!`,
    image: "", // TODO: generate some nice art here
    code: await Hash.of(code)
  }
  const metadataHash = await Hash.of(JSON.stringify(metadata));
  const tokenURI = `ipfs://${metadataHash}`

  console.log(`Minting NFT for contract ${contract_address}`)

  const tx = {
    from: account,
    to: contract_address,
    nonce: nonce,
    gas: 500000,
    value: 10 ** 16,
    data: contract.methods.createRobot(account, tokenURI, name, code).encodeABI(),
  };

  const receipt = await w3.eth.sendTransaction(tx);
  return receipt;
}

async function mintNFTMetamask(name: string, code: string) {
  if ((window as any).ethereum) {
    // const accounts = await (window as any).ethereum.enable();
    // const provider = new Web3.providers.HttpProvider((window as any).ethereum);
    const w3 = new Web3((window as any).ethereum);
    const accounts = await w3.eth.getAccounts();
    return mintNFT(name, code, accounts[0], w3);
  } else {
    throw Error("No web3 wallet installed :(");
  }
}

function Submit(props: RouteComponentProps) {
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  const parseFile = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    const reader = new FileReader();
    let filename;
    if (e.target.files) {
      filename = e.target.files[0];
    } else {
      setError(`No file specified.`)
      return;
    }
    reader.onload = async (e: ProgressEvent<FileReader>) => {
      const text = e.target?.result;
      if (typeof text === 'string') {
        setCode(text);
      } else {
        setError(`couldn't read file ${filename}.`)
        return;
      }
    };
    reader.readAsText(filename);
  }, [setCode, setError]);

  const submit = useCallback(async () => {
    if (name.length === 0) {
      setError("please enter a name!");
      return;
    }
    if (code.length === 0) {
      setError("please submit your code!");
      return;
    }
    try {
      const receipt = await mintNFTMetamask(name, code);
      setStatus(`Success! ${receipt}`)
      console.log(receipt);
    } catch (e) {
      if (e instanceof Error) {
        setError(e.message);
      }
    }
  }, [name, code, setError]);

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-center text-lg font-bold">malthusia</h1>
      <div className="grid gap-4 mt-4">

        <div>
          <label>name: </label>
          <input className="border border-gray-500 rounded-sm" type='text' value={name} onChange={(e) => setName(e.target.value)}></input>
        </div>
        <div>
          <label>code (flattened): </label>
          <input type="file" onChange={(e) => parseFile(e)}></input>
        </div>
        <div>
          <button className="font-bold bg-blue-700 text-white rounded-md px-4 py-1" onClick={submit}>submit to ethereum</button>
        </div>
        <div className="text-red-700">
          <span>{error}</span>
        </div>
        <div className="bg-gray-100 overflow-x-scroll p-4">
          <code className="whitespace-pre">{code}</code>
        </div>
      </div>
    </div>
  );
}

export default Submit;
