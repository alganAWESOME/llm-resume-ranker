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

    def test_0_vs_1(self):
        comparison = self._get_comparison(rank1=0, rank2=1)
        #print(comparison)
        assert self._is_winner_to_be_ranked(comparison)

if __name__ == "__main__":
    pytest.main(["-s", __file__])