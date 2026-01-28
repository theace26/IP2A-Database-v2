"""Security robustness tests for password hashing.

These tests verify that our password hashing implementation
is cryptographically secure and follows best practices.
"""

import time
from src.core.security import hash_password, verify_password


class TestPasswordHashingSecurity:
    """Tests to verify password hashing security properties."""

    def test_same_password_different_hashes(self):
        """
        Test that the same password produces different hashes (salt uniqueness).

        This verifies that each hash has a unique salt, preventing rainbow table attacks.
        """
        password = "SecurePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        hash3 = hash_password(password)

        # All hashes should be different
        assert hash1 != hash2
        assert hash1 != hash3
        assert hash2 != hash3

        # But all should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
        assert verify_password(password, hash3)

    def test_hash_format_is_bcrypt(self):
        """Test that hashes follow bcrypt format ($2b$)."""
        password = "TestPassword123"
        hash_result = hash_password(password)

        # bcrypt hashes start with $2b$ (bcrypt version identifier)
        assert hash_result.startswith("$2b$")

        # bcrypt hashes have the format: $2b$rounds$salt+hash
        parts = hash_result.split("$")
        assert len(parts) == 4  # ['', '2b', 'rounds', 'salt+hash']
        assert parts[1] == "2b"  # Version identifier
        assert parts[2] == "12"  # Cost factor (rounds)

    def test_hash_length_consistency(self):
        """Test that all hashes have consistent length (60 characters for bcrypt)."""
        passwords = [
            "short",
            "medium_length_password",
            "very_long_password_with_many_characters_1234567890!@#$%^&*()",
            "unicode_password_测试密码",
        ]

        for password in passwords:
            hash_result = hash_password(password)
            # bcrypt hashes are always 60 characters
            assert len(hash_result) == 60

    def test_computational_cost(self):
        """
        Test that hashing is computationally expensive (prevents brute force).

        With 12 rounds (2^12 = 4096 iterations), hashing should take
        at least 0.05 seconds to prevent rapid brute force attacks.
        """
        password = "TestPassword123"

        start_time = time.time()
        hash_password(password)
        duration = time.time() - start_time

        # Should take at least 50ms (0.05s) with 12 rounds
        # This prevents attackers from trying millions of passwords quickly
        assert (
            duration >= 0.05
        ), f"Hashing too fast ({duration}s), may be vulnerable to brute force"

    def test_wrong_password_fails(self):
        """Test that incorrect passwords always fail verification."""
        correct_password = "CorrectPassword123!"
        hash_result = hash_password(correct_password)

        wrong_passwords = [
            "WrongPassword123!",
            "correctpassword123!",  # Different case
            "CorrectPassword123",  # Missing character
            "CorrectPassword123! ",  # Extra space
            "",  # Empty
        ]

        for wrong_password in wrong_passwords:
            assert not verify_password(wrong_password, hash_result)

    def test_timing_attack_resistance(self):
        """
        Test that verification time is consistent (resists timing attacks).

        Verification should take similar time for correct and incorrect passwords
        to prevent attackers from using timing analysis to guess passwords.
        """
        password = "SecurePassword123!"
        hash_result = hash_password(password)

        # Time correct password verification
        correct_times = []
        for _ in range(5):
            start = time.time()
            verify_password(password, hash_result)
            correct_times.append(time.time() - start)

        # Time incorrect password verification
        incorrect_times = []
        for _ in range(5):
            start = time.time()
            verify_password("WrongPassword123!", hash_result)
            incorrect_times.append(time.time() - start)

        avg_correct = sum(correct_times) / len(correct_times)
        avg_incorrect = sum(incorrect_times) / len(incorrect_times)

        # Timing difference should be minimal (within 50%)
        # bcrypt is designed to have constant time comparison
        time_ratio = max(avg_correct, avg_incorrect) / min(avg_correct, avg_incorrect)
        assert time_ratio < 1.5, f"Timing difference too large: {time_ratio}x"

    def test_long_password_support(self):
        """Test that long passwords (up to 72 bytes) are supported."""
        # bcrypt has a 72-byte password limit
        # Test passwords of various lengths
        passwords = [
            "a" * 10,  # Short
            "a" * 50,  # Medium
            "a" * 72,  # Maximum for bcrypt
        ]

        for password in passwords:
            hash_result = hash_password(password)
            assert verify_password(password, hash_result)

    def test_special_characters_and_unicode(self):
        """Test that special characters and unicode are handled correctly."""
        passwords = [
            "!@#$%^&*()_+-=[]{}|;:',.<>?/",  # Special characters
            "测试密码123",  # Chinese characters
            "пароль123",  # Cyrillic
            "كلمة السر",  # Arabic
            "🔐🔑🛡️",  # Emojis
        ]

        for password in passwords:
            hash_result = hash_password(password)
            assert verify_password(password, hash_result)
            # Verify it doesn't match a different password
            assert not verify_password("different", hash_result)

    def test_hash_is_not_reversible(self):
        """
        Test that you cannot derive the password from the hash.

        This is a philosophical test - bcrypt hashes should not contain
        any recognizable patterns from the original password.
        """
        password = "MySecretPassword123!"
        hash_result = hash_password(password)

        # The hash should not contain the password
        assert password not in hash_result
        assert password.lower() not in hash_result.lower()

        # The hash should not contain obvious patterns
        assert "MySecret" not in hash_result
        assert "Password" not in hash_result
        assert "123" not in hash_result  # Except possibly in the cost factor

    def test_empty_password_handling(self):
        """Test that empty passwords are handled (though should be prevented by validation)."""
        # Empty passwords should technically work with bcrypt,
        # but application validation should prevent this
        empty_password = ""
        hash_result = hash_password(empty_password)

        # Should still hash and verify correctly
        assert verify_password(empty_password, hash_result)
        # But should not match a non-empty password
        assert not verify_password("a", hash_result)

    def test_whitespace_sensitivity(self):
        """Test that passwords are whitespace-sensitive."""
        passwords_with_whitespace = [
            ("password", "password "),  # Trailing space
            ("password", " password"),  # Leading space
            ("password", "pass word"),  # Middle space
            ("password", "password\n"),  # Newline
            ("password", "password\t"),  # Tab
        ]

        for pwd1, pwd2 in passwords_with_whitespace:
            hash1 = hash_password(pwd1)
            # Different passwords should not verify
            assert not verify_password(pwd2, hash1)


class TestPasswordHashingConfiguration:
    """Tests to verify password hashing configuration."""

    def test_bcrypt_rounds_are_12(self):
        """Verify that we're using 12 rounds (good security/performance balance)."""
        password = "TestPassword123"
        hash_result = hash_password(password)

        # Extract rounds from hash (format: $2b$12$...)
        rounds = hash_result.split("$")[2]
        assert rounds == "12", f"Expected 12 rounds, got {rounds}"

    def test_bcrypt_version_2b(self):
        """Verify we're using bcrypt version 2b (latest stable version)."""
        password = "TestPassword123"
        hash_result = hash_password(password)

        # Extract version from hash (format: $2b$...)
        version = hash_result.split("$")[1]
        assert version == "2b", f"Expected version 2b, got {version}"

    def test_deterministic_verification(self):
        """Test that verification is deterministic (same result every time)."""
        password = "TestPassword123"
        hash_result = hash_password(password)

        # Verify multiple times - should always return True
        for _ in range(10):
            assert verify_password(password, hash_result)

        # Verify with wrong password - should always return False
        for _ in range(10):
            assert not verify_password("WrongPassword", hash_result)


class TestPasswordHashingPerformance:
    """Tests to verify performance characteristics."""

    def test_hashing_performance_acceptable(self):
        """Test that hashing completes in reasonable time (< 1 second)."""
        password = "TestPassword123"

        start_time = time.time()
        hash_password(password)
        duration = time.time() - start_time

        # Should complete in less than 1 second for good user experience
        assert duration < 1.0, f"Hashing took {duration}s, too slow for production"

    def test_verification_performance_acceptable(self):
        """Test that verification completes in reasonable time (< 1 second)."""
        password = "TestPassword123"
        hash_result = hash_password(password)

        start_time = time.time()
        verify_password(password, hash_result)
        duration = time.time() - start_time

        # Should complete in less than 1 second for good user experience
        assert duration < 1.0, f"Verification took {duration}s, too slow for production"
