import { AGGREGATOR_ADDRESS, HOSPITALS } from "./ledger";

export interface WalletProvider {
  id: string;
  name: string;
  hint: string;
}

export interface WalletAccount {
  address: string;
  label: string;
  balance: number;
}

export const PROVIDERS: WalletProvider[] = [
  { id: "metamask", name: "MetaMask", hint: "Browser extension" },
  { id: "walletconnect", name: "WalletConnect", hint: "Scan with a mobile wallet" },
  { id: "coinbase", name: "Coinbase Wallet", hint: "Extension or mobile" },
];

export const ACCOUNTS: WalletAccount[] = [
  { address: AGGREGATOR_ADDRESS, label: "Consortium aggregator", balance: 4.2184 },
  { address: HOSPITALS[0].address, label: HOSPITALS[0].name, balance: 1.0631 },
  { address: "0xE17b5a02C9d84F36a1B07c5e92D3f48A6b0C7d19", label: "Auditor", balance: 0.3 },
];

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

export async function requestAccounts(_provider: WalletProvider): Promise<WalletAccount[]> {
  await wait(900);
  return ACCOUNTS;
}

export async function signTransaction(): Promise<void> {
  await wait(1_100);
}
