import pytest
import os
import uuid
from datetime import datetime
from db.database import Database
from datamodels.datamodels import User


@pytest.fixture
def test_db():
    test_db_path = f"test_{uuid.uuid4()}.duckdb"
    db = Database(db_path=test_db_path)
    db.initialize_db()

    yield db

    db.close()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture
def sample_user():
    return User(uuid=str(uuid.uuid4()), email="test@example.com")


class TestDatabase:
    def test_database_initialization(self, test_db):
        assert test_db.con is not None

        tables = test_db.con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [table[0] for table in tables]

        assert "users" in table_names
        assert "history" in table_names

    def test_add_user_success(self, test_db, sample_user):
        result = test_db.add_user(sample_user)
        assert result is True

        fetched_user = test_db.get_user(sample_user.uuid)
        assert fetched_user is not None
        assert fetched_user.uuid == sample_user.uuid
        assert fetched_user.email == sample_user.email

    def test_add_duplicate_user(self, test_db, sample_user):
        test_db.add_user(sample_user)
        result = test_db.add_user(sample_user)
        assert result is False

    def test_add_user_duplicate_email(self, test_db, sample_user):
        test_db.add_user(sample_user)

        duplicate_email_user = User(uuid=str(uuid.uuid4()), email=sample_user.email)
        result = test_db.add_user(duplicate_email_user)
        assert result is False

    def test_get_user_not_found(self, test_db):
        result = test_db.get_user("nonexistent-uuid")
        assert result is None

    def test_add_history_entry(self, test_db, sample_user):
        test_db.add_user(sample_user)

        question = "What is 2+2?"
        response = "The answer is 4."
        image_url = "uploads/test.jpg"

        entry_id = test_db.add_history_entry(
            sample_user.uuid, question, response, image_url
        )

        assert entry_id is not None

        history = test_db.get_user_history(sample_user.uuid)
        assert len(history) == 1
        assert history[0]["question"] == question
        assert history[0]["response"] == response
        assert history[0]["image_url"] == image_url

    def test_add_history_entry_without_image(self, test_db, sample_user):
        test_db.add_user(sample_user)

        entry_id = test_db.add_history_entry(
            sample_user.uuid,
            "What is calculus?",
            "Calculus is a branch of mathematics.",
        )

        assert entry_id is not None

        history = test_db.get_user_history(sample_user.uuid)
        assert len(history) == 1
        assert history[0]["image_url"] is None

    def test_get_user_history_multiple_entries(self, test_db, sample_user):
        test_db.add_user(sample_user)

        entries = [
            ("Question 1", "Answer 1", "img1.jpg"),
            ("Question 2", "Answer 2", "img2.jpg"),
            ("Question 3", "Answer 3", None),
        ]

        for question, response, image_url in entries:
            test_db.add_history_entry(sample_user.uuid, question, response, image_url)

        history = test_db.get_user_history(sample_user.uuid)
        assert len(history) == 3

        assert history[0]["question"] == "Question 3"
        assert history[1]["question"] == "Question 2"
        assert history[2]["question"] == "Question 1"

    def test_get_user_history_limit(self, test_db, sample_user):
        test_db.add_user(sample_user)

        for i in range(10):
            test_db.add_history_entry(sample_user.uuid, f"Question {i}", f"Answer {i}")

        history = test_db.get_user_history(sample_user.uuid, limit=5)
        assert len(history) == 5

    def test_get_user_history_empty(self, test_db, sample_user):
        test_db.add_user(sample_user)

        history = test_db.get_user_history(sample_user.uuid)
        assert len(history) == 0

    def test_get_history_nonexistent_user(self, test_db):
        history = test_db.get_user_history("nonexistent-uuid")
        assert len(history) == 0

    def test_database_close(self, test_db):
        test_db.close()
        assert test_db.con is None

    def test_database_reconnect(self, test_db):
        test_db.close()
        test_db.connect()
        assert test_db.con is not None

    def test_history_timestamps(self, test_db, sample_user):
        test_db.add_user(sample_user)

        test_db.add_history_entry(sample_user.uuid, "Test question", "Test answer")

        history = test_db.get_user_history(sample_user.uuid)
        assert len(history) == 1
        assert history[0]["timestamp"] is not None

        timestamp_str = history[0]["timestamp"]
        datetime.fromisoformat(timestamp_str)
