from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from reddit_intelligence.config import RedditResearch, RelevanceResearch
from reddit_intelligence.db.repositories import InMemoryContentRepository, InMemoryRunRepository
from reddit_intelligence.processing.relevance import RelevanceScorer
from reddit_intelligence.reddit.collector import RedditCollector
from reddit_intelligence.reddit.deletion_sync import sync_deleted_content


def _build_collector(
    repo: InMemoryContentRepository,
    run_repo: InMemoryRunRepository | None = None,
) -> RedditCollector:
    scorer = RelevanceScorer(
        RelevanceResearch(
            minimum_text_length=10,
            minimum_rule_score=1,
            include_terms=["discover", "recommendation", "daily mix", "same songs"],
            exclude_terms=["giveaway"],
        )
    )
    return RedditCollector(
        repository=repo,
        relevance_scorer=scorer,
        max_comments_per_post=250,
        minimum_post_score=0,
        run_repository=run_repo,
    )


def test_collect_from_fixture_is_idempotent_and_merges_queries() -> None:
    repo = InMemoryContentRepository()
    run_repo = InMemoryRunRepository()
    collector = _build_collector(repo, run_repo=run_repo)
    posts_path = Path("data/fixtures/reddit_posts.json")
    comments_path = Path("data/fixtures/reddit_comments.json")

    first = collector.collect_from_fixture(posts_path, comments_path, matched_query="q1")
    second = collector.collect_from_fixture(posts_path, comments_path, matched_query="q2")

    assert first.posts_seen == 3
    assert first.comments_seen == 3
    assert repo.post_count() == 3
    assert repo.comment_count() == 3

    post = repo.get_post("p_fixture_001")
    assert post is not None
    assert post.relevance_score >= 1
    assert sorted(post.matched_queries) == ["q1", "q2"]
    assert second.posts_upserted == 3
    assert second.crawl_run_id is not None
    run = run_repo.get_crawl_run(second.crawl_run_id)
    assert run is not None
    assert run.status == "success"
    assert second.deleted_posts_detected >= 1

    deletion_sync = sync_deleted_content(repo, run_repository=run_repo, run_id=second.crawl_run_id)
    assert deletion_sync.deleted_posts_found >= 1
    assert deletion_sync.events_recorded >= 1


@dataclass
class FakeCommentForest:
    comments: list[object]

    def replace_more(self, limit: int = 0) -> None:
        assert limit == 0

    def list(self) -> list[object]:
        return self.comments


@dataclass
class FakeSubmission:
    id: str
    subreddit: str
    title: str
    selftext: str
    permalink: str
    score: int
    upvote_ratio: float
    num_comments: int
    created_utc: int
    comments: FakeCommentForest


class FakeSubreddit:
    def __init__(self, submissions: list[FakeSubmission]) -> None:
        self._submissions = submissions

    def search(
        self,
        query: str,
        sort: str,
        time_filter: str,
        limit: int,
    ) -> list[FakeSubmission]:
        del query, sort, time_filter, limit
        return self._submissions


class FakeAuth:
    limits = {"remaining": 88}


class FakeRedditClient:
    def __init__(self, submissions: list[FakeSubmission]) -> None:
        self._submissions = submissions
        self.auth = FakeAuth()

    def subreddit(self, name: str) -> FakeSubreddit:
        del name
        return FakeSubreddit(self._submissions)


def test_collect_incremental_captures_rate_limit_metadata() -> None:
    repo = InMemoryContentRepository()
    run_repo = InMemoryRunRepository()
    collector = _build_collector(repo, run_repo=run_repo)

    comment_payload = {
        "id": "c_live",
        "parent_id": "t3_p_live",
        "subreddit": "spotify",
        "body": "Recommendations are repetitive and frustrating.",
        "permalink": "/r/spotify/comments/p_live/c_live/",
        "score": 5,
        "depth": 0,
        "created_utc": 1719532800,
    }
    submissions = [
        FakeSubmission(
            id="p_live",
            subreddit="spotify",
            title="Daily Mix repeats songs",
            selftext="Need better recommendation quality.",
            permalink="/r/spotify/comments/p_live/post/",
            score=10,
            upvote_ratio=0.9,
            num_comments=1,
            created_utc=1719532800,
            comments=FakeCommentForest([comment_payload]),
        )
    ]
    research = RedditResearch(
        subreddits=["spotify"],
        search_queries=["daily mix"],
        time_filter="month",
        sort="new",
        posts_per_query=10,
        max_comments_per_post=10,
        minimum_post_score=0,
        refresh_active_posts_days=7,
    )
    metrics = collector.collect_incremental(
        reddit_client=FakeRedditClient(submissions),
        research=research,
    )
    assert metrics.rate_limit_remaining == 88.0
    assert metrics.posts_seen == 1
    assert metrics.comments_seen == 1
    assert metrics.crawl_run_id is not None
    run = run_repo.get_crawl_run(metrics.crawl_run_id)
    assert run is not None
    assert run.status == "success"


def test_fixture_files_remain_valid_json() -> None:
    posts = json.loads(Path("data/fixtures/reddit_posts.json").read_text(encoding="utf-8"))
    comments = json.loads(Path("data/fixtures/reddit_comments.json").read_text(encoding="utf-8"))
    assert isinstance(posts, list)
    assert isinstance(comments, list)
