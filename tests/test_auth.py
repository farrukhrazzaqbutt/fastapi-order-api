from fastapi import status


class TestAuth:
    def test_seed_admin_user(self, client):
        """Test seeding admin user"""
        response = client.post("/auth/seed")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "admin"
        assert "id" in data
        assert "created_at" in data

    def test_seed_admin_user_twice(self, client):
        """Test seeding admin user twice returns existing user"""
        # First seed
        response1 = client.post("/auth/seed")
        assert response1.status_code == status.HTTP_200_OK

        # Second seed should return same user
        response2 = client.post("/auth/seed")
        assert response2.status_code == status.HTTP_200_OK
        assert response1.json()["id"] == response2.json()["id"]

    def test_login_success(self, client):
        """Test successful login"""
        # Seed admin user first
        client.post("/auth/seed")

        response = client.post(
            "/auth/login", json={"username": "admin", "password": "admin"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post(
            "/auth/login", json={"username": "admin", "password": "wrongpassword"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        response = client.post(
            "/auth/login", json={"username": "nonexistent", "password": "password"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_register_user(self, client):
        """Test user registration"""
        response = client.post(
            "/auth/register", json={"username": "newuser", "password": "newpass123"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "newuser"
        assert "id" in data

    def test_register_duplicate_username(self, client):
        """Test registration with duplicate username"""
        # First registration
        client.post(
            "/auth/register", json={"username": "duplicate", "password": "pass123"}
        )

        # Second registration with same username
        response = client.post(
            "/auth/register", json={"username": "duplicate", "password": "pass123"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_short_password(self, client):
        """Test registration with short password"""
        response = client.post(
            "/auth/register", json={"username": "user", "password": "123"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_short_username(self, client):
        """Test registration with short username"""
        response = client.post(
            "/auth/register", json={"username": "ab", "password": "password123"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
