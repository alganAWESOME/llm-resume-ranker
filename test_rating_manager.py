from resume_ratings_manager import RatingManager
from resume_manager import ResumeManager
from unittest.mock import patch
import pytest
import os
import json
import glicko2

@pytest.fixture(scope='class')
def my_fixture():
    resume_mgr = ResumeManager('for_testing_resume_manager')
    rating_mgr = RatingManager(resume_mgr.ranked_filenames)

    return resume_mgr, rating_mgr

class TestManagers:
    """
    End-to-end test of RatingManager and ResumeManager classes.
    
    Normally, an LLM will decide which resume is better.
    This class mocks this behaviour by picking as the winner
    the resume whose filename is lexicographically smaller.
    """
    @pytest.fixture(autouse=True)
    def setup(self, my_fixture):
        self.resume_mgr, self.rating_mgr = my_fixture
        self.ranked_fol = 'for_testing_resume_manager/ranked'
        self.unranked_fol = 'for_testing_resume_manager/unranked'
        self.ratings_json = 'for_testing_resume_manager/ratings.json'

    @staticmethod
    def _mock_compare(resume1, resume2):
        return 1 if resume1 < resume2 else 2
    
    def _read_json(self):
        with open(self.ratings_json, 'r') as f:
            ratings_data = json.load(f)
        return ratings_data
    
    def test_unrank_initialise(self):
        # Unrank files
        self.resume_mgr.unrank_files()
        assert len(os.listdir(self.ranked_fol)) == 0
        ratings_data = self._read_json()
        assert ratings_data == {}

        # Re-intialise files
        self.resume_mgr.init_unranked()
        filenames = os.listdir(self.ranked_fol)
        assert sorted(filenames) == ['1500-a.png', '1500-xxx.png', '1500-zzz.png']
        ratings_data = self._read_json()
        default_rating_data = {"rating": 1500, "rd": 350, "vol": 0.06}
        assert ratings_data == {"a.png": default_rating_data,
                                "xxx.png": default_rating_data,
                                "zzz.png": default_rating_data}
        
        # If we don't do this, the previous test run will make
        # resume_mgr think resumes have a rating other than 1500.
        self.resume_mgr._read_ranked_folder()

    @patch.object(RatingManager, '_compare_resumes')        
    def test_update_ratings(self, mock_compare):
        mock_compare.side_effect = self._mock_compare

        self.resume_mgr.update_ratings()

        # manually calculate what ratings.json should look like
        a_player = glicko2.Player()
        xxx_player = glicko2.Player()
        zzz_player = glicko2.Player()
        
        rating_list, rd_list = [1500, 1500], [350, 350]
        a_player.update_player(rating_list, rd_list, [1, 1])
        xxx_player.update_player(rating_list, rd_list, [1, 0])
        zzz_player.update_player(rating_list, rd_list, [0, 0])

        a_data = {"rating": a_player.getRating(), "rd": a_player.getRd(), "vol": a_player.vol}
        xxx_data = {"rating": xxx_player.getRating(), "rd": xxx_player.getRd(), "vol": xxx_player.vol}
        zzz_data = {"rating": zzz_player.getRating(), "rd": zzz_player.getRd(), "vol": zzz_player.vol}

        json_should_be = {"a.png": a_data,
                          "xxx.png": xxx_data,
                          "zzz.png": zzz_data}
        
        # check json
        ratings_data = self._read_json()
        assert ratings_data == json_should_be

        # check filenames
        a_filename = str(int(a_data["rating"])) + "-a.png" # should look like "1645-a.png" (e.g.)
        xxx_filename = str(int(xxx_data["rating"])) + "-xxx.png"
        zzz_filename = str(int(zzz_data["rating"])) + "-zzz.png"
        filenames = os.listdir(self.ranked_fol)
        assert a_filename in filenames
        assert xxx_filename in filenames
        assert zzz_filename in filenames
        assert len(filenames) == 3

if __name__ == "__main__":
    pytest.main(['-s', __file__])