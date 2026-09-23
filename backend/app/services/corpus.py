from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models import CorpusState


def bump_corpus_version(db: Session) -> None:
    statement = insert(CorpusState).values(id=1, version=1)
    db.execute(
        statement.on_conflict_do_update(
            index_elements=[CorpusState.id], set_={"version": CorpusState.version + 1}
        )
    )


def current_corpus_version(db: Session) -> int:
    return db.scalar(select(CorpusState.version).where(CorpusState.id == 1)) or 0
