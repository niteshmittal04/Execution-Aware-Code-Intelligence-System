from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from pathlib import Path

from git import Repo

from backend.config.settings import AppConfig
from backend.utils.retry import retry_call


class RepositoryCloner:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def clone(self, repo_url: str, branch: str | None = None) -> Path:
        clone_root = Path(self.config.github.clone_dir).resolve()
        clone_root.mkdir(parents=True, exist_ok=True)
        repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        target_path = clone_root / repo_name

        if target_path.exists():
            return target_path

        def _clone() -> Path:
            kwargs: dict[str, str] = {}
            if branch:
                kwargs["branch"] = branch
            Repo.clone_from(repo_url, str(target_path), **kwargs)
            return target_path

        def _with_timeout() -> Path:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_clone)
                try:
                    return future.result(timeout=self.config.github.clone_timeout_seconds)
                except FuturesTimeoutError as exc:
                    raise TimeoutError("Repository clone timed out.") from exc

        return retry_call(
            fn=_with_timeout,
            attempts=self.config.runtime.retry_attempts,
            initial_backoff_seconds=self.config.runtime.retry_backoff_seconds,
            multiplier=self.config.runtime.retry_backoff_multiplier,
        )
