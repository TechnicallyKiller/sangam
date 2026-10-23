// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title ReputationRegistry
/// @notice Stores per-round contribution scores (0..10000 bps), an asymmetric
///         reputation (quick to distrust, slow to trust) and cumulative reward points.
contract ReputationRegistry {
    uint256 public constant MAX_SCORE = 10_000;
    uint256 public constant INITIAL_REPUTATION = 5_000; // r_k = 0.5
    uint256 public constant KEEP_BPS = 8_000;           // r <- 0.8 r + 0.2 s

    address public owner;
    address public validator; // validator committee account that submits scores

    mapping(address => uint256) private reputation;
    mapping(address => uint256) private reward;
    mapping(address => bool) private seen;
    mapping(uint256 => mapping(address => uint256)) public scoreOf;
    mapping(uint256 => mapping(address => bool)) public scored;

    event ScoreRecorded(uint256 indexed round, address indexed participant, uint256 score, uint256 reputation);

    error NotValidator();
    error ScoreTooHigh();
    error AlreadyScored();
    error LengthMismatch();
    error EmptyBatch();

    constructor(address _validator) {
        owner = msg.sender;
        validator = _validator;
    }

    /// @notice Batched write of one round's scores; updates reputation by Eq. (4).
    function recordScores(uint256 round, address[] calldata ps, uint256[] calldata scores) external {
        if (msg.sender != validator) revert NotValidator();
        uint256 n = ps.length;
        if (n == 0) revert EmptyBatch();
        if (n != scores.length) revert LengthMismatch();

        uint256 threshold = _median(scores) / 2;

        for (uint256 i = 0; i < n; i++) {
            address p = ps[i];
            uint256 s = scores[i];
            if (s > MAX_SCORE) revert ScoreTooHigh();
            if (scored[round][p]) revert AlreadyScored();

            scored[round][p] = true;
            scoreOf[round][p] = s;

            uint256 r = seen[p] ? reputation[p] : INITIAL_REPUTATION;
            r = s < threshold ? r / 2 : (KEEP_BPS * r + (MAX_SCORE - KEEP_BPS) * s) / MAX_SCORE;
            seen[p] = true;
            reputation[p] = r;
            reward[p] += s;

            emit ScoreRecorded(round, p, s, r);
        }
    }

    function reputationOf(address p) external view returns (uint256) {
        return seen[p] ? reputation[p] : INITIAL_REPUTATION;
    }

    function rewardOf(address p) external view returns (uint256) {
        return reward[p];
    }

    /// @dev Median of a small batch (insertion sort on a memory copy); mean of the two middles when even.
    function _median(uint256[] calldata xs) private pure returns (uint256) {
        uint256 n = xs.length;
        uint256[] memory a = new uint256[](n);
        for (uint256 i = 0; i < n; i++) {
            uint256 v = xs[i];
            uint256 j = i;
            while (j > 0 && a[j - 1] > v) {
                a[j] = a[j - 1];
                j--;
            }
            a[j] = v;
        }
        return n % 2 == 1 ? a[n / 2] : (a[n / 2 - 1] + a[n / 2]) / 2;
    }
}
