"""
Integration tests for the complete application workflow.
"""

import pytest
from fastapi import status


class TestCompleteWorkflow:
    """Test complete user workflows and integration scenarios."""

    def test_complete_signup_and_unregister_workflow(self, client, reset_activities):
        """Test a complete workflow of signing up and then unregistering."""
        email = "workflow@mergington.edu"
        activity = "Basketball Club"
        
        # 1. Get initial activities state
        initial_response = client.get("/activities")
        initial_data = initial_response.json()
        initial_count = len(initial_data[activity]["participants"])
        
        # 2. Sign up for activity
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == status.HTTP_200_OK
        
        # 3. Verify signup in activities list
        after_signup_response = client.get("/activities")
        after_signup_data = after_signup_response.json()
        assert email in after_signup_data[activity]["participants"]
        assert len(after_signup_data[activity]["participants"]) == initial_count + 1
        
        # 4. Unregister from activity
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == status.HTTP_200_OK
        
        # 5. Verify unregistration in activities list
        after_unregister_response = client.get("/activities")
        after_unregister_data = after_unregister_response.json()
        assert email not in after_unregister_data[activity]["participants"]
        assert len(after_unregister_data[activity]["participants"]) == initial_count

    def test_multiple_activities_signup(self, client, reset_activities):
        """Test a student signing up for multiple different activities."""
        email = "multisport@mergington.edu"
        activities = ["Soccer Team", "Basketball Club", "Swimming Club"]
        
        # Sign up for multiple activities
        for activity in activities:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            if response.status_code == status.HTTP_404_NOT_FOUND:
                # Skip if activity doesn't exist
                continue
            assert response.status_code == status.HTTP_200_OK
        
        # Verify student is in all activities
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        signed_up_count = 0
        for activity in activities:
            if activity in activities_data and email in activities_data[activity]["participants"]:
                signed_up_count += 1
        
        assert signed_up_count >= 2  # At least signed up for 2 activities

    def test_activity_capacity_management(self, client, reset_activities):
        """Test that activities can reach their maximum capacity."""
        # Find an activity with available spots
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        test_activity = None
        for name, data in activities_data.items():
            available_spots = data["max_participants"] - len(data["participants"])
            if available_spots > 0 and available_spots <= 3:  # Find one with few spots left
                test_activity = name
                break
        
        if test_activity:
            available_spots = activities_data[test_activity]["max_participants"] - len(activities_data[test_activity]["participants"])
            
            # Fill remaining spots
            for i in range(available_spots):
                email = f"student{i}@mergington.edu"
                response = client.post(f"/activities/{test_activity}/signup?email={email}")
                assert response.status_code == status.HTTP_200_OK
            
            # Verify activity is now at capacity
            final_response = client.get("/activities")
            final_data = final_response.json()
            assert len(final_data[test_activity]["participants"]) == final_data[test_activity]["max_participants"]

    def test_concurrent_signups_same_activity(self, client, reset_activities):
        """Test multiple students signing up for the same activity."""
        activity = "Mathletes"
        emails = [f"concurrent{i}@mergington.edu" for i in range(3)]
        
        # Sign up multiple students
        responses = []
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
        
        # Verify all are registered
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        for email in emails:
            assert email in activities_data[activity]["participants"]


class TestDataConsistency:
    """Test data consistency and state management."""

    def test_activities_data_persistence_across_requests(self, client, reset_activities):
        """Test that activity data persists across multiple requests."""
        email = "persistent@mergington.edu"
        activity = "Drama Club"
        
        # Make a signup
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Make multiple GET requests and ensure data is consistent
        for _ in range(5):
            response = client.get("/activities")
            data = response.json()
            assert email in data[activity]["participants"]

    def test_participant_count_accuracy(self, client, reset_activities):
        """Test that participant counts are accurate."""
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        for activity_name, activity_data in activities_data.items():
            participant_count = len(activity_data["participants"])
            max_participants = activity_data["max_participants"]
            
            # Check that count is within valid range
            assert 0 <= participant_count <= max_participants
            
            # Check that all participants are unique
            participants = activity_data["participants"]
            assert len(participants) == len(set(participants))  # No duplicates


class TestErrorHandling:
    """Test comprehensive error handling scenarios."""

    def test_malformed_requests(self, client, reset_activities):
        """Test handling of malformed requests."""
        # Test with invalid HTTP methods
        response = client.patch("/activities")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        response = client.put("/activities/Chess Club/signup")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_url_encoding_edge_cases(self, client, reset_activities):
        """Test URL encoding edge cases."""
        # Test activity name with spaces and special characters
        encoded_activity = "Chess%20Club"
        response = client.post(f"/activities/{encoded_activity}/signup?email=test@example.com")
        assert response.status_code == status.HTTP_200_OK

    def test_response_format_consistency(self, client, reset_activities):
        """Test that all responses follow consistent format."""
        # Test successful responses
        response = client.get("/activities")
        assert response.headers["content-type"] == "application/json"
        
        # Test error responses
        response = client.post("/activities/NonExistent/signup?email=test@example.com")
        assert response.headers["content-type"] == "application/json"
        assert "detail" in response.json()