// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title SangamCoordinator
/// @notice Coordinates federated learning rounds. Stores only commitments
///         (hashes and IPFS CIDs); model weights never touch the chain.
contract SangamCoordinator {
    enum RoundStatus { None, Open, Aggregated, Closed }

    struct Round {
        RoundStatus status;
        bytes32 startModelHash;
        string startModelCid;
        bytes32 globalModelHash;
        string globalModelCid;
        bool globalCommitted;
        uint256 updateCount;
    }

    address public owner;
    address public aggregator;
    uint256 public currentRound;

    mapping(address => bool) public isParticipant;
    mapping(uint256 => Round) private rounds;
    mapping(uint256 => mapping(address => bytes32)) public updateOf;

    event ParticipantRegistered(address indexed participant);
    event RoundOpened(uint256 indexed round, bytes32 modelHash, string cid);
    event UpdateSubmitted(uint256 indexed round, address indexed participant, bytes32 updateHash);
    event GlobalModelCommitted(uint256 indexed round, bytes32 modelHash, string cid);
    event RoundClosed(uint256 indexed round, uint256 updateCount);

    error NotOwner();
    error NotAggregator();
    error NotParticipant();
    error AlreadyRegistered();
    error RoundNotOpen();
    error PreviousRoundOpen();
    error AlreadySubmitted();
    error EmptyHash();
    error AlreadyCommitted();
    error GlobalModelNotCommitted();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    modifier onlyAggregator() {
        if (msg.sender != aggregator) revert NotAggregator();
        _;
    }

    constructor(address _aggregator) {
        owner = msg.sender;
        aggregator = _aggregator;
    }

    function registerParticipant(address p) external onlyOwner {
        if (isParticipant[p]) revert AlreadyRegistered();
        isParticipant[p] = true;
        emit ParticipantRegistered(p);
    }

    function openRound(bytes32 modelHash, string calldata cid) external onlyAggregator returns (uint256 id) {
        RoundStatus last = rounds[currentRound].status;
        if (last == RoundStatus.Open || last == RoundStatus.Aggregated) revert PreviousRoundOpen();
        id = ++currentRound;
        Round storage r = rounds[id];
        r.status = RoundStatus.Open;
        r.startModelHash = modelHash;
        r.startModelCid = cid;
        emit RoundOpened(id, modelHash, cid);
    }

    function submitUpdate(uint256 round, bytes32 updateHash) external {
        if (!isParticipant[msg.sender]) revert NotParticipant();
        Round storage r = rounds[round];
        if (r.status != RoundStatus.Open) revert RoundNotOpen();
        if (updateHash == bytes32(0)) revert EmptyHash();
        if (updateOf[round][msg.sender] != bytes32(0)) revert AlreadySubmitted();
        updateOf[round][msg.sender] = updateHash;
        r.updateCount++;
        emit UpdateSubmitted(round, msg.sender, updateHash);
    }

    function commitGlobalModel(uint256 round, bytes32 hash, string calldata cid) external onlyAggregator {
        Round storage r = rounds[round];
        if (r.status == RoundStatus.Aggregated) revert AlreadyCommitted();
        if (r.status != RoundStatus.Open) revert RoundNotOpen();
        if (hash == bytes32(0)) revert EmptyHash();
        r.globalModelHash = hash;
        r.globalModelCid = cid;
        r.globalCommitted = true;
        r.status = RoundStatus.Aggregated;
        emit GlobalModelCommitted(round, hash, cid);
    }

    function closeRound(uint256 round) external onlyAggregator {
        Round storage r = rounds[round];
        if (r.status == RoundStatus.Open) revert GlobalModelNotCommitted();
        if (r.status != RoundStatus.Aggregated) revert RoundNotOpen();
        r.status = RoundStatus.Closed;
        emit RoundClosed(round, r.updateCount);
    }

    function getRound(uint256 round) external view returns (Round memory) {
        return rounds[round];
    }
}
