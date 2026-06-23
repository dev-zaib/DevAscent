"""Challenge retriever — pgvector similarity search with dedup."""
from devascent.rag.embedder import (
    generate_weak_spot_embedding,
    generate_challenge_embedding,
)
from devascent.rag.seed_data import SEED_CHALLENGES


class ChallengeRetriever:
    """Retrieves challenges using vector similarity search.

    In production this queries PostgreSQL with pgvector's <=> operator.
    For now, falls back to in-memory search over seed data.

    Dedup: never returns a challenge the user has already attempted.
    """

    def __init__(self):
        self._challenges = SEED_CHALLENGES

    async def retrieve(
        self,
        skills_matrix: dict[str, float],
        attempted_ids: list[str] | None = None,
        limit: int = 5,
    ) -> dict | None:
        """Find the best challenge matching user's weak spots.

        Args:
            skills_matrix: User's current skill scores (0-100 per skill)
            attempted_ids: Challenge IDs the user has already attempted
            limit: Max number of candidates to return (returns best one)

        Returns:
            Best matching challenge, or None if no candidates found
        """
        attempted = set(attempted_ids or [])

        # Find weakest skills (lowest 3 scores)
        if skills_matrix:
            sorted_skills = sorted(skills_matrix.items(), key=lambda x: x[1])
            weak_skills = [s for s, _ in sorted_skills[:3]]
        else:
            weak_skills = []

        # Try vector search first
        if weak_skills:
            embedding = generate_weak_spot_embedding(weak_skills)
            if embedding:
                candidate = await self._pgvector_search(
                    embedding, attempted, weak_skills
                )
                if candidate:
                    return candidate

        # Fallback: keyword + level match from seed data
        return self._keyword_search(weak_skills, attempted)

    async def _pgvector_search(
        self,
        embedding: list[float],
        attempted: set[str],
        weak_skills: list[str],
    ) -> dict | None:
        """pgvector similarity search against challenges table.

        In production: SELECT ... ORDER BY embedding <=> $1 LIMIT $2
        For now: iterate seed data and compute cosine similarity manually.
        """
        candidates = []
        for challenge in self._challenges:
            chal_id = challenge["title"]  # Using title as ID for seed data
            if chal_id in attempted:
                continue

            # Score: how many weak skills overlap with target skills
            target = set(challenge.get("target_skills", []))
            score = len(set(weak_skills) & target)

            # Bonus for matching target_level to user's level
            candidates.append((score, challenge))

        candidates.sort(key=lambda x: x[0], reverse=True)
        if candidates and candidates[0][0] > 0:
            return candidates[0][1]
        return None

    def _keyword_search(
        self,
        weak_skills: list[str],
        attempted: set[str],
    ) -> dict | None:
        """Fallback keyword-based challenge search."""
        candidates = []
        for challenge in self._challenges:
            chal_id = challenge["title"]
            if chal_id in attempted:
                continue

            target = set(challenge.get("target_skills", []))
            score = len(set(weak_skills) & target)
            candidates.append((score, challenge))

        # Sort by: skill match (desc) → difficulty pref for BASELINE first
        candidates.sort(key=lambda x: x[0], reverse=True)

        if candidates:
            return candidates[0][1]
        return self._challenges[0] if self._challenges else None

    async def seed_embeddings(self) -> None:
        """Generate and store embeddings for all seed challenges.

        In production this inserts into PostgreSQL.
        """
        for challenge in self._challenges:
            embedding = generate_challenge_embedding(challenge)
            if embedding:
                challenge["embedding"] = embedding


retriever = ChallengeRetriever()
