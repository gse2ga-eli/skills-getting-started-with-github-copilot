"""
Tests for the basic API endpoints and functionality.
"""

import pytest
from fastapi import status


class TestBasicEndpoints:
    """Test basic API endpoints."""

    def test_root_endpoint_redirects_to_static(self, client):
        """Test that root endpoint redirects to static index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert "/static/index.html" in response.headers["location"]

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all available activities."""
        response = client.get("/activities")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Check that we have expected activities
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        for activity in expected_activities:
            assert activity in data

    def test_activity_structure(self, client, reset_activities):
        """Test that each activity has the correct structure."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)
            
            # Check that max_participants is positive
            assert activity_data["max_participants"] > 0
            
            # Check that participants count doesn't exceed max
            assert len(activity_data["participants"]) <= activity_data["max_participants"]


class TestSignupEndpoint:
    """Test signup functionality."""

    def test_successful_signup(self, client, reset_activities):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_for_nonexistent_activity(self, client, reset_activities):
        """Test signup for an activity that doesn't exist."""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_duplicate_signup_prevention(self, client, reset_activities):
        """Test that students cannot sign up twice for the same activity."""
        email = "duplicate@mergington.edu"
        activity = "Chess Club"
        
        # First signup should succeed
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == status.HTTP_200_OK
        
        # Second signup should fail
        response2 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response2.json()
        assert data["detail"] == "Student already signed up"

    def test_signup_persists_in_activities_list(self, client, reset_activities):
        """Test that signup persists and appears in activities list."""
        email = "persistent@mergington.edu"
        activity = "Programming Class"
        
        # Sign up student
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == status.HTTP_200_OK
        
        # Check that student appears in activities list
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        assert email in activities_data[activity]["participants"]

    def test_multiple_students_can_signup(self, client, reset_activities):
        """Test that multiple different students can sign up for the same activity."""
        activity = "Science Club"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == status.HTTP_200_OK
        
        # Verify all students are registered
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        for email in emails:
            assert email in activities_data[activity]["participants"]


class TestUnregisterEndpoint:
    """Test unregister functionality."""

    def test_successful_unregister(self, client, reset_activities):
        """Test successful unregistration from an activity."""
        # First, sign up a student
        email = "temp@mergington.edu"
        activity = "Drama Club"
        
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == status.HTTP_200_OK
        
        # Then unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == status.HTTP_200_OK
        
        data = unregister_response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]

    def test_unregister_from_nonexistent_activity(self, client, reset_activities):
        """Test unregister from an activity that doesn't exist."""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_unregister_when_not_registered(self, client, reset_activities):
        """Test unregister when student is not registered for the activity."""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert data["detail"] == "Student is not registered for this activity"

    def test_unregister_removes_from_participants_list(self, client, reset_activities):
        """Test that unregister removes student from participants list."""
        # Use existing participant
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        # Verify student is initially registered
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity]["participants"]
        
        # Unregister student
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == status.HTTP_200_OK
        
        # Verify student is no longer in participants list
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity]["participants"]

    def test_signup_after_unregister(self, client, reset_activities):
        """Test that a student can sign up again after unregistering."""
        email = "rejoiner@mergington.edu"
        activity = "Art Workshop"
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == status.HTTP_200_OK
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == status.HTTP_200_OK
        
        # Sign up again
        signup_response2 = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response2.status_code == status.HTTP_200_OK
        
        # Verify student is registered
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity]["participants"]


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_special_characters_in_activity_name(self, client, reset_activities):
        """Test handling of special characters in activity names."""
        # Add a test activity with spaces (URL encoding test)
        response = client.post("/activities/Chess%20Club/signup?email=test@mergington.edu")
        assert response.status_code == status.HTTP_200_OK

    def test_special_characters_in_email(self, client, reset_activities):
        """Test handling of special characters in email addresses."""
        email = "test+tag@mergington.edu"
        activity = "Programming Class"
        
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == status.HTTP_200_OK

    def test_empty_email_parameter(self, client, reset_activities):
        """Test handling of empty email parameter."""
        response = client.post("/activities/Chess Club/signup?email=")
        # Should still work as the backend doesn't validate email format
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]

    def test_missing_email_parameter(self, client, reset_activities):
        """Test handling of missing email parameter."""
        response = client.post("/activities/Chess Club/signup")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY