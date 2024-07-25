import glicko2
import random
from filename_manager import FilenameManager

class RatingManager:
    def __init__(self, ranked_resumes):
        self.ranked_resumes = ranked_resumes
        self.num_ranked_res = len(ranked_resumes)
        self.filename_mgr = FilenameManager()

    def update_ratings(self, ratings_data, num_matches=None):
        matches = self._generate_matches(self.num_ranked_res, num_matches)
        match_results = self._play_matches(matches, ratings_data)
        new_ratings_data = self._update_ratings(match_results, ratings_data)

        return new_ratings_data
    
    def _generate_matches(self, n, num_matches=None):
        """
        Generate random matches for n players.
        If `num_matches` is None, the maximum number of matches is played.
        """
        max_num_matches = n * (n - 1) // 2
        if num_matches is None:
            num_matches = max_num_matches
        
        if num_matches > max_num_matches:
            raise ValueError('too many matches')
        
        # Shortcut
        if num_matches == max_num_matches:
            return [[i, j] for i in range(n) for j in range(i+1, n)]

        players = range(n)
        matches = []

        while len(matches) < num_matches:
            match = sorted(random.sample(players, 2))
            if match not in matches:
                matches.append(match)

        return matches
    
    def _play_matches(self, matches, ratings_data):

        # {"resume.png": ([ratings], [rds], [wins])}
        match_results = {}

        for a, b in matches:
            resume1, resume2 = self.ranked_resumes[a], self.ranked_resumes[b]
            resume1 = self.filename_mgr.rm_rankstring(resume1)
            resume2 = self.filename_mgr.rm_rankstring(resume2)
            winner = self._compare_resumes(resume1, resume2)

            if resume1 not in match_results:
                match_results[resume1] = ([], [], [])

            if resume2 not in match_results:
                match_results[resume2] = ([], [], [])
            
            r1_stats = ratings_data[resume1]
            r2_stats = ratings_data[resume2]

            match_results[resume1][0].append(r2_stats['rating'])
            match_results[resume1][1].append(r2_stats['rd'])
            match_results[resume1][2].append(1 if winner == 1 else 0)

            match_results[resume2][0].append(r1_stats['rating'])
            match_results[resume2][1].append(r1_stats['rd'])
            match_results[resume2][2].append(1 if winner == 2 else 0)

        return match_results

    def _update_ratings(self, match_results, ratings_data):
        # convert ratings data into a dict of glicko players
        # {"resume.png": Player()}
        glicko_players = {}
        print(f'{ratings_data=}')
        for resume, data in ratings_data.items():
            glicko_players[resume] = glicko2.Player(data['rating'], data['rd'], data['vol'])

        # update ratings_data
        for resume, player in glicko_players.items():
            opp_ratings, opp_rds, wins = match_results[resume]
            player.update_player(opp_ratings, opp_rds, wins)
            ratings_data[resume]["rating"] = player.getRating()
            ratings_data[resume]["rd"] = player.getRd()
            ratings_data[resume]["vol"] = player.vol

        return ratings_data

    def _compare_resumes(self, resume1, resume2):
        
        return 1 if resume1 < resume2 else 2

if __name__ == "__main__":
    # # Feb222012 example.
    # P1 = glicko2.Player()
    # print(f'{P1.rating=}, {P1.rd=}')
    # P1.setRd(200)
    # P1.update_player([1400, 1550, 1700], [30, 100, 300], [1, 0, 0])
    # # Original Ryan example.
    # Ryan = glicko2.Player()
    # print(f'{Ryan.rating=}, {Ryan.rd=}')
    # Ryan.update_player([1400, 1550, 1700],
    #     [30, 100, 300], [1, 1, 1])
    
    # print('update done')

    # print(f'{P1.rating=}, {P1.rd=}')
    # print(f'{Ryan.rating=}, {Ryan.rd=}')

    
    num_matches = lambda n : n * (n - 1) // 2

    print(num_matches(20))

    # testing lol
    mgr = RatingManager('')
    assert mgr.generate_matches(3, 3) == [[0, 1], [0, 2], [1, 2]]


    