import pytest


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activities_contain_required_fields(self, client, reset_activities):
        """Test that activities have all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_initial_participants(self, client, reset_activities):
        """Test that initial participants are present"""
        response = client.get("/activities")
        data = response.json()
        
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant(self, client, reset_activities):
        """Test signing up a new participant for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        """Test that signup actually adds the participant to the activity"""
        client.post(
            "/activities/Programming Class/signup?email=test@mergington.edu"
        )
        
        response = client.get("/activities")
        activities = response.json()
        assert "test@mergington.edu" in activities["Programming Class"]["participants"]

    def test_signup_duplicate_participant_returns_error(self, client, reset_activities):
        """Test that signing up an already registered participant returns an error"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that signing up for a nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_multiple_participants(self, client, reset_activities):
        """Test signing up multiple different participants"""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for email in emails:
            response = client.post(
                f"/activities/Gym Class/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all are added
        response = client.get("/activities")
        activities = response.json()
        for email in emails:
            assert email in activities["Gym Class"]["participants"]


class TestRemoveParticipantEndpoint:
    """Tests for the DELETE /activities/{activity_name}/remove endpoint"""

    def test_remove_existing_participant(self, client, reset_activities):
        """Test removing an existing participant from an activity"""
        response = client.delete(
            "/activities/Chess Club/remove?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]

    def test_remove_participant_actually_removes(self, client, reset_activities):
        """Test that remove actually removes the participant"""
        client.delete(
            "/activities/Chess Club/remove?email=michael@mergington.edu"
        )
        
        response = client.get("/activities")
        activities = response.json()
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]

    def test_remove_nonexistent_participant_returns_error(self, client, reset_activities):
        """Test that removing a nonexistent participant returns an error"""
        response = client.delete(
            "/activities/Chess Club/remove?email=nonexistent@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_remove_from_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that removing from a nonexistent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/remove?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_remove_all_participants(self, client, reset_activities):
        """Test removing all participants from an activity"""
        response = client.get("/activities")
        activity = response.json()["Basketball Team"]
        original_count = len(activity["participants"])
        
        for email in activity["participants"][:]:
            response = client.delete(
                f"/activities/Basketball Team/remove?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all removed
        response = client.get("/activities")
        activities = response.json()
        assert len(activities["Basketball Team"]["participants"]) == 0


class TestSignupAndRemoveFlow:
    """Integration tests for signup and remove workflows"""

    def test_signup_then_remove_workflow(self, client, reset_activities):
        """Test the complete flow of signing up and then removing a participant"""
        email = "integration@mergington.edu"
        
        # Sign up
        response = client.post(
            f"/activities/Art Studio/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify signed up
        response = client.get("/activities")
        assert email in response.json()["Art Studio"]["participants"]
        
        # Remove
        response = client.delete(
            f"/activities/Art Studio/remove?email={email}"
        )
        assert response.status_code == 200
        
        # Verify removed
        response = client.get("/activities")
        assert email not in response.json()["Art Studio"]["participants"]

    def test_signup_remove_signup_again_workflow(self, client, reset_activities):
        """Test signing up, removing, and then signing up again"""
        email = "reregister@mergington.edu"
        activity = "Music Ensemble"
        
        # First signup
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Remove
        response = client.delete(f"/activities/{activity}/remove?email={email}")
        assert response.status_code == 200
        
        # Second signup (should succeed)
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify signed up again
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
