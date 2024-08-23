import os
import pytest
from resume_comparer import LLMResumeComparer

@pytest.fixture(scope="class")
def resume_comparer_fixture():
    resume_comparer = LLMResumeComparer(resume_folder='test_resumes')
    resumes = os.listdir('./test_resumes/ranked')
    resumes.sort()
    return resume_comparer, resumes

class TestResumeComparerDistance1:

    @pytest.fixture(autouse=True)
    def setup_class(self, resume_comparer_fixture):
        self.resume_comparer, self.resumes = resume_comparer_fixture

    def _get_comparison(self, rank1, rank2):
        unranked, ranked = self.resumes[rank1], self.resumes[rank2]
        return self.resume_comparer.compare_resumes(unranked, ranked)
    
    @staticmethod
    def _is_winner_resume1(comparison):
        return comparison['winner'] == comparison['resume1']

    def _compare_and_assert(self, rank1, rank2):
        comparison = self._get_comparison(rank1, rank2)
        self.resume_comparer.pretty_print(comparison)
        assert self._is_winner_resume1(comparison)

    def test_0vs1(self):
        self._compare_and_assert(0, 1)

    def test_1vs2(self):
        self._compare_and_assert(1, 2)
        
    def test_2vs3(self):
        self._compare_and_assert(2, 3)
        
    def test_3vs4(self):
        self._compare_and_assert(3, 4)

    def test_4vs5(self):
        self._compare_and_assert(4, 5)

    def test_5vs6(self):
        self._compare_and_assert(5, 6)


class TestResumeComparerDistance2:

    @pytest.fixture(autouse=True)
    def setup_class(self, resume_comparer_fixture):
        self.resume_comparer, self.resumes = resume_comparer_fixture

    def _get_comparison(self, rank1, rank2):
        unranked, ranked = self.resumes[rank1], self.resumes[rank2]
        return self.resume_comparer.compare_resumes(unranked, ranked)
    
    @staticmethod
    def _is_winner_resume1(comparison):
        return comparison['winner'] == comparison['resume1']

    def _compare_and_assert(self, rank1, rank2):
        comparison = self._get_comparison(rank1, rank2)
        self.resume_comparer.pretty_print(comparison)
        assert self._is_winner_resume1(comparison)

    def test_0vs2(self):
        self._compare_and_assert(0, 2)

    def test_1vs3(self):
        self._compare_and_assert(1, 3)

    def test_2vs4(self):
        self._compare_and_assert(2, 4)

    def test_3vs5(self):
        self._compare_and_assert(3, 5)

    def test_4vs6(self):
        self._compare_and_assert(4, 6)

# evaluate single-distance
# print summary statistics


        
if __name__ == "__main__":
    pytest.main(["-s", __file__, '-k', 'TestResumeComparerDistance1'])