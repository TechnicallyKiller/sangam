/** Operator access types. No simulated wallet provider or signing flow. */
export interface WalletProvider { id: string; name: string; hint: string }
export interface WalletAccount { address: string; label: string; balance: number }
