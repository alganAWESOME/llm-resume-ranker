from resume_sorter import ResumeSorter
from unittest.mock import patch
import pytest
import os
from rankstring import RankString

@pytest.fixture(scope='class')
def resume_sorter_fixture():
    resume_sorter = ResumeSorter(resume_folder='resumes_test_sorter', debug=True)
    resume_sorter.unrank_files()
    resume_sorter.read_ranked_folder()

    # Move these two files to storage
    move_to_storage = ['abb.png', 'xxx.png', 'a.png', 'zzz.png']
    for filename in move_to_storage:
        try:
            os.rename(f'./resumes_test_sorter/unranked/{filename}',
                    f'./resumes_test_sorter/storage/{filename}')
        except:
            continue # they're probably already in storage

    return resume_sorter, RankString()

class TestResumeSorter:

    @pytest.fixture(autouse=True)
    def setup(self, resume_sorter_fixture):
        self.sorter, self.rankstring = resume_sorter_fixture

    def assert_filenames(self):
        """
        Makes assertions about filenames in the ranked folder:
        1. Are the rankstrings correct
        2. Are the filenames in lexicographical order (when you remove the rankstring)
        """
        ranked_resumes = sorted(os.listdir('./resumes_test_sorter/ranked/'))

        for i in range(len(ranked_resumes) - 1):
            resume1, resume2 = ranked_resumes[i], ranked_resumes[i+1]
            _, resume_name1 = self.rankstring.get_rankstring(resume1)
            _, resume_name2 = self.rankstring.get_rankstring(resume2)

            # check rankstring
            assert self.rankstring.is_rank_consecutive(resume1, resume2)

            # check lexicographic order
            assert resume_name1 < resume_name2

    def mock_compare(self, *args, **kwargs):
        resume_tbr = self.sorter.to_be_ranked_filename

        curr_rank = self.sorter.current_rank
        ranked_filenames = self.sorter.ranked_filenames
        resume_r = ranked_filenames[curr_rank]

        return {'Resume A': resume_tbr,
                'Resume B': resume_r,
                'winner': 'placeholder',
                'claude_response': 'placeholder'}
    
    def mock_is_winner_tbr(self, comparison):
        """Returns True if Resume A is lexicographically smaller than Resume B."""
        print(f'Comparison: {comparison['Resume A']} vs {comparison['Resume B'][4:]}')
        return comparison['Resume A'] < comparison['Resume B'][4:]

    @patch.object(ResumeSorter, '_is_winner_to_be_ranked')
    @patch.object(ResumeSorter, '_bon_with_ranked_at_curr')
    @patch.object(ResumeSorter, '_compare_with_ranked_at_curr')
    def test_insert_all(self, mock_compare, mock_bon_compare, mock_is_winner_tbr):
        """Test inserting a few at a time."""
        mock_compare.side_effect = self.mock_compare
        mock_bon_compare.side_effect = self.mock_compare
        mock_is_winner_tbr.side_effect = self.mock_is_winner_tbr

        print(f'\nRanking: {os.listdir(f'./{'resumes_test_sorter'}/unranked')}\n')
        
        self.sorter.insert_all()
        self.assert_filenames()

        # input('Done with test, continue?')

    @staticmethod
    def _moveto_unranked_from_storage(filename):
        try:
            os.rename(f'./resumes_test_sorter/storage/{filename}',
                    f'./resumes_test_sorter/unranked/{filename}')
        except:
            print(f'{filename} doesnt exist in storage')

    @patch.object(ResumeSorter, '_is_winner_to_be_ranked')
    @patch.object(ResumeSorter, '_bon_with_ranked_at_curr')
    @patch.object(ResumeSorter, '_compare_with_ranked_at_curr')
    def test_insert_upwards(self, mock_compare, mock_bon_compare, mock_is_winner_tbr):
        """Test insert where first direction is win (hence name 'upwards')."""

        mock_compare.side_effect = self.mock_compare
        mock_bon_compare.side_effect = self.mock_compare
        mock_is_winner_tbr.side_effect = self.mock_is_winner_tbr

        # move abb.png into unranked from storage
        self._moveto_unranked_from_storage('abb.png')
        
        self.sorter.insert("abb.png")
        self.assert_filenames()

    @patch.object(ResumeSorter, '_is_winner_to_be_ranked')
    @patch.object(ResumeSorter, '_bon_with_ranked_at_curr')
    @patch.object(ResumeSorter, '_compare_with_ranked_at_curr')
    def test_insert_downwards(self, mock_compare, mock_bon_compare, mock_is_winner_tbr):
        """Test insert where first direction is loss (hence name 'downwards')."""

        mock_compare.side_effect = self.mock_compare
        mock_bon_compare.side_effect = self.mock_compare
        mock_is_winner_tbr.side_effect = self.mock_is_winner_tbr

        # move xxx.png into unranked from storage
        self._moveto_unranked_from_storage('xxx.png')
        
        self.sorter.insert("xxx.png")
        self.assert_filenames()

    @patch.object(ResumeSorter, '_is_winner_to_be_ranked')
    @patch.object(ResumeSorter, '_bon_with_ranked_at_curr')
    @patch.object(ResumeSorter, '_compare_with_ranked_at_curr')
    def test_insert_firstplace(self, mock_compare, mock_bon_compare, mock_is_winner_tbr):
        """Test insert where final result should be rank 0."""

        mock_compare.side_effect = self.mock_compare
        mock_bon_compare.side_effect = self.mock_compare
        mock_is_winner_tbr.side_effect = self.mock_is_winner_tbr

        self._moveto_unranked_from_storage('a.png')

        self.sorter.insert("a.png")
        self.assert_filenames()

    @patch.object(ResumeSorter, '_is_winner_to_be_ranked')
    @patch.object(ResumeSorter, '_bon_with_ranked_at_curr')
    @patch.object(ResumeSorter, '_compare_with_ranked_at_curr')
    def test_insert_lastplace(self, mock_compare, mock_bon_compare, mock_is_winner_tbr):
        """Test insert where final result should be rank <last-place>."""

        mock_compare.side_effect = self.mock_compare
        mock_bon_compare.side_effect = self.mock_compare
        mock_is_winner_tbr.side_effect = self.mock_is_winner_tbr

        self._moveto_unranked_from_storage('zzz.png')

        self.sorter.insert("zzz.png")
        self.assert_filenames()

if __name__ == "__main__":
    pytest.main(['-s', __file__])