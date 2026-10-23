import { expect } from "chai";
import { ethers } from "hardhat";

const H = (s: string) => ethers.keccak256(ethers.toUtf8Bytes(s));

async function setup() {
  const [owner, agg, h1, h2, outsider] = await ethers.getSigners();
  const coord = await (await ethers.getContractFactory("SangamCoordinator")).deploy(agg.address);
  const reg = await (await ethers.getContractFactory("ReputationRegistry")).deploy(agg.address);
  await coord.registerParticipant(h1.address);
  await coord.registerParticipant(h2.address);
  return { coord, reg, owner, agg, h1, h2, outsider };
}

describe("SangamCoordinator", () => {
  it("runs a full round and emits the audit events", async () => {
    const { coord, agg, h1, h2 } = await setup();
    await expect(coord.connect(agg).openRound(H("m0"), "cid0"))
      .to.emit(coord, "RoundOpened").withArgs(1, H("m0"), "cid0");
    await expect(coord.connect(h1).submitUpdate(1, H("u1")))
      .to.emit(coord, "UpdateSubmitted").withArgs(1, h1.address, H("u1"));
    await coord.connect(h2).submitUpdate(1, H("u2"));
    await coord.connect(agg).commitGlobalModel(1, H("m1"), "cid1");
    await expect(coord.connect(agg).closeRound(1)).to.emit(coord, "RoundClosed").withArgs(1, 2);

    const r = await coord.getRound(1);
    expect(r.status).to.equal(3); // Closed
    expect(r.globalModelCid).to.equal("cid1");
    expect(await coord.updateOf(1, h1.address)).to.equal(H("u1"));
  });

  it("rejects unauthorised callers", async () => {
    const { coord, agg, h1, outsider } = await setup();
    await expect(coord.connect(outsider).registerParticipant(outsider.address)).to.be.revertedWithCustomError(coord, "NotOwner");
    await expect(coord.connect(h1).openRound(H("m0"), "c")).to.be.revertedWithCustomError(coord, "NotAggregator");
    await coord.connect(agg).openRound(H("m0"), "c");
    await expect(coord.connect(outsider).submitUpdate(1, H("u"))).to.be.revertedWithCustomError(coord, "NotParticipant");
  });

  it("blocks duplicate submissions and zero hashes", async () => {
    const { coord, agg, h1 } = await setup();
    await coord.connect(agg).openRound(H("m0"), "c");
    await expect(coord.connect(h1).submitUpdate(1, ethers.ZeroHash)).to.be.revertedWithCustomError(coord, "EmptyHash");
    await coord.connect(h1).submitUpdate(1, H("u"));
    await expect(coord.connect(h1).submitUpdate(1, H("u2"))).to.be.revertedWithCustomError(coord, "AlreadySubmitted");
  });

  it("rejects duplicate participant registration and late submissions after aggregation", async () => {
    const { coord, agg, h1 } = await setup();
    await expect(coord.registerParticipant(h1.address)).to.be.revertedWithCustomError(coord, "AlreadyRegistered");
    await coord.connect(agg).openRound(H("m0"), "c");
    await coord.connect(agg).commitGlobalModel(1, H("m1"), "c1");
    await expect(coord.connect(h1).submitUpdate(1, H("late"))).to.be.revertedWithCustomError(coord, "RoundNotOpen");
  });

  it("enforces round lifecycle ordering", async () => {
    const { coord, agg, h1 } = await setup();
    await coord.connect(agg).openRound(H("m0"), "c");
    await expect(coord.connect(agg).openRound(H("m0"), "c")).to.be.revertedWithCustomError(coord, "PreviousRoundOpen");
    await expect(coord.connect(agg).closeRound(1)).to.be.revertedWithCustomError(coord, "GlobalModelNotCommitted");
    await coord.connect(agg).commitGlobalModel(1, H("m1"), "c1");
    expect((await coord.getRound(1)).status).to.equal(2); // Aggregated
    await expect(coord.connect(agg).openRound(H("m1"), "c1")).to.be.revertedWithCustomError(coord, "PreviousRoundOpen");
    await expect(coord.connect(agg).commitGlobalModel(1, H("m2"), "c2")).to.be.revertedWithCustomError(coord, "AlreadyCommitted");
    await coord.connect(agg).closeRound(1);
    await expect(coord.connect(h1).submitUpdate(1, H("late"))).to.be.revertedWithCustomError(coord, "RoundNotOpen");
    await coord.connect(agg).openRound(H("m1"), "c1");
    expect(await coord.currentRound()).to.equal(2);
  });
});

describe("ReputationRegistry", () => {
  it("starts at 0.5 and applies the 0.8/0.2 rule for honest rounds", async () => {
    const { reg, agg, h1, h2 } = await setup();
    expect(await reg.reputationOf(h1.address)).to.equal(5000);
    await reg.connect(agg).recordScores(1, [h1.address, h2.address], [8000, 8000]);
    // 0.8*5000 + 0.2*8000
    expect(await reg.reputationOf(h1.address)).to.equal(5600);
    expect(await reg.rewardOf(h1.address)).to.equal(8000);
  });

  it("halves reputation when a score is below half the round median", async () => {
    const { reg, agg, h1, h2, h3 } = await setupThree();
    await reg.connect(agg).recordScores(1, [h1.address, h2.address, h3.address], [9000, 9000, 1000]);
    expect(await reg.reputationOf(h3.address)).to.equal(2500); // 5000 / 2
    expect(await reg.reputationOf(h1.address)).to.equal(5800);
    await reg.connect(agg).recordScores(2, [h1.address, h2.address, h3.address], [9000, 9000, 9000]);
    expect(await reg.reputationOf(h3.address)).to.equal(3800); // slow recovery: 0.8*2500 + 0.2*9000
  });

  it("validates caller, range, duplicates and batch shape", async () => {
    const { reg, agg, h1 } = await setup();
    await expect(reg.connect(h1).recordScores(1, [h1.address], [1])).to.be.revertedWithCustomError(reg, "NotValidator");
    await expect(reg.connect(agg).recordScores(1, [h1.address], [10_001])).to.be.revertedWithCustomError(reg, "ScoreTooHigh");
    await expect(reg.connect(agg).recordScores(1, [h1.address], [])).to.be.revertedWithCustomError(reg, "LengthMismatch");
    await expect(reg.connect(agg).recordScores(1, [], [])).to.be.revertedWithCustomError(reg, "EmptyBatch");
    await reg.connect(agg).recordScores(1, [h1.address], [1]);
    await expect(reg.connect(agg).recordScores(1, [h1.address], [1])).to.be.revertedWithCustomError(reg, "AlreadyScored");
  });
});

async function setupThree() {
  const base = await setup();
  const h3 = (await ethers.getSigners())[5];
  return { ...base, h3 };
}
