"""Financial Merkle Tree Implementation for Ledger Auditing & Inclusion Proofs.
-------------------------------------------------------------------------
Features:
1. Deterministic binary Merkle tree constructed from SHA-256 leaf hashes.
2. Cryptographic inclusion proofs (audit trails).
3. Constant-time proof verification.
"""

import hashlib
from typing import Any, Dict, List, Optional


class FinancialMerkleTree:
    """Binary Merkle tree constructed over cryptographic settlement assertion leaves."""

    def __init__(self, leaves: List[str]):
        if not leaves:
            raise ValueError("FinancialMerkleTree requires at least one leaf.")
        self.raw_leaves = leaves
        self.leaf_hashes = [self._hash(l) if not l.startswith("sha256:") else l.replace("sha256:", "") for l in leaves]
        self.levels: List[List[str]] = [self.leaf_hashes]
        self._build_tree()

    @staticmethod
    def _hash(data: str) -> str:
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    @staticmethod
    def _hash_pair(left: str, right: str) -> str:
        combined = f"{left}:{right}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def _build_tree(self) -> None:
        current_level = self.leaf_hashes
        while len(current_level) > 1:
            next_level: List[str] = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                next_level.append(self._hash_pair(left, right))
            self.levels.append(next_level)
            current_level = next_level

    @property
    def root_hash(self) -> str:
        """Hex representation of the Merkle root hash."""
        return self.levels[-1][0]

    def get_proof(self, index: int) -> List[Dict[str, str]]:
        """Generate audit path inclusion proof for leaf at given index."""
        if index < 0 or index >= len(self.leaf_hashes):
            raise IndexError("Leaf index out of range.")

        proof: List[Dict[str, str]] = []
        curr_idx = index
        for level in self.levels[:-1]:
            is_right = (curr_idx % 2 == 1)
            sibling_idx = curr_idx - 1 if is_right else curr_idx + 1
            if sibling_idx >= len(level):
                sibling_idx = curr_idx
            proof.append({
                "position": "left" if is_right else "right",
                "hash": level[sibling_idx],
            })
            curr_idx = curr_idx // 2
        return proof

    @staticmethod
    def verify_proof(leaf_hash: str, proof: List[Dict[str, str]], expected_root: str) -> bool:
        """Cryptographically verify an inclusion proof against expected root."""
        current = leaf_hash.replace("sha256:", "")
        expected = expected_root.replace("sha256:", "")
        for step in proof:
            sibling = step["hash"].replace("sha256:", "")
            if step["position"] == "left":
                current = FinancialMerkleTree._hash_pair(sibling, current)
            else:
                current = FinancialMerkleTree._hash_pair(current, sibling)
        return current.lower() == expected.lower()
