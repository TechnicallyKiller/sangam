import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import "dotenv/config";

const { AMOY_RPC_URL, DEPLOYER_PRIVATE_KEY } = process.env;

const config: HardhatUserConfig = {
  solidity: {
    version: "0.8.24",
    settings: { optimizer: { enabled: true, runs: 200 } },
  },
  networks: {
    localhost: { url: "http://127.0.0.1:8545" },
    ...(AMOY_RPC_URL && DEPLOYER_PRIVATE_KEY
      ? { amoy: { url: AMOY_RPC_URL, accounts: [DEPLOYER_PRIVATE_KEY], chainId: 80002 } }
      : {}),
  },
};

export default config;
