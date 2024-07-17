import os
import pytest
from resume_comparer import LLMResumeComparer

@pytest.fixture(scope="class")
def resume_comparer_fixture():
    resume_comparer = LLMResumeComparer(resume_folder='test_resumes')
    resumes = os.listdir('./test_resumes/ranked')
    resumes.sort()
    return resume_comparer, resumes

class TestResumeComparer:

    @pytest.fixture(autouse=True)
    def setup_class(self, resume_comparer_fixture):
        self.resume_comparer, self.resumes = resume_comparer_fixture

    def _get_comparison(self, rank1, rank2):
        unranked, ranked = self.resumes[rank1], self.resumes[rank2]
        return self.resume_comparer.best_of_n(3, unranked, ranked)
    
    @staticmethod
    def _is_winner_to_be_ranked(comparison):
        return comparison['winner'] == comparison['to_be_ranked_resume']

    def _compare_and_assert(self, rank1, rank2):
        comparison = self._get_comparison(rank1, rank2)
        assert self._is_winner_to_be_ranked(comparison)

    def test_0vs1(self):
        self._compare_and_assert(0, 1)

    # Occasionally fails; longbow.png might indeed be better
    def test_1vs2(self):
        self._compare_and_assert(1, 2)
        
    def test_2vs3(self):
        self._compare_and_assert(2, 3)
        
    # This one also fails; again the ordering could be wrong
    def test_3vs4(self):
        self._compare_and_assert(3, 4)

    def test_4vs5(self):
        self._compare_and_assert(4, 5)
        
if __name__ == "__main__":
    pytest.main(["-s", __file__])