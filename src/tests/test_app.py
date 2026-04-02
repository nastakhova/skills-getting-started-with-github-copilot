"""Tests for the Activity Management API endpoints using AAA pattern"""
import pytest


class TestGetActivities:
    """Test GET /activities endpoint"""

    def test_get_all_activities(self, client):
        """
        GIVEN the API is running
        WHEN I request all activities
        THEN I should get a 200 response with all activities
        """
        # Arrange
        # (client fixture provides the test client)
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_activities_contain_required_fields(self, client):
        """
        GIVEN the API has activities stored
        WHEN I request all activities
        THEN each activity should have required fields
        """
        # Arrange
        # (client fixture provides the test client)
        expected_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        # Assert
        for field in expected_fields:
            assert field in activity, f"Missing required field: {field}"
        assert isinstance(activity["participants"], list)


class TestActivitySignup:
    """Test POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant(self, client):
        """
        GIVEN an empty activity slot
        WHEN a student signs up for an activity
        THEN the signup should succeed with a 200 response
        """
        # Arrange
        activity_name = "Gym Class"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in response.json()["message"]

    def test_signup_adds_participant_to_list(self, client):
        """
        GIVEN a student successfully signs up
        WHEN I retrieve the activity details
        THEN the student email should appear in the participants list
        """
        # Arrange
        activity_name = "Gym Class"
        email = "newstudent@mergington.edu"
        
        # Act
        client.post(f"/activities/{activity_name}/signup?email={email}")
        response = client.get("/activities")
        
        # Assert
        participants = response.json()[activity_name]["participants"]
        assert email in participants

    def test_signup_duplicate_prevents_double_registration(self, client):
        """
        GIVEN a student already signed up for an activity
        WHEN the same student tries to sign up again
        THEN the second signup should fail with a 400 response
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        # First signup
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Act
        response_duplicate = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response_duplicate.status_code == 400
        assert "already signed up" in response_duplicate.json()["detail"]

    def test_signup_nonexistent_activity(self, client):
        """
        GIVEN an activity does not exist
        WHEN a student tries to sign up for it
        THEN the request should fail with a 404 response
        """
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_with_existing_participant(self, client):
        """
        GIVEN a student is already signed up for an activity
        WHEN that student tries to sign up again
        THEN the request should fail with a 400 response
        """
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={existing_email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]


class TestActivityUnregister:
    """Test DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant(self, client):
        """
        GIVEN a student is signed up for an activity
        WHEN the student is unregistered
        THEN the unregister should succeed with a 200 response
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_removes_participant_from_list(self, client):
        """
        GIVEN a student is signed up for an activity
        WHEN the student is unregistered
        THEN the student should be removed from the participants list
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        client.delete(f"/activities/{activity_name}/unregister?email={email}")
        response = client.get("/activities")
        
        # Assert
        participants = response.json()[activity_name]["participants"]
        assert email not in participants

    def test_unregister_nonexistent_activity(self, client):
        """
        GIVEN an activity does not exist
        WHEN attempting to unregister from it
        THEN the request should fail with a 404 response
        """
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_nonexistent_participant(self, client):
        """
        GIVEN a student is not signed up for an activity
        WHEN attempting to unregister that student
        THEN the request should fail with a 400 response
        """
        # Arrange
        activity_name = "Chess Club"
        email = "notreal@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_twice_fails(self, client):
        """
        GIVEN a student has been unregistered from an activity
        WHEN attempting to unregister the same student again
        THEN the second unregister should fail with a 400 response
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        # First unregister succeeds
        client.delete(f"/activities/{activity_name}/unregister?email={email}")
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]


class TestActivityFullWorkflow:
    """Test complete signup and unregister workflow"""

    def test_full_signup_and_unregister_workflow(self, client):
        """
        GIVEN a student and an available activity
        WHEN the student signs up, then later unregisters
        THEN the activity state should reflect both operations correctly
        """
        # Arrange
        email = "workflow@mergington.edu"
        activity_name = "Programming Class"
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert - Signup succeeded
        assert signup_response.status_code == 200
        
        # Act - Verify signup
        activities_after_signup = client.get("/activities")
        
        # Assert - Participant appears in list
        assert email in activities_after_signup.json()[activity_name]["participants"]
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert - Unregister succeeded
        assert unregister_response.status_code == 200
        
        # Act - Verify unregister
        activities_after_unregister = client.get("/activities")
        
        # Assert - Participant removed from list
        assert email not in activities_after_unregister.json()[activity_name]["participants"]

    def test_signup_different_activities(self, client):
        """
        GIVEN a student and multiple activities
        WHEN the student signs up for different activities
        THEN the student should appear in all activities' participant lists
        """
        # Arrange
        email = "multiactivity@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Gym Class"]
        
        # Act - Sign up for multiple activities
        for activity_name in activities_to_join:
            client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert - Verify in all activities
        response = client.get("/activities")
        data = response.json()
        for activity_name in activities_to_join:
            assert email in data[activity_name]["participants"]
