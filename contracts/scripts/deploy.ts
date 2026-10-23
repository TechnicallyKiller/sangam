import { ethers, network } from "hardhat";
import fs from "fs";
import path from "path";

/** Merge KEY=value pairs into an env file, creating it if needed. */
function upsertEnv(file: string, vars: Record<string, string>) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const lines = fs.existsSync(file) ? fs.readFileSync(file, "utf8").split("\n") : [];
  for (const [k, v] of Object.entries(vars)) {
    const i = lines.findIndex((l) => l.startsWith(`${k}=`));
    if (i >= 0) lines[i] = `${k}=${v}`;
    else lines.push(`${k}=${v}`);
  }
  fs.writeFileSync(file, lines.filter((l, i, a) => l !== "" || i < a.length - 1).join("\n") + "\n");
}

async function main() {
  const [deployer, aggregator] = await ethers.getSigners();
  // On a testnet there is one key; deployer doubles as aggregator.
  const aggAddr = (aggregator ?? deployer).address;

  const coord = await (await ethers.getContractFactory("SangamCoordinator")).deploy(aggAddr);
  const reg = await (await ethers.getContractFactory("ReputationRegistry")).deploy(aggAddr);
  await Promise.all([coord.waitForDeployment(), reg.waitForDeployment()]);

  const coordinator = await coord.getAddress();
  const registry = await reg.getAddress();
  console.log(`network      ${network.name}`);
  console.log(`coordinator  ${coordinator}`);
  console.log(`registry     ${registry}`);
  console.log(`aggregator   ${aggAddr}`);

  const root = path.resolve(__dirname, "../..");
  upsertEnv(path.join(root, "backend/.env"), {
    COORDINATOR_ADDRESS: coordinator,
    REGISTRY_ADDRESS: registry,
  });
  upsertEnv(path.join(root, "frontend/.env"), {
    VITE_COORDINATOR_ADDRESS: coordinator,
    VITE_REGISTRY_ADDRESS: registry,
  });
}

main().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
