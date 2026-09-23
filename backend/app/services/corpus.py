from pymongo.database import Database

from app.db.mongo import CORPUS

CORPUS_KEY = "corpus"


def bump_corpus_version(db: Database) -> None:
    db[CORPUS].update_one({"_id": CORPUS_KEY}, {"$inc": {"version": 1}}, upsert=True)


def current_corpus_version(db: Database) -> int:
    state = db[CORPUS].find_one({"_id": CORPUS_KEY})
    return int(state["version"]) if state else 0
